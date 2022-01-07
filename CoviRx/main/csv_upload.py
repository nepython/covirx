import csv
import logging
from copy import deepcopy

from django.core.cache import cache
from django.template.loader import get_template

from .models import Drug
from .utils import store_fields, verbose_names, invalid_drugs, target_model_names, sendmail


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
        headers = [drug.lower().replace(' ', '_') for drug in drugs[1]]
        position = generate_position_for_target(drugs)
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
            drug_details['label'] = drug_label(drug, drugs[1])
            drug_details['filters_passed'] = filters_passed(drug, drugs[0], drugs[1])
            custom.update(save_target_models(drug, position, drugs[1])) # Save the various target models as custom fields
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


def generate_position_for_target(drugs):
    position = dict()
    prev_target = None
    for i, target in enumerate(drugs[0]):
        if target and prev_target and len(position[prev_target])<2:
            position[prev_target].append(i)
        if target in target_model_names:
            position[target] = [i]
            prev_target = target
    return position


def save_target_models(drug, position, headers):
    """
    Args:
        drug (list): Contains all the parameter for the drug
        position (dictionary of list (start, end)): Contains the starting and ending position of every target model
    """
    target_models = dict()
    for target, pos in position.items():
        target_model = dict()
        for h in range(pos[0], pos[1]):
            target_model[headers[h]] = drug[h]
        if any(x != str() for x in target_model.values()):
            target_models[target] = target_model
    return target_models


def drug_label(drug, header):
    if drug[header.index('Covid trials')].lower()=='' or drug[header.index('Covid trials')].lower()=='no':
        return '1'
    if 'completed' in drug[header.index('Outcome')].lower():
        return '2'
    if 'withdrawn' in drug[header.index('Outcome')].lower():
        return '3'
    return '4'


def filters_passed(drug, header0, header1):
    if drug[header0.index('Filtering')+1].lower=='':
        return 0
    if drug[header1.index('FDA/TGA')]!='FDA' and drug[header1.index('FDA/TGA')]!='TGA':
        return 1
    removal_reason = drug[header1.index('Notes- Reason for removal')].lower()
    if drug[header0.index('Filtering')].lower()=='no' 'approval' in removal_reason:
        return 1
    if 'clinical' in removal_reason and 'class' not in removal_reason:
        return 2
    if 'cc50' in removal_reason or 'si' in removal_reason:
        return 3
    if 'ic50' in removal_reason:
        return 4
    if 'administration' in removal_reason:
        return 5
    if 'cad' in removal_reason or 'pains' in removal_reason:
        return 6
    if 'class' in removal_reason:
        return 7
    if 'indication' in removal_reason:
        return 8
    if 'pregnancy' in removal_reason:
        return 9
    if 'side effects' in removal_reason:
        return 10
    return 11


def mail_invalid_drugs(recepients, invalid_drugs, username, timestamp):
    html = get_template('mail_templates/invalid-drugs.html').render({'drugs': invalid_drugs, 'uploaded_by': username, 'timestamp': timestamp})
    subject = "List of invalid drugs in latest drug upload on CoviRx"
    sendmail(html, subject, recepients)
