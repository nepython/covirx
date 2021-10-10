import pytz
from django.conf import settings

tzinfo = pytz.timezone(settings.TIME_ZONE)
