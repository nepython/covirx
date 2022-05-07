import reversion
from django.contrib import admin, messages
from django.db import models
from django import forms
from django.forms import Textarea
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from reversion.admin import VersionAdmin

from .models import Article, Contact, CustomFields, Drug, DrugBulkUpload, ContributedDrug

from flat_json_widget.widgets import FlatJsonWidget


admin.site.register(ContributedDrug)

class PermissionVersionAdmin(VersionAdmin):
	def _reversion_revisionform_view(self, request, version, *args, **kwargs):
		if not request.user.is_superuser:
			messages.error(request, "Recovery can be made only by super user.")
			return redirect("{}:{}_{}_changelist".format(self.admin_site.name, self.opts.app_label, self.opts.model_name))
		else:
			return super()._reversion_revisionform_view(request, version, *args, **kwargs)


class JsonDocumentForm(forms.ModelForm):
    class Meta:
        widgets = {
            'custom_fields': FlatJsonWidget
        }


@admin.action(description='Delete all drugs from database')
def delete_all_drugs(modeladmin, request, queryset):
    Drug.objects.all().delete()


@admin.register(Drug)
class DrugAdmin(PermissionVersionAdmin):
    formfield_overrides = {
        models.TextField: {
            'widget': Textarea(
                attrs={'rows': 1, 'cols': 80, 'style': 'height: 1.5em;'}
            )
        }
    }
    form = JsonDocumentForm
    # Needs to be decided if this action should be removed
    # actions = [delete_all_drugs]
    actions = None
    search_fields = ['name']

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def _create_revision(self, drug, user):
        with reversion.create_revision():
            # Save previous version to be able to restore in future
            reversion.add_to_revision(drug)
            reversion.set_user(user)
            reversion.set_comment('Drug was deleted.')

    def delete_model(self, request, obj):
        self._create_revision(obj, request.user)
        super().delete_model(request, obj)

    class Media:
        js = ('main/js/jquery-3.6.0.min.js', 'admin/js/drug_customfield.js',)
        css = {
            'all': ('admin/css/drug_customfield.css',)
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


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {
            'widget': forms.Textarea(
                attrs={'rows': 1, 'cols': 80, 'style': 'height: 1.5em;'}
            )
        }
    }

    def has_module_permission(self, request, object=None):
        return request.user.is_superuser


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
