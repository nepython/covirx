import logging
import json
import requests
from io import StringIO
from wsgiref.util import FileWrapper
from threading import Thread
from collections import defaultdict, OrderedDict

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.db.models import Count
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import Context
from django.template.loader import get_template

from accounts.models import User, Visitor
from .csv_upload import get_invalid_headers, save_drugs_from_csv
from .forms import DrugBulkUploadForm, DrugForm
from .models import Drug, DrugBulkUpload, Contact, AddDrug
from .utils import (invalid_drugs, search_fields, store_fields, verbose_names,
    clinical_trial_links, target_model_names, extra_references, sendmail, MAX_SUGGESTIONS)
from .tanimoto import similar_drugs
import csv


def home(request):
    Visitor.record(request)
    return render(request, 'main/index.html', {'fields': search_fields})


def autocomplete(request):
    if request.method == 'POST':
        return JsonResponse({})
    keyword = json.loads(request.GET.get('keyword', '{}'))
    suggestions = min(int(request.GET.get('suggestions', 5)), MAX_SUGGESTIONS)
    if (not keyword):
        return JsonResponse({})
    return JsonResponse(search_drug(keyword, suggestions))


def search_drug(keyword, suggestions): # suggestions is the count of the number of suggestions to pass
    drugs = dict()
    query = {f'{k}__startswith': v for k, v in keyword.items() if v}
    if not query: return drugs
    drugmodels = Drug.objects.filter(**query)[:suggestions]
    for i, drug in enumerate(drugmodels):
        try:
            drugmetadata = model_to_dict(drug, fields=['label']+search_fields+list(verbose_names.values()))
            drugs[i] = drugmetadata
            drugs[i]['id'] = str(drug.id)
        except Exception as e:
            logging.getLogger('error_logger').error(f'Error encounter white searching for drug {drug} {repr(e)}')
    return drugs


