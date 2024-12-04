from celery import Celery
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from .models import get_forex_data  # Assuming you have a function to fetch forex data
from .models import get_user_notifications  # Get notifications set by users

app = Celery('tasks', broker='pyamqp://guest@localhost//')

def send_email(to_email: str, subject: str, body: str):
    from_email = "christosxifias@gmail.com"
    password = 'your-email-password'
    
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")

@app.task
def check_forex_notifications():
    """Task to check user notifications based on forex data"""
    now = datetime.now()
    notifications = get_user_notifications()  # Get all active notifications for users

    for notification in notifications:
        # Get the forex data for the requested currency pair
        forex_data = get_forex_data(notification['currency_pair'])

        # Check if the rate matches the condition
        if forex_data['rate'] == notification['target_rate']:
            # Send email notification
            email_body = f"""
            <html>
                <body>
                    <p>Dear {notification['username']},</p>
                    <p>The currency pair {notification['currency_pair']} has reached the target rate of {notification['target_rate']}.</p>
                </body>
            </html>
            """
            send_email(notification['email'], f"Notification: {notification['currency_pair']} Reached Target", email_body)
