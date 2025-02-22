import os

from celery import Celery
from celery.signals import worker_ready, worker_shutdown
from celery.schedules import crontab
from django.conf import settings
import asyncio
from utils.controllers.metatrader import AsyncMT5Controller
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tradeproject.settings")

app = Celery('trading_project', include=['utils.tasks'])
app.config_from_object('django.conf:settings', namespace='CELERY')


app.conf.beat_schedule = {
    'schedule-5-minute': {
        'task': 'utils.tasks.five_minute_signal',
        'schedule': crontab(minute='*/5'),
    },
    'schedule-1-minute': {
        'task': 'utils.tasks.one_minute_signal',
        'schedule': crontab(minute='*/1'),
    },
    "set-signal-status": {
        "task": "utils.tasks.update_signal_statuses",
        "schedule": crontab(minute='*/1'),
    }
}


@worker_ready.connect
def init_worker(**_):
    """Initialize MT5 connection pool when worker starts"""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(AsyncMT5Controller.get_instance())

@worker_shutdown.connect
def cleanup_worker(**_):
    """Cleanup MT5 connections when worker shuts down"""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(AsyncMT5Controller.cleanup_connections())

app.autodiscover_tasks(settings.INSTALLED_APPS)