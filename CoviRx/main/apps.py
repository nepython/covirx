from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
    verbose_name = 'CoviRx'

    def ready(self):
        try:
            from django.core.cache import cache
            from .models import CustomFields
            cache.set(
                'custom_fields',
                CustomFields.objects.values_list('name', flat=True),
                None
            )
        except: # error can occur during migrations
            pass
