# OLD
"""from __future__ import absolute_import, unicode_literals

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app
from celery import Celery

import os

__all__ = ['celery_app']
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')
app = Celery('proj')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
"""


from __future__ import absolute_import, unicode_literals

from .celery import app as celery_app

__all__ = ['celery_app']
