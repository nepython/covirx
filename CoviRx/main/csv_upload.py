import csv
import logging
from copy import deepcopy

from django.core.cache import cache
from django.template.loader import get_template

from .models import Drug
from .utils import store_fields, verbose_names, invalid_drugs, sendmail


def get_invalid_headers(obj):
    file_path = obj.csv_file.path
    with open(file_path, 'r') as fp:
        drugs = list(csv.reader(fp, delimiter=','))
        headers = [drug.lower().replace(' ', '_') for drug in drugs[1]]
        invalid_headers = list()
        for field in headers:
            if field not in (store_fields+list(verbose_names.keys())):
                invalid_headers.append(field)
    return invalid_headers


def save_drugs_from_csv(obj, invalid_headers): #TODO: Make the code less redundant
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
        valid_headers = set(headers)-set(invalid_headers)
        for drug in drugs[2:]:
            if cache.get(obj.pk, None):
                break # Cancel Upload feature
            drug_details = dict() # create a dictionary of drug details
            custom = {f: '' for f in cache.get('custom_fields')}
            for i, field in enumerate(headers):
                if field not in valid_headers or not drug[i]:
                    continue
                if field in store_fields:
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
        mail_invalid_drugs(cache.get('email_recepients').split(';'), deepcopy(invalid_drugs), obj.uploaded_by, obj.timestamp)
    cache.delete('total_count')
    cache.delete('valid_count')
    cache.delete('invalid_count')
    cache.delete('email_recepients')
    obj.invalid_drugs = str(invalid_drugs)
    obj.full_clean()
    obj.save()
    invalid_drugs.clear()


def mail_invalid_drugs(recepients, invalid_drugs, username, timestamp):
    html = get_template('mail_templates/invalid-drugs.html').render({'drugs': invalid_drugs, 'uploaded_by': username, 'timestamp': timestamp})
    subject = "List of invalid drugs in latest drug upload on CoviRx"
    sendmail(html, subject, recepients)
