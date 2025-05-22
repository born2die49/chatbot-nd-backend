# d_chatbot/celery.py
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
# Replace 'd_chatbot.settings' with your actual project settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'd_chatbot.settings')

# Create the Celery application instance
# The first argument is the name of the current module, used for naming tasks.
# The second argument 'broker' is the URL of your message broker (e.g., Redis, RabbitMQ).
# This will be automatically configured from your Django settings if you use 'app.config_from_object'.
app = Celery('d_chatbot') #<<<<< Name your celery app after your project

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
# Celery will automatically discover tasks in files named 'tasks.py' in your apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')