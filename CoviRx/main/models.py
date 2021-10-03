import os
import uuid
from datetime import datetime
from copy import deepcopy

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class CustomFields(models.Model):
    name = models.TextField(unique=True, null=False, blank=False, help_text="Enter the name of this field exactly as in the Excel sheet.")
    verbose_name = models.TextField(unique=True, null=True, blank=True, help_text="Enter the name of this field in the format in which you want the user to view the field.")

    def save(self, *args, **kwargs):
        if not self.verbose_name:
            self.verbose_name = self.name
        self.name = self.name.lower().replace(' ', '_')
        super().save(*args, **kwargs)
        cache.set(
            'custom_fields',
            self.__class__.objects.values_list('name', flat=True), None
        )

    def __str__(self):
        return f"{self.verbose_name}"

    class Meta:
        verbose_name_plural = "Custom fields"

class Drug(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, null=False, unique=True)
    # Drug Structure
    formula = models.TextField(blank=True, null=True)
    smiles = models.TextField(blank=True, null=True, unique=True)
    inchi = models.TextField(blank=True, null=True, unique=True)
    # Drug identifiers
    synonyms = models.TextField(blank=True, null=True, unique=True)
    cas = models.TextField(blank=True, null=True, unique=True)
    chebl = models.TextField(blank=True, null=True, unique=True)
    chembl = models.TextField(blank=True, null=True)
    pubchem = models.TextField(blank=True, null=True, unique=True)
    chembank = models.TextField(blank=True, null=True)
    drugbank = models.TextField(blank=True, null=True)
    indication_class = models.TextField(blank=True, null=True, verbose_name='indication_class/category')
    references = models.TextField(blank=True, null=True)
    LABEL_CHOICES = [
        ('1', _('White')),
        ('2', _('Green')),
        ('3', _('Red')),
        ('4', _('Amber')),
    ]
    label = models.CharField(max_length=1, choices=LABEL_CHOICES, default='1')
    custom_fields = models.JSONField(default=dict, blank=True)

    @classmethod
    def get_or_create(cls, kwargs):
        try:
            drug = Drug.objects.get(name=kwargs['name'])
        except:
            drug = Drug()
        drug.__dict__.update(kwargs)
        print(drug.name)
        drug.full_clean()
        drug.save()
        return drug

    def clean(self):
        if not self.smiles:
            self.smiles = None
        if not self.cas:
            self.cas = None
        if not self.chebl:
            self.chebl = None
        if not self.pubchem:
            self.pubchem = None

    def __str__(self):
        return f"{self.name}"

    class Meta:
        # indexing a field makes it faster for carrying search on that field in the db
        indexes = [
            models.Index(fields=['name',]),
            models.Index(fields=['smiles',]),
            models.Index(fields=['inchi',]),
            models.Index(fields=['synonyms',]),
            models.Index(fields=['cas',]),
            models.Index(fields=['chebl',]),
            models.Index(fields=['pubchem',]),
        ]


def storage_path(instance, filename):
    """ file will be uploaded to MEDIA_ROOT/drugs/<filename>/<datetime> """
    return f'drugs/{datetime.now()}-{filename}'


class DrugBulkUpload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_uploaded = models.DateTimeField(auto_now=True)
    csv_file = models.FileField(upload_to=storage_path)
    invalid_drugs = models.TextField(blank=True, null=True)
    valid_count = models.IntegerField(default=0)
    invalid_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)

    def invalid_drug(self):
        """ Increments the counter for invalid drugs, is useful to display while uploading """
        self.invalid_count+=1
        cache.set('invalid_count', self.invalid_count, None)

    def valid_drug(self):
        """ Increments the counter for valid drugs, is useful to display while uploading """
        self.valid_count+=1
        cache.set('valid_count', self.valid_count, None)


class Contact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_uploaded = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=158, blank=False, null=False)
    email = models.EmailField(blank=False)
    subject = models.CharField(max_length=158, blank=False, null=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    organisation = models.CharField(max_length=158, blank=True, null=True)
    message = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


@receiver(models.signals.post_delete, sender=DrugBulkUpload)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `DrugBulkUpload` object is deleted.
    """
    if instance.csv_file:
        if os.path.isfile(instance.csv_file.path):
            os.remove(instance.csv_file.path)


@receiver(models.signals.post_save, sender=CustomFields)
def auto_add_custom_field(sender, instance, **kwargs):
    """
    Add the custom field with no value to every drug in database
    """
    for drug in Drug.objects.all():
        drug.custom_fields[instance.name] = ''
        drug.save()


@receiver(models.signals.post_delete, sender=CustomFields)
def auto_delete_custom_field(sender, instance, **kwargs):
    """
    Delete the custom field for every drug in database
    """
    for drug in Drug.objects.all():
        drug.custom_fields.pop(instance.name, None)
        drug.save()
