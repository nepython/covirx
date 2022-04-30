# Sets background theme for admin page
from django.db import migrations

from .. import create_admin_theme


def forwards_func(apps, schema_editor):
    Theme = apps.get_model("admin_interface", "Theme")
    create_admin_theme(Theme)

def reverse_func(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
        ('admin_interface', '0021_file_extension_validator'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
