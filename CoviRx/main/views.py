import logging
import json
from threading import Thread
from collections import defaultdict, OrderedDict

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template import Context
from django.template.loader import get_template

from accounts.models import User, Visitor
from .csv_upload import get_invalid_headers, save_drugs_from_csv
from .forms import DrugBulkUploadForm
from .models import Drug, DrugBulkUpload, Contact
from .utils import invalid_drugs, search_fields, store_fields, verbose_names, sendmail


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
            drugmetadata = model_to_dict(drug, fields=store_fields+list(verbose_names.values()))
            drugs[i] = drugmetadata
        except Exception as e:
            logging.getLogger('error_logger').error(f'Error encounter white searching for drug {drug} {repr(e)}')
    return drugs


def contact(request):
    Visitor.record(request)
    res = {'success': False}
    if request.method == "POST":
        contact = Contact()
        for field in request.POST:
            if field in contact.__dict__:
                contact.__dict__.update({field: request.POST.get(field)})
        try:
            contact.full_clean()
        except Exception as e:
            messages.error(request, f'Could not submit the form, caught an exception. {repr(e)}')
        finally:
            res['success'] = True
            contact.save()
            contact.copy = True if request.POST.get('response-copy') else False
            html = get_template('mail_templates/contact.html').render({'contact': contact})
            recepients = list(User.objects.filter(email_notifications=True).values_list('email', flat=True))
            bcc = [contact.email] if contact.copy else list()
            log = f'Mail successfully sent for message received from {contact.name}'
            Thread(target = sendmail, args = (html, contact.subject, recepients, bcc, log)).start() # async from the process so that the view gets returned post successful save
    return render(request, 'main/contact.html', res)


def references(request):
    Visitor.record(request)
    refs = [r[0] for r in Drug.objects.values_list('references').distinct() if r[0]!=None and r[0]!='']
    return render(request, 'main/references.html', {'references': refs})


@user_passes_test(lambda u: u.is_superuser, login_url='/admin/login/')
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
            messages.error(request, 'File is not CSV type')
            return redirect('drug-bulk-upload')
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
        messages.error(request, f'Unable to upload file. {repr(e)}')
        return JsonResponse({})


@user_passes_test(lambda u: u.is_superuser, login_url='/admin/login/')
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
    'References': 2,
    'Contact': 3,
    'Website': 4,
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
