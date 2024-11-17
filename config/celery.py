from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
# This tells Celery where to find the Django settings (config.settings) to configure itself.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize the Celery application with the name 'config'
# This creates the Celery app instance, which will be used to manage tasks.
app = Celery('config')

# Load task modules from all registered Django app configs.
# It tells Celery to look for tasks in all Django apps that are listed in `INSTALLED_APPS`.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically discover tasks in installed apps (based on task module naming convention).
# It looks for tasks in each app that has a `tasks.py` module.
app.autodiscover_tasks()

# Enable retrying connections on startup
# This ensures Celery retries connecting to the broker (e.g., Redis) if the connection fails.
app.conf.broker_connection_retry_on_startup = True

# Auto-discover tasks in installed apps using the settings from INSTALLED_APPS
# It allows Celery to discover tasks dynamically from the Django apps.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Define a simple debug task to print out the request info
# This task can be called to debug or inspect Celery requests.
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
