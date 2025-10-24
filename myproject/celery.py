"""
Celery configuration for the Django project
"""

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

app = Celery("myproject")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Periodic task: cleanup PDFs older than expiry minutes, runs every 10 mins
app.conf.beat_schedule = {
    "cleanup-temp-pdfs-every-minute": {
        "task": "posts.tasks.cleanup_old_temp_pdfs",
        "schedule": 600.0,                          # every 10 minutes
        "args": (settings.PDF_LINK_EXPIRY_MINUTES,),   
    },
}