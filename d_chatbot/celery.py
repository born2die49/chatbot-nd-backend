# d_chatbot/celery.py
import os
from celery import Celery
from django.conf import settings # Import settings directly for diagnostics

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'd_chatbot.settings')

app = Celery('d_chatbot')

# Diagnostic print:
print(f"--- DIAGNOSTIC: DJANGO_SETTINGS_MODULE is {os.environ.get('DJANGO_SETTINGS_MODULE')} ---")
try:
    print(f"--- DIAGNOSTIC: settings.CELERY_BROKER_URL is '{settings.CELERY_BROKER_URL}' ---")
except AttributeError:
    print("--- DIAGNOSTIC: settings.CELERY_BROKER_URL is NOT SET in Django settings! ---")
except ImportError:
    print("--- DIAGNOSTIC: Could not import Django settings! ---")


app.config_from_object('django.conf:settings', namespace='CELERY')

# Diagnostic print after loading config:
print(f"--- DIAGNOSTIC: Celery app.conf.broker_url is '{app.conf.broker_url}' ---")
print(f"--- DIAGNOSTIC: Celery app.conf.result_backend is '{app.conf.result_backend}' ---")


app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')