# Generated by Django 3.2.6 on 2022-04-27 10:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0026_alter_article_relevant'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AddDrug',
            new_name='ContributedDrug',
        ),
    ]
