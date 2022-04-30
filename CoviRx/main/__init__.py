from django.core.management import call_command

def create_admin_theme(Theme):
    if Theme.objects.filter(name="USWDS").exists():
        return
    call_command('loaddata', 'admin_interface_theme_uswds.json')
    theme = Theme.objects.get(name="USWDS")
    theme.active = True
    theme.logo.name = "main/static/main/images/covirx_light.png"
    theme.title = "CoviRx: Covid19 Drug Repurposing Database"
    theme.save()
