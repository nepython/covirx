from django import forms

from .models import DrugBulkUpload

class DrugBulkUploadForm(forms.ModelForm):
  class Meta:
    model = DrugBulkUpload
    fields = ('csv_file',)
