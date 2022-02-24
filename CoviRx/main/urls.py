from django.urls import path, include
from . import views
from .views import *


urlpatterns = [
    path('', home, name='home'),
    path('drug/<drug_id>', individual_drug, name='individual-drug'),
    path('api/similar/<drug_id>', similar_drugs_json, name='similar-drugs-json'),
    path('drug-bulk-upload',csv_upload, name='drug-bulk-upload'),
    path('drug-bulk-upload-update', csv_upload_updates, name='drug-bulk-upload-update'),
    path('api/drugs-metadata', autocomplete, name='drugs-metadata'),
    path('organisations', organisations, name='organisations'),
    path('contact', contact, name='contact'),
    path('cookie-policy', cookie_policy, name='cookie-policy'),
    path('references', references, name='references'),
    path('api/charts-json', charts_json, name='charts-json'),
    path('add_drug', add_drug, name='add-drug'),
    path('list_drugs', list_drugs, name='list-drugs'),
    path('show_drug/<drug_id>', show_drug, name='show-drug'),
    path('drug_csv',drug_csv,name='drug_csv'),
    path('target-models', target_models, name='target_models'),
]
