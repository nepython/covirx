from django import forms
from django.forms import ModelForm

from .models import DrugBulkUpload
from .models import AddDrug


class DrugForm(ModelForm):
  class Meta:
    model = AddDrug
    fields = "__all__"
    

    widgets = {
      'personName': forms.TextInput(attrs={'class':'form-control','placeholder':'Name of Person Working on Drug'}),

      #Original Indication
      'email': forms.EmailInput(attrs={'class':'form-control','placeholder':'Please enter your valid email address'}),
      
      'organisation': forms.TextInput(attrs={'class':'form-control','placeholder':'Organization where the work was carried out'}),
      
      'drugName':forms.TextInput(attrs={'class':'form-control','placeholder':'Tolterodine (tartrate)'}),
      'vitvio':forms.TextInput(attrs={'class':'form-control','placeholder':'Invitro; Invivo; Ex vivo assay'}),

      'results': forms.TextInput(attrs={'class':'form-control','placeholder':'Activity Results(IC50/EC50)'}),
    }


class DrugBulkUploadForm(forms.ModelForm):
  class Meta:
    model = DrugBulkUpload
    fields = ('csv_file',)
