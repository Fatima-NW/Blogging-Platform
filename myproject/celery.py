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

# Periodic task: cleanup PDFs older than 10 mins, runs every 5 mins
app.conf.beat_schedule = {
    "cleanup-temp-pdfs-every-minute": {
        "task": "posts.tasks.cleanup_old_temp_pdfs",
        "schedule": 300.0,        # every 5 minutes
        "args": (10,),            # max_age_minutes = 10
    },
}