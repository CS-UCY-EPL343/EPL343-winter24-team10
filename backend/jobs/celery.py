from celery import Celery
import os
import mysql.connector
from datetime import datetime

# Initialize Celery app
app = Celery(
    'tasks', 
    broker=f'pyamqp://{os.getenv("RABBITMQ_HOST")}:5672//',  # RabbitMQ connection string
    backend=f'redis://{os.getenv("REDIS_HOST")}:6379/0'  # Redis connection string for task results
)

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

@app.task
def send_notification(user_id, stock_id, threshold):
    """Send notification for price threshold breach."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT stock_name, close_price, date FROM STOCK 
            WHERE stock_id = %s ORDER BY date DESC LIMIT 1
        """, (stock_id,))
        result = cursor.fetchone()
        
        if result:
            stock_name, close_price, date = result
            if close_price >= threshold:
                message = f"Stock {stock_name} has breached your threshold of {threshold}. Current price: {close_price} on {date}."
                
                print(f"Sending notification: {message}")

                cursor.execute("""
                    INSERT INTO NOTIFICATIONS (user_id, stock_id, threshold, message, date_sent) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, stock_id, threshold, message, datetime.now()))
                conn.commit()

    except Exception as e:
        print(f"Error sending notification: {e}")
    finally:
        cursor.close()
        conn.close()
