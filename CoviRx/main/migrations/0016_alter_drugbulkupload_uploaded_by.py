# Generated by Django 3.2.6 on 2021-12-17 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_auto_20211206_2109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drugbulkupload',
            name='uploaded_by',
            field=models.CharField(max_length=100),
        ),
    ]
