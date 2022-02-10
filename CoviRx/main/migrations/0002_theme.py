# Sets background theme for admin page
from django.db import migrations
import subprocess

from CoviRx.settings import BASE_DIR


def forwards_func(apps, schema_editor):
    subprocess.run([f"{BASE_DIR}/manage.py", "loaddata", "admin_interface_theme_uswds.json"])
    Theme = apps.get_model("admin_interface", "Theme")
    theme = Theme.objects.get(name="USWDS")
    theme.active=True
    theme.logo.name = "main/static/main/images/covirx_light.png"
    theme.title = "CoviRx: Covid19 Drug Repurposing Database"
    theme.save()

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
