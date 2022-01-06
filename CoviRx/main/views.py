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
from .utils import invalid_drugs, search_fields, store_fields, verbose_names, target_model_names, sendmail
from .tanimoto import similar_drugs
import csv


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


def show_drug(request, drug_id):
    drug = AddDrug.objects.get(pk=drug_id)
    return render(request , 'main/show_drug.html', 
        {'drug':drug})


def list_drugs(request):
    drugs_list = AddDrug.objects.all()
    return render(request , 'main/drug.html', 
        {'drugs_list':drugs_list})


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


def home(request):
    Visitor.record(request)
    return render(request, 'main/index.html', {'fields': search_fields})


def autocomplete(request):
    if request.method == 'POST':
        return JsonResponse({})
    keyword = json.loads(request.GET.get('keyword', '{}'))
    suggestions = int(request.GET.get('suggestions', 5))
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
    # Visitor.record(request)
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
            'Rotation bonds': drug.rotbonds,
            'Administration route': drug.administration_route,
            'Indication class/ category': drug.indication_class
        },
        'activity_rank': drug.rank_score,
        'target_models': {k: v for k, v in drug.custom_fields.items() if k in target_model_names},
        'other_details': {
            'CAS Number': drug.cas_number,
            'Formula': drug.formula,
            'Synonyms': drug.synonyms,
            'ChEBL': drug.chebl,
            'PubChem ID': drug.pubchemcid,
            'ChemBank': drug.chembank,
            'Drug Bank': drug.drugbank,
            'Clinical Phase': drug.phase,
        },
        'filters_passed': drug.filters_passed,
    }
    if 'download' in request.GET:
        json_file = StringIO()
        json_file.write(json.dumps(kwargs))
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
    refs = [r[0] for r in Drug.objects.values_list('references').distinct() if r[0]!=None and r[0]!='']
    return render(request, 'main/references.html', {'references': refs})


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
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
        # async from the process so that the view gets returned post successful upload
        Thread(target = save_drugs_from_csv, args = (upload, invalid_headers)).start()
        return JsonResponse({'csv-id': str(upload.pk), 'invalid-headers': invalid_headers})
    except Exception as e:
        logging.getLogger('error_logger').error(f'Unable to upload file. {repr(e)}')
        return JsonResponse({'error': f'Unable to upload file. {repr(e)}'})


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
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
    if 'visitors' in charts_requested:
        site_visitors = Visitor.site_visitors()
        page_visitors = Visitor.page_visitors()
        charts['visitors'] = [list(column_order.keys())]
        days = defaultdict(lambda:OrderedDict({k.lower(): 0 for k in column_order.keys() if k not in ['Day', 'Website']}))
        for visit in page_visitors:
            days[visit['day']][visit['page_visited']] += visit['visits']
        for item in site_visitors:
            d = item['day']
            charts['visitors'] += [[d]+[v for v in days[d].values()]+[item['visits']]]
    if 'categories' in charts_requested:
        qs = (Drug.objects.filter()
            .exclude(indication_class__isnull=True)
            .exclude(indication_class__exact='')
            .values('indication_class')
            .annotate(count=Count('indication_class')))
        others_count = qs.filter(count=1).count() # we club all categories which occur only once in others
        na_count = Drug.objects.filter(indication_class__isnull=True).count() # category not available
        categories = list(qs.filter(count__gt=1))
        charts['categories'] = [['Drug Categories', 'Number of drugs']]
        charts['categories'] += [[category['indication_class'], category['count']] for category in categories]
        charts['categories'] += [['Others', others_count], ['NA', na_count]]
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
