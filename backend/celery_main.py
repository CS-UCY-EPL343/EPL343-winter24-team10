from celery import Celery
from celery.schedules import crontab
import os


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
# Initialize Celery app
app = Celery('tasks')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'check-notifications-every-30-seconds': {
        'task': 'backend.tasks.check_notifications',
        'schedule': 30.0,  # Run every 30 seconds
    },
}

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))