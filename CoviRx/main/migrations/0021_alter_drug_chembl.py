# Generated by Django 3.2.6 on 2022-01-30 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0020_auto_20220130_0146'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drug',
            name='chembl',
            field=models.TextField(blank=True, null=True, unique=True),
        ),
    ]