def individual_drug(request, drug_id):
    Visitor.record(request, drug_overview=drug_id)
    drug = Drug.objects.get(pk=drug_id)
    kwargs = {
        'name': drug.name,
        'chembl': drug.chembl,
        'smiles': drug.smiles,
        'inchi': drug.inchi,
        'drug_likeness': {
            'Molecular Weight': drug.mw,
            'No. of Chiral Centres': drug.nochiralcentres,
            'logP': drug.logp,
            'HBA': drug.hba,
            'HBD': drug.hbd,
            'PSA': drug.psa,
            'Rotatable bonds': drug.rotbonds,
        },
        'original_indication': drug.custom_fields.get('Original Indication', dict()),
        'identifiers': {
            'CAS Number': drug.cas_number,
            'Formula': drug.formula,
            'Synonyms': drug.synonyms,
            'ChEBI': drug.chebi,
            'PubChem ID': drug.pubchemcid,
            'Drug Bank': drug.drugbank,
        },
        'activity_rank': drug.rank_score,
        'target_models': {k: v for k, v in drug.custom_fields.items() if k in target_model_names},
        'covid_trials': drug.custom_fields.get('COVID Trials', dict()),
        'more_info_trials': f'/clinical-trials/{drug.name}' if drug.name in clinical_trial_links else None,
        'pk_pd': drug.custom_fields.get('PK/PD', dict()),
        'red_flags': drug.custom_fields.get('Red Flags', dict()),
        'filters_passed': drug.filters_passed,
        'references': drug.references,
    }
    if 'download-json' in request.GET:
        json_file = StringIO()
        json_file.write(json.dumps(kwargs, indent=4))
        json_file.seek(0)
        wrapper = FileWrapper(json_file)
        response = HttpResponse(wrapper, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename={drug.name}.json'
        return response
    return render(request, 'main/individual_drug.html', kwargs)


def contact(request):
    Visitor.record(request)
    res = {'success': False}
    if request.method == "POST":
        contact = Contact()
        post_data = request.POST.copy()
         # Google recaptcha verification
        recaptcha_response = post_data.pop('g-recaptcha-response')
        data = {
            'secret': settings.GOOGLE_INVISIBLE_RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response,
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()
        if not result['success']:
            res['msg'] = 'Invalid reCAPTCHA. Please try again.'
            return render(request, 'main/contact.html', res)
        for field in post_data:
            if field in contact.__dict__:
                contact.__dict__.update({field: post_data.get(field)})
        try:
            contact.full_clean()
        except Exception as e:
            messages.error(request, f'Could not submit the form, caught an exception. {repr(e)}')
        finally:
            res['success'] = True
            contact.save()
            contact.copy = True if post_data.get('response-copy') else False
            html = get_template('mail_templates/contact.html').render({'contact': contact})
            recepients = list(User.objects.filter(email_notifications=True).values_list('email', flat=True))
            bcc = [contact.email] if contact.copy else list()
            log = f'Mail successfully sent for message received from {contact.name}'
            Thread(target = sendmail, args = (html, contact.subject, recepients, bcc, log)).start() # async from the process so that the view gets returned post successful save
    return render(request, 'main/contact.html', res)


def organisations(request):
    return render(request, 'main/organisations.html')


def references(request):
    Visitor.record(request)
    refs = [r[0] for r in Drug.objects.values_list('references').distinct() if r[0]!=None and r[0]!='']+extra_references
    return render(request, 'main/references.html', {'references': refs})


def add_drug(request):
    submitted = False
    if request.method == "POST":
        post_data = request.POST.copy()
        # Google recaptcha verification
        recaptcha_response = post_data.pop('g-recaptcha-response')
        data = {
            'secret': settings.GOOGLE_INVISIBLE_RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response,
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()
        if not result['success']:
            return render(request, 'main/add_drug.html', {'msg': 'Invalid reCAPTCHA. Please try again.'})
        form = DrugForm(post_data)
        if form.is_valid():
            form.save()
            try:
                added_drug = AddDrug.objects.get(personName=post_data.get('personName'), drugName=post_data.get('drugName'))
                email = post_data.get('email')
                html = get_template('mail_templates/add_drug.html').render({'added_drug': added_drug})
                recepients = list(User.objects.filter(email_notifications=True).values_list('email', flat=True))
                bcc = [email] if post_data.get('response-copy') else list()
                log = f'Copy of mail successfully sent for new drug received from {added_drug.personName}'
                Thread(target = sendmail, args = (html, 'New drug submitted to CoviRx', recepients, bcc, log)).start() # async from the process so that the view gets returned post successful save
            except:
                pass
            return HttpResponseRedirect('/add_drug?submitted=True')
    else:
        form = DrugForm
        if 'submitted' in request.GET:
            submitted = True
    return render(request , 'main/add_drug.html',
        {'form':form,'submitted':submitted})


def show_drug(request, drug_id):
    drug = AddDrug.objects.get(pk=drug_id)
    return render(request , 'main/show_drug.html', 
        {'drug':drug})


def list_drugs(request):
    drugs_list = AddDrug.objects.all()
    return render(request , 'main/drug.html', 
        {'drugs_list':drugs_list})


def drug_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=drugs.csv'
    # Create a csv writer
    writer = csv.writer(response)
    drugs = AddDrug.objects.all()
    # Add column headings to the csv file
    writer.writerow(['Name of Person','Email id','Organization','Drug name','Invitro','Invivo','Exvivo','Activity Results(IC50/EC50)','Inference'])
    # Loop Thu and output
    for drug in drugs:
        writer.writerow([drug.personName, drug.email, drug.organisation, drug.drugName, drug.invitro, drug.invivo, drug.exvivo, drug.results, drug.inference])
    return response


def cookie_policy(request):
    return render(request, 'main/cookie-policy.html')


@user_passes_test(lambda u: u.is_staff, login_url='/login')
def csv_upload(request):
    if request.method == 'GET':
        form = DrugBulkUploadForm()
        return render(request, 'main/drug_upload.html', {})
    try:
        form = DrugBulkUploadForm(data=request.POST, files=request.FILES)
        if not form.is_valid():
            raise ValidationError('The submitted form is invalid!')
        csv_file = form.cleaned_data['csv_file']
        if not csv_file.name.endswith('.csv'):
            return JsonResponse({'error': 'File is not CSV type'})
        user = '{} <{}>'.format(request.user.get_full_name(), request.user.email)
        upload = DrugBulkUpload(csv_file=csv_file, uploaded_by=user)
        upload.full_clean()
        upload.save()
        invalid_headers = get_invalid_headers(upload)
        res = {'csv-id': str(upload.pk)}
        if cache.get('total_count', 0): # Previous upload in progress, kill it
            previous_upload = DrugBulkUpload.objects.order_by('-date_uploaded').first()
            cache.set(previous_upload.pk, 'cancel', 3600)
            res['error'] = f'Previous upload by {previous_upload.uploaded_by} which was in progress was cancelled mid-way.'
        # async from the process so that the view gets returned post successful upload
        Thread(target = save_drugs_from_csv, args = (upload, invalid_headers)).start()
        return JsonResponse(res)
    except Exception as e:
        logging.getLogger('error_logger').error(f'Unable to upload file. {repr(e)}')
        return JsonResponse({'error': f'Unable to upload file. {repr(e)}'})


@user_passes_test(lambda u: u.is_staff, login_url='/login')
def articles_found(request):
    if request.method == 'GET':
        kwargs = {
            'heading': ['Drug Name', 'number of articles'],
            'rows': [
                {'name': drug.name, 'count': drug.related_articles().count()} for i, drug in enumerate(Drug.objects.all()) if drug.related_articles().count()
            ],
        }
        return render(request, 'main/articles_found.html', kwargs)


@user_passes_test(lambda u: u.is_staff, login_url='/login')
def related_articles(request, drug_name):
    if request.method == 'GET':
        d = Drug.objects.get(name=drug_name)
        articles = d.related_articles()
        kwargs = {
            'heading': ['Title', 'url', 'date mined', 'Target model', 'keywords', 'verified by', 'relevant'],
            'rows': [article.json() for article in articles],
            'msg': 'Kindly scroll the table horizontally if all columns are not visible.'
        }
        return render(request, 'main/articles_found_individual_drug.html', kwargs)


@user_passes_test(lambda u: u.is_staff, login_url='/login')
def csv_upload_updates(request):
    if request.method == 'GET':
        pk = request.GET.get('cancel-upload')
        res = dict()
        if pk:
            cache.set(pk, 'cancel', 3600)
            res[pk] = (f"The drug upload was cancelled midway. <b>"
                f"{cache.get('valid_count', 0)}</b> drugs got successfully added.")
        return JsonResponse(res)
    # TODO: How to be really sure which bulk upload it is representing
    # pk = json.loads(request.body.decode('UTF-8')).get('pk', '-1')
    email_recepients = json.loads(request.body.decode('UTF-8')).get('email', '')
    cache.set('email_recepients', email_recepients, None)
    invalid_count = int(json.loads(request.body.decode('UTF-8')).get('invalid_count', 0))
    invalidated_drugs = dict()
    for drug in list(invalid_drugs)[invalid_count:]:
        invalidated_drugs[drug] = invalid_drugs[drug]
    return JsonResponse({
        'total': cache.get('total_count', '-NA-'),
        'valid': cache.get('valid_count', '-NA-'),
        'invalid': cache.get('invalid_count', '-NA-'),
        'invalid_drugs': invalidated_drugs,
    })


column_order = OrderedDict({
    'Day': 0,
    'Home': 1,
    'Purpose': 2,
    'Organisations': 3,
    'References': 4,
    'Contact': 5,
    'Website': 6,
})
drug_label = {
    '1': 'White',
    '2': 'Green',
    '3': 'Red',
    '4': 'Amber',
}


def charts_json(request):
    charts = dict()
    charts_requested = dict(request.GET).get('charts[]', list())
    if 'visitors' in charts_requested and request.user.is_staff:
        site_visitors = Visitor.site_visitors()
        page_visitors = Visitor.page_visitors()
        charts['visitors'] = [list(column_order.keys())]
        days = defaultdict(lambda:OrderedDict({k.lower(): 0 for k in column_order.keys() if k not in ['Day', 'Website']}))
        for visit in page_visitors:
            days[visit['day']][visit['page_visited']] += visit['visits']
        for item in site_visitors:
            d = item['day']
            charts['visitors'] += [[d]+[v for v in days[d].values()]+[item['visits']]]
    # TODO: Implement it on the front end
    if 'top_drugs' in charts_requested and request.user.is_staff:
        top_drugs = list(Visitor.objects.filter(drug_overview=True)
        .values('page_visited')
        .annotate(count=Count('page_visited'))
        .order_by('-count')[:10])
        for d in top_drugs:
            try:
                d['page_visited'].replace('individual-drug/', '')
                name = Drug.objects.get(d['page_visited']).name
                charts['top_drugs'] += [[name, d['count'], d['page_visited']]]
            except Exception:
                pass
    if 'categories' in charts_requested:
        qs = (Drug.objects.filter()
            .exclude(indication_class__isnull=True)
            .exclude(indication_class__exact='')
            .values('indication_class')
            .annotate(count=Count('indication_class')))
        others_count = qs.filter(count=1).count() # we club all categories which occur only once in others
        #na_count = Drug.objects.filter(indication_class__isnull=True).count() # category not available
        categories = list(qs.filter(count__gt=1))
        charts['categories'] = [['Drug Categories', 'Number of drugs']]
        charts['categories'] += [[category['indication_class'], category['count']] for category in categories]
        charts['categories'] += [['Others', others_count]]
        charts['total_drugs'] = Drug.objects.all().count()
    if 'labels' in charts_requested:
        labels = list(Drug.objects.filter()
            .values('label')
            .order_by('label')
            .annotate(count=Count('label')))
        charts['labels'] = [['Drug Labels', 'Number of drugs']]
        charts['labels'] += [[drug_label[label['label']], label['count']] for label in labels]
    if 'phase' in charts_requested:
        phase = list(Drug.objects.filter()
            .exclude(phase__isnull=True)
            .exclude(phase__exact='')
            .values('phase')
            .order_by('phase')
            .annotate(count=Count('phase')))
        charts['phase'] = [['Clinical Trial Phase', 'Number of drugs']]
        charts['phase'] += [[p['phase'], p['count']] for p in phase]
    return JsonResponse(charts)


def similar_drugs_json(request, drug_id):
    drug = Drug.objects.get(pk=drug_id)
    name, smile = drug.name, drug.smiles
    ref_drugs = OrderedDict({n: s for n, s in Drug.objects.values_list('name', 'smiles') if n!=name})
    similar__drugs = similar_drugs(ref_drugs, {name: smile})
    similar__drugs = sorted(similar__drugs, key=similar__drugs.get)
    similar__drugs.reverse()
    similar__drugs = similar__drugs[:5] # Limit to top 5 similar drugs
    response = dict()
    for i, n in enumerate(similar__drugs):
        d = Drug.objects.get(name=n)
        response[i] = {'id': d.id, 'name': d.name, 'smiles': d.smiles}
    return JsonResponse(response)


def target_models(request):
    return render(request, "main/target_models.html")


def clinical_trials(request, drug_name):
    if not drug_name in clinical_trial_links:
        return render(request, 'main/clinical_trials.html', {"msg": "We do not have detailed clinical trial for the drug."})
    # The below name is of the format as required by clinicaltrials.gov
    name = clinical_trial_links[drug_name]
    name = name[name.find('&term=')+len('&term='):name.find('+')]
    url = f'https://clinicaltrials.gov/ct2/results/download_fields?down_count=10000&down_flds=shown&down_fmt=tsv&term={name}&cond=COVID-19&flds=a&flds=b&flds=i&flds=f&flds=k&flds=o&flds=p&flds=n&flds=r&flds=x'
    r = requests.get(url, allow_redirects=True)
    records = r.content.decode('utf-8').replace('\r', '')
    records = [row.split('\t') for row in records.split('\n') if row]
    kwargs = {
        'heading': records[0][:-1],
        'rows': [
            {records[0][i]: v for i, v in enumerate(record) if (records[0][i]!='URL')} for record in records[1:]
        ],
        'urls': [row[-1] for row in records[1:]],
        'msg': 'Kindly scroll the table horizontally to view all the columns.'
    }
    return render(request, 'main/clinical_trials.html', kwargs)
