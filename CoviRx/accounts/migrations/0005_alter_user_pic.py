# Generated by Django 3.2.6 on 2021-12-06 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_user_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='pic',
            field=models.TextField(default='https://randomuser.me/api/portraits/lego/2.jpg', verbose_name='Profile picture link'),
        ),
    ]