from __future__ import absolute_import, unicode_literals
import os
import apps
from GIB2 import settings
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GIB2.settings')

app = Celery('GIB2')
app.config_from_object('django.conf:settings', 'CELERY')
app.autodiscover_tasks(settings.INSTALLED_APPS)
