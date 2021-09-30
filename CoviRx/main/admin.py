from django.contrib import admin
from django.db import models
from django import forms
from django.forms import Textarea
from django.urls import reverse
from django.utils.html import format_html

from .models import Contact, CustomFields, Drug, DrugBulkUpload

from flat_json_widget.widgets import FlatJsonWidget


class JsonDocumentForm(forms.ModelForm):
    class Meta:
        widgets = {
            'custom_fields': FlatJsonWidget
        }


@admin.action(description='Delete all drugs from database')
def delete_all_drugs(modeladmin, request, queryset):
    Drug.objects.all().delete()


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {
            'widget': Textarea(
                attrs={'rows': 1, 'cols': 80, 'style': 'height: 1.5em;'}
            )
        }
    }
    form = JsonDocumentForm
    actions = [delete_all_drugs]

    class Media:
        js = ('main/js/jquery-3.6.0.min.js', 'main/js/drug_individual_admin.js',)
        css = {
            'all': ('main/css/drug_individual_admin.css',)
        }


@admin.register(DrugBulkUpload)
class DrugBulkAdmin(admin.ModelAdmin):
    def get_fields(self, *args, **kwargs):
        fields = ('id', 'date_uploaded', 'valid_count', 'invalid_count', 'csv_file',  'invalid_drugs')
        return fields

    def get_list_display(self, *args, **kwargs):
        return super().get_list_display(*args, **kwargs)+('date_uploaded',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CustomFields)
class CustomFieldsAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {
            'widget': Textarea(
                attrs={'rows': 1, 'cols': 80, 'style': 'height: 1.5em;'}
            )
        }
    }

    def get_list_display(self, *args, **kwargs):
        return ('name', )

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    def get_fields(self, *args, **kwargs):
        fields = ('name', 'email', 'date_uploaded', 'phone', 'organisation', 'subject', 'message')
        return fields

    def get_list_display(self, *args, **kwargs):
        return super().get_list_display(*args, **kwargs)+('email', 'subject', 'date_uploaded')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
