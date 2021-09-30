from django.contrib import admin
from django.urls import path

from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('drug-bulk-upload',csv_upload, name='drug-bulk-upload'),
    path('drug-bulk-upload-update', csv_upload_updates, name='drug-bulk-upload-update'),
    path('api/drugs-metadata', autocomplete, name='drugs-metadata'),
    path('contact', contact, name='contact'),
]

admin.site.index_title  =  "Welcome to the Admin Panel"
