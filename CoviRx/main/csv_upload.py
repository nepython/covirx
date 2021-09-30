import csv
import logging
from copy import deepcopy

from django.core.cache import cache
from django.template.loader import get_template
from django.core.mail import EmailMessage
from premailer import transform

from .models import Drug
from .utils import searchfields, verbose_names, invalid_drugs
from CoviRx.settings import EMAIL_HOST_USER


def get_invalid_headers(obj):
    file_path = obj.csv_file.path
    with open(file_path, 'r') as fp:
        drugs = list(csv.reader(fp, delimiter=','))
        headers = [drug.lower().replace(' ', '_') for drug in drugs[1]]
        invalid_headers = list()
        for field in headers:
            if field not in searchfields+['label']:
                invalid_headers.append(field)
    return invalid_headers


def save_drugs_from_csv(obj): #TODO: Make the code less redundant
    cache.set('valid_count', 0, None)
    cache.set('invalid_count', 0, None)
    cache.set('email_recepients', '', None)
    invalid_drugs.clear()
    file_path = obj.csv_file.path
    custom_fields = cache.get('custom_fields')
    with open(file_path, 'r') as fp:
        drugs = list(csv.reader(fp, delimiter=','))
        obj.total_count = len(drugs)-2
        cache.set('total_count', len(drugs)-2, None)
        obj.save()
        headers = [drug.lower().replace(' ', '_') for drug in drugs[1]] # would need to be changed for target models
        for drug in drugs[2:]:
            if cache.get(obj.pk, None):
                break # Cancel Upload feature
            # create a dictionary of drug details
            drug_details = dict()
            custom = {f: '' for f in cache.get('custom_fields')}
            for i, field in enumerate(headers):
                if field in searchfields or field=='label':
                    drug_details[field] = drug[i]
                elif field in verbose_names:
                    drug_details[verbose_names[field]] = drug[i]
                elif field in custom_fields:
                    custom[field] = drug[i]
            try:
                drug_details['custom_fields'] = custom
                Drug.get_or_create(drug_details).custom_fields
                obj.valid_drug()
            except Exception as e:
                msg = f'Unable to add drug {drug_details["name"]} because of an error. {repr(e)}'
                logging.getLogger('error_logger').error(msg)
                obj.invalid_drug()
                invalid_drugs[drug_details['name']] = repr(e.error_dict) if hasattr(e, 'error_dict') else repr(e)
    if cache.get('email_recepients'):
        mail_invalid_drugs(cache.get('email_recepients').split(';'), deepcopy(invalid_drugs))
    cache.delete('total_count')
    cache.delete('valid_count')
    cache.delete('invalid_count')
    cache.delete('email_recepients')
    obj.invalid_drugs = str(invalid_drugs)
    obj.full_clean()
    obj.save()
    invalid_drugs.clear()


def mail_invalid_drugs(recepients, invalid_drugs):
    message = transform(
        get_template('main/invalid-drugs-mail_template.html').render({'drugs': invalid_drugs}),
        allow_insecure_ssl=True,
        disable_leftover_css=True,
        strip_important=False,
        disable_validation=True,
    )
    msg = EmailMessage(
        "List of invalid drugs in latest drug upload on CoviRx",
        message,
        EMAIL_HOST_USER,
        recepients,
    )
    msg.content_subtype = "html"
    msg.send(fail_silently=False)
