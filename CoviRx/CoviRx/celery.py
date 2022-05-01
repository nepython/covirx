import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoviRx.settings')

app = Celery()
app.conf.beat_schedule = {
    'mine_articles': {
        'task': 'main.mine_articles.scrape_google_scholar',
        'schedule': crontab(0, 0, day_of_month='10'), # Day chosen arbitrarily
    },
    'create_monthly_backup': {
        'task': 'main.create_backup.create_backup_and_send_restore_email',
        'schedule': crontab(0, 0, day_of_month='1'), # Execute on the first day of every month.
    },
}
app.config_from_object('django.conf:settings')
