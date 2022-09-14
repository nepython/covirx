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
    path('contribute/add_drug', save_contributed_drug, name='add-drug'),
    path('contribute/list_drugs', list_contributed_drugs, name='list-drugs'),
    path('contribute/show_drug/<drug_id>', show_contributed_drug, name='show-drug'),
    path('contribute/download_csv',download_contributed_drugs_csv,name='drug_csv'),
    path('target-models', target_models, name='target_models'),
    path('clinical-trials/<drug_name>', clinical_trials, name='clinical_trials'),
    path('articles-found', articles_found, name='articles_found'),
    path('articles-found-for-downselected-drugs', downselected_drugs_articles_found, name='downselected_drugs_articles_found'),
    path('related-articles/<drug_name>', related_articles, name='related_articles'),
    path('monitor-article-verification', monitor_article_verification, name='monitor-article-verification'),
    path('api/update-drug/<drug_name>', update_drug, name='update_drug'),
    path('api/restore/<backup_id>', restore_db, name='restore_db'),
]
