import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

app = Celery("ecommerce")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.task_default_queue = "default"
app.autodiscover_tasks()
