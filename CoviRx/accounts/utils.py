import pytz
from django.conf import settings

tzinfo = pytz.timezone(settings.TIME_ZONE)
# Number od days after which invite expires
INVITE_EXPIRY = 7
