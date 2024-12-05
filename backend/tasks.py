import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from celery import shared_task
import smtplib
import mysql.connector
import os

#from .models import get_forex_data  # Assuming you have a function to fetch forex data
#from .models import get_user_notifications  # Get notifications set by USER

# Function to connect to MySQL database
def get_db_connection():
    """Establish a connection to the database."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4",
        collation="utf8mb4_general_ci",
    )

def send_email(to_email: str, subject: str, body: str):
    from_email = "christosxifias@gmail.com"
    password = 'qaka svdx huhr akxu'
    
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

@shared_task
def check_notifications():
    """Check thresholds and send notifications if conditions are met."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get all notifications and the latest prices
        query = """
        SELECT 
            u.email, 
            u.username, 
            n.stock_id, 
            n.threshold, 
            s.stock_name, 
            s.close_price, 
            s.date, 
            n.notification_id AS notification_id
        FROM
            NOTIFICATIONS n
        JOIN 
            USER u ON u.user_id = n.user_id
        JOIN 
            STOCK s ON s.stock_id = n.stock_id
        WHERE 
            s.date = (SELECT MAX(date) FROM STOCK WHERE stock_id = s.stock_id)
        """
        cursor.execute(query)
        notifications = cursor.fetchall()

        for notification in notifications:
            stock_name = notification['stock_name']
            close_price = notification['close_price']
            threshold = notification['threshold']
            email = notification['email']
            username = notification['username']

            if close_price >= threshold:
                # Send email
                subject = f"Stock Alert: {stock_name} breached {threshold}"
                body = f"""
                <html>
                    <body>
                        <p>Dear {username},</p>
                        <p>The stock <strong>{stock_name}</strong> has breached your threshold of {threshold}.</p>
                        <p>Current price: {close_price} on {notification['date']}.</p>
                    </body>
                </html>
                """
                send_email(email, subject, body)

    except Exception as e:
        print(f"Error checking notifications: {e}")
    finally:
        cursor.close()
        conn.close()
