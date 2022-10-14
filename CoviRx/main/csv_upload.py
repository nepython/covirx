import csv
import logging
from copy import deepcopy

from django.core.cache import cache
from django.template.loader import get_template

from .models import Drug
from .utils import store_fields, verbose_names, invalid_drugs, target_model_names, sendmail


def get_invalid_headers(obj):
    file_path = obj.csv_file.path
    with open(file_path, 'r', encoding='UTF-8') as fp:
        drugs = list(csv.reader(fp, delimiter=','))
        headers = [drug.lower().replace(' ', '_') for drug in drugs[1]]
        invalid_headers = list()
        for field in headers:
            if field not in (store_fields+list(verbose_names.keys())):
                invalid_headers.append(field)
    return invalid_headers


def generate_position(drugs, given_names=target_model_names):
    position = dict()
    prev_target = None
    for i, target in enumerate(drugs[0]):
        if target and prev_target and len(position[prev_target])<2:
            position[prev_target].append(i)
        if target in given_names:
            position[target] = [i]
            prev_target = target
    if (len(position[prev_target])==1):
        position[prev_target].append(len(drugs[0]))
    return position


def save_drugs_from_csv(obj, invalid_headers): #TODO: Make the code less redundant
    file_path = obj.csv_file.path
    custom_fields = cache.get('custom_fields')
    with open(file_path, 'r', encoding='UTF-8') as fp:
        drugs = list(csv.reader(fp, delimiter=','))
        obj.start_upload(len(drugs)-2, invalid_drugs)
        headers = [drug.lower().replace(' ', '_') for drug in drugs[1]]
        position_covid, position_indication = generate_position(drugs, ['COVID Trials']), generate_position(drugs, ['Original Indication'])
        position_pk, position_target = generate_position(drugs, ['PK/PD']), generate_position(drugs)
        position_red_flags = generate_position(drugs, ['Red Flags'])
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
            drug_details['filters_passed'], drug_details['filters_failed'] = filters_passed(drug, drugs[0], drugs[1])
            custom.update(save_positions(drug, position_target, drugs[1], rename_fields={
                'Potency (μM) Concentration at which compound exhibits half-maximal efficacy, AC50. Extrapolated AC50s also include the highest efficacy observed and the concentration of compound at which it was observed.': 'Potency (μM)',
                'Efficacy (%) Maximal efficacy of compound, reported as a percentage of control. These values are estimated based on fits of the Hill equation to the dose-response curves.': 'Efficacy (%)'
            })) # Save the various target models as custom fields
            custom.update(save_positions(drug, position_covid, drugs[1], exclude=['Comments/Notes', 'Analogue in trial'])) # Save the COVID trials data as custom fields
            custom.update(save_positions(drug, position_pk, drugs[1])) # Save the PK/ PD data as custom fields
            custom.update(save_positions(drug, position_indication, drugs[1], exclude=['References'])) # Save the Original indication data as custom fields
            custom.update(save_positions(drug, position_red_flags, drugs[1], exclude=['Breast feeding'])) # Save the Red Flags data as custom fields
            try:
                drug_details['custom_fields'] = custom
                Drug.get_or_create(drug_details)
                obj.valid_drug()
            except Exception as e:
                msg = f'Unable to add drug {drug_details["name"]} because of an error. {repr(e)}'
                logging.getLogger('error_logger').error(msg)
                obj.invalid_drug()
                invalid_drugs[drug_details['name']] = repr(e.error_dict) if hasattr(e, 'error_dict') else repr(e)
    if cache.get('email_recepients'):
        mail_invalid_drugs(cache.get('email_recepients').split(';'), deepcopy(invalid_drugs), obj.uploaded_by, obj.date_uploaded)
    obj.finish_upload(invalid_drugs)


def save_positions(drug, position, headers, exclude=list(), rename_fields=None):
    """
    Args:
        drug (list): Contains all the parameter for the drug
        position (dictionary of list (start, end)): Contains the starting and ending position of columns to store
        rename_fields (dict): if key present in field to be stored then rename it as value
    """
    target_models = dict()
    for target, pos in position.items():
        target_model = dict()
        for h in range(pos[0], pos[1]):
            if headers[h] not in exclude:
                field_name = headers[h]
                if rename_fields and field_name in rename_fields:
                    field_name = rename_fields[field_name]
                target_model[field_name] = drug[h]
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
    """
    A drug could have failed multiple filters since some
    filters were applied in parallel and not sequentially,
    return the filter count which is the least
    """
    removal_reasons = drug[header1.index('Notes- Reason for removal')].lower()
    first_failure = 11
    all_failures = list()
    for reason in removal_reasons.replace(';', ',').split(','):
        filter_failed_at = _filters_passed(reason, drug, header0, header1)
        if filter_failed_at<11:
            all_failures.append(filter_failed_at+1)
        first_failure = min(first_failure, filter_failed_at)
    all_failures = _filters_failed(all_failures, drug, header1)
    return first_failure, all_failures

def _filters_passed(removal_reason, drug, header0, header1):
    # Assay Data not present
    if not removal_reason and drug[header0.index('Filtering')+1]=='NO':
        return 0
    if drug[header1.index('FDA/TGA')] not in ['FDA', 'TGA']:
        return 1
    if 'clinical trial' in removal_reason and 'clinical trials' not in removal_reason:
        return 2
    if 'cc50' in removal_reason or 'si<10' in removal_reason:
        return 3
    if 'same class of drug' in removal_reason:
        return 4
    if 'ic50' in removal_reason:
        return 5
    if 'cad' in removal_reason or 'pains' in removal_reason:
        return 6
    if 'administration' in removal_reason:
        return 7
    if 'pregnancy' in removal_reason:
        return 8
    if 'side effects' in removal_reason:
        return 9
    if 'indication' in removal_reason:
        return 10
    return 11

def _filters_failed(all_failures, drug, header1):
    last_failure = max(all_failures, default=12)
    if last_failure<2 and drug[header1.index('FDA/TGA')] not in ['FDA', 'TGA']:
        all_failures.append(2)
    if last_failure<3 and 'Yes' in drug[header1.index('Covid trials')]:
        all_failures.append(3)
    if last_failure<4 and 'Yes' in drug[header1.index('CC50<10 or SI<10')]:
        all_failures.append(4)
    if last_failure<6 and 'Yes' in drug[header1.index('IC50>10x original indication')]:
        all_failures.append(6)
    if last_failure<7 and not drug[header1.index('PAINS')]:
        all_failures.append(7)
    administration = drug[header1.index('Administration route')]
    if last_failure<8 and administration and 'oral' not in administration.lower():
        all_failures.append(8)
    if last_failure<9 and 'Category' in drug[header1.index('Pregnancy concerns')]:
        all_failures.append(9)
    if last_failure<10 and drug[header1.index('Side effects')] not in ['', 'NA']:
        all_failures.append(10)
    if last_failure<11:
        drug_indication = drug[header1.index('Indication (1)')].lower()
        for indication in ['diagnostic agents', 'pharmaceutical aids', 'supplements']:
            if indication in drug_indication:
                all_failures.append(11)
                break
    filters_failed = dict()
    for filter in range(1,12):
        if filter in all_failures:
            filters_failed[filter] = True
    return filters_failed


def mail_invalid_drugs(recepients, invalid_drugs, username, timestamp):
    html = get_template('mail_templates/invalid-drugs.html').render({'drugs': invalid_drugs, 'uploaded_by': username, 'timestamp': timestamp})
    subject = "List of invalid drugs in latest drug upload on CoviRx"
    sendmail(html, subject, recepients)
