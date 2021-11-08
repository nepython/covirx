from django.urls import path, include
from . import views
from .views import *


urlpatterns = [
    path('', home, name='home'),
    path('drug-bulk-upload',csv_upload, name='drug-bulk-upload'),
    path('drug-bulk-upload-update', csv_upload_updates, name='drug-bulk-upload-update'),
    path('api/drugs-metadata', autocomplete, name='drugs-metadata'),
    path('team', team, name='team'),
    path('contact', contact, name='contact'),
    path('references', references, name='references'),
    path('api/charts-json', charts_json, name='charts-json'),
    path('addDrug', addDrug, name='addDrug'),
    path('list_drugs', list_drugs, name='list-drugs'),
    path('show_drug/<drug_id>', show_drug, name='show-drug'),
    path('drug_csv',drug_csv,name='drug_csv'),
]
