# Generated by Django 3.2.6 on 2021-10-30 07:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_auto_20211030_0002'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adddrug',
            name='indication',
        ),
        migrations.RemoveField(
            model_name='adddrug',
            name='indication1',
        ),
        migrations.RemoveField(
            model_name='adddrug',
            name='pathway',
        ),
        migrations.RemoveField(
            model_name='adddrug',
            name='pathway1',
        ),
        migrations.AddField(
            model_name='adddrug',
            name='email',
            field=models.EmailField(blank=True, max_length=50, verbose_name='Email'),
        ),
        migrations.AddField(
            model_name='adddrug',
            name='isInvitro',
            field=models.BooleanField(default=False, verbose_name='Is Invitro?'),
        ),
        migrations.AddField(
            model_name='adddrug',
            name='isInvivo',
            field=models.BooleanField(default=False, verbose_name='Is Invivo?'),
        ),
        migrations.AddField(
            model_name='adddrug',
            name='organisation',
            field=models.CharField(blank=True, max_length=158, verbose_name='Organization'),
        ),
        migrations.AddField(
            model_name='adddrug',
            name='results',
            field=models.CharField(blank=True, max_length=50, verbose_name='Activity Results'),
        ),
        migrations.AddField(
            model_name='adddrug',
            name='vitvio',
            field=models.CharField(blank=True, max_length=50, verbose_name='VitVio'),
        ),
        migrations.AlterField(
            model_name='adddrug',
            name='drugName',
            field=models.TextField(blank=True, verbose_name='Drug Name'),
        ),
    ]
