from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from passlib.context import CryptContext
from api.jwt_auth import create_access_token ,create_email_verification_token
from api.dashboard import fetch_forex_data, plot_forex_data, fetch_news_for_currency
from datetime import timedelta
<<<<<<< HEAD
from jobs.celery import send_notification
from pydantic import BaseModel

# from jobs.celery import celery_app
=======
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email_validator import validate_email, EmailNotValidError
>>>>>>> 878e7b8b05f9e1fd92d51a18686bd6abdf3eccfd

import os
import jwt
import smtplib
import logging
import requests
import mysql.connector

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Mount static and picture directories
app.mount("/static", StaticFiles(directory="/app/frontend/static"), name="static")
app.mount("/pictures", StaticFiles(directory="/app/frontend/pictures"), name="pictures")

# Setup templates
templates = Jinja2Templates(directory="/app/frontend/templates")

# Environment variables for database and API
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALPHA_VANTAGE_API_KEY = 'Z9PPR7T1ICWXAP1P'
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"


NEWS_API_KEY='09a61846155e40b08a46dba4aa59ef41'

send_notification.delay(user_id=16, stock_id=101, threshold=100.00)


# Utility Functions
def get_db_connection():
    """Establish a connection to the database."""
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
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


def verify_password(plain_password, hashed_password):
    """Verify if the password matches the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str):
    """Hash a password."""
    return pwd_context.hash(password)


# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    """Render the registration page."""
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register_user(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    """Register a new user and send email verification."""
    # Validate email format
    try:
        valid = validate_email(email)
        email = valid.email  # Clean the email
    except EmailNotValidError as e:
        return {"Error_Message": f"Invalid email format: {str(e)}"}
    
    # Hash the password
    hashed_password = hash_password(password)
    
    # Store the user data in the database
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO USER (email, password, username, lvl, registration_date)
            VALUES (%s, %s, %s, 0, NOW())
        """, (email, hashed_password, name))
        conn.commit()
        
        # Generate email verification token
        verification_token = create_email_verification_token(email)
        
        # Create verification link
        verification_link = f"http://localhost:8000/verify_email?token={verification_token}"
        
        # Send the verification email
        email_body = f"""
        <html>
            <body>
                <p>Hello {name},</p>
                <p>Thank you for registering. Please click the link below to verify your email:</p>
                <a href="{verification_link}">Verify Email</a>
            </body>
        </html>
        """
        send_email(email, "Email Verification", email_body)
        
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        conn.rollback()
        return {"Error_Message": "An error occurred while registering the user."}
    finally:
        cursor.close()
        conn.close()
        
SECRET_KEY='secret_key'
ALGORITHM='HS256'
@app.get("/verify_email")
async def verify_email(request: Request, token: str):
    """Verify the user's email using the token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        # Update the user's email verification status in the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE USER SET email_verified = TRUE WHERE email = %s", (email,))
        conn.commit()
        
        return {"message": "Email verified successfully!"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    """Authenticate the user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Password, user_id FROM USER WHERE Email = %s", (email,))
        result = cursor.fetchone()
        if result:
            stored_password, user_id = result
            if verify_password(password, stored_password):
                logger.info(f"User {email} logged in successfully.")
                # Commenting out JWT part
                # access_token = create_access_token(data={"sub": str(user_id)}, expires_delta=timedelta(minutes=30))
                # response = RedirectResponse(url="/dashboard", status_code=303)
                # response.set_cookie("access_token", access_token, httponly=True, secure=True, max_age=1800)
                # return response
                return RedirectResponse(url="/dashboard", status_code=303)
        return templates.TemplateResponse("login.html", {"request": request, "Error_Message": "Incorrect Email or Password"})
    except Exception as e:
        logger.error(f"Login error: {e}")
        return templates.TemplateResponse("login.html", {"request": request, "Error_Message": "An error occurred"})
    finally:
        cursor.close()
        conn.close()

from datetime import datetime, timedelta


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, currency2: str = Form(...)):

    currency1 = "USD" 
    start_date = "2014-11-07" 
    end_date = datetime.today()

    # Fetch forex data for the selected currencies and date range
    forex_data = fetch_forex_data(currency1, currency2, start_date, end_date.strftime('%Y-%m-%d'))

    # Plot the forex data
    graph_data = plot_forex_data(forex_data, currency1, currency2)

    if graph_data is None:
        error_message = "No data available for the selected currencies and date range."
        return templates.TemplateResponse("dashboard.html", {"request": request, "error_message": error_message})

    return templates.TemplateResponse(
        "dashboard.html", 
        {"request": request, "graph_data": graph_data, "currency1": currency1, "currency2": currency2}
    )


@app.get("/forgot_password", response_class=HTMLResponse)
async def forgot_password(request: Request):
    """Render the password reset page."""
    return templates.TemplateResponse("new_password.html", {"request": request})



@app.post("/forgot_password", response_class=HTMLResponse)
async def forgot_password_post(request: Request, password: str = Form(...), password1: str = Form(...)):
    """Handle password reset."""
    if password != password1:
        return templates.TemplateResponse("new_password.html", {"request": request, "Error_Message": "Passwords do not match."})
    return templates.TemplateResponse("password_changed.html", {"request": request})


@app.post("/fill_database", response_class=HTMLResponse)
async def fill_database(request: Request):
    """Fill the database with data from Alpha Vantage API."""
    # Define the list of currency pairs (USD as the baseline)
    currency_pairs = ["USD/EUR", "USD/GBP", "USD/JPY", "USD/AUD", "USD/CAD", "USD/CHF", "USD/NZD"]

    # Function to fetch forex data from Alpha Vantage API
    for pair in currency_pairs:
        params = {
            "function": "FX_DAILY",
            "from_symbol": pair.split('/')[0],
            "to_symbol": pair.split('/')[1],
            "apikey": ALPHA_VANTAGE_API_KEY,
            "outputsize": "full",  # 'full' will give all available data
            "datatype": "json"
        }
        
        response = requests.get(ALPHA_VANTAGE_URL, params=params)
        
        if response.status_code == 200:
            forex_data = response.json()
            if "Time Series FX (Daily)" in forex_data:
                data = forex_data["Time Series FX (Daily)"]

                # Establish DB connection to insert data
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    # Loop through the forex data and insert it into the database
                    for date, values in data.items():
                        cursor.execute("""
                            INSERT INTO STOCK (stock_name, date, open_price, high_price, low_price, close_price, value)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            pair,
                            date,
                            values["1. open"],
                            values["2. high"],
                            values["3. low"],
                            values["4. close"],
                            1
                        ))
                    conn.commit()
                    logger.info(f"Forex data for {pair} inserted successfully.")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Error inserting data for {pair}: {e}")
                finally:
                    cursor.close()
                    conn.close()
            else:
                logger.error(f"No data found for {pair}")
        else:
            logger.error(f"Failed to fetch data for {pair}: {response.status_code}")

    # Return a message after filling the database
    return HTMLResponse(content="Database successfully filled with forex data!")

def save_articles_to_db(articles):
    conn = get_db_connection()
    cursor = conn.cursor()

    for article in articles:
        title = article['title']
        description = article['description']
        content = article['content']
        url = article['url']
        published_at = article['publishedAt']

        try:
            cursor.execute("""
                INSERT INTO NEWS (title, description, content, url, published_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (title, description, content, url, published_at))
            conn.commit()
        except Exception as e:
            logger.error(f"Error saving article: {e}")
            conn.rollback()
    cursor.close()
    conn.close()


@app.get("/fetch_news", response_class=HTMLResponse)
async def fetch_news(request: Request):
    url = f"https://newsapi.org/v2/everything?q=currency&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    news = response.json()
    if news['status'] == 'ok':
        articles = news['articles']
        save_articles_to_db(articles)
    return templates.TemplateResponse("news.html", {"request": request, "articles": articles})


@app.get("/notifications",response_class=HTMLResponse)
async def notifications(request: Request):
<<<<<<< HEAD
    return templates.TemplateResponse("notifications.html", {"request": request})


# Define the notification model
class Notification(BaseModel):
    currency: str
    threshold: float
    user_id: int
    stock_id: int

@app.post("/notifications", response_class=HTMLResponse)
async def notifications_post(request: Request, notification: Notification):
    """Save a new notification in the database."""
    
    # Validate input (e.g., check if threshold is a positive number)
    if notification.threshold <= 0:
        return templates.TemplateResponse("notifications.html", {"request": request, "Error_Message": "Threshold must be positive"})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO NOTIFICATIONS (threshold, user_id, stock_id, currency)
            VALUES (%s, %s, %s, %s)
        """, (notification.threshold, notification.user_id, notification.stock_id, notification.currency))
        conn.commit()
        
        logger.info(f"Notification saved successfully for user {notification.user_id} with threshold {notification.threshold} and stock ID {notification.stock_id}.")
        return RedirectResponse(url="/notifications", status_code=303)
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving notification: {e}")
        return templates.TemplateResponse("notifications.html", {"request": request, "Error_Message": "An error occurred while saving the notification."})
    finally:
        cursor.close()
        conn.close()


# @celery_app.task
# def check_and_send_notifications():
#     """Check forex rates and send notifications for any thresholds that are exceeded."""
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)
    
#     try:
#         cursor.execute("""
#             SELECT n.notification_id, n.threshold, n.user_id, n.stock_id, s.stock_name, s.value
#             FROM NOTIFICATIONS n
#             JOIN STOCK s ON n.stock_id = s.stock_id
#         """)
#         notifications = cursor.fetchall()
        
#         for notification in notifications:
#             if notification['value'] >= notification['threshold']:
#                 # Call your send_notification function to notify the user
#                 send_notification(notification['user_id'], notification['stock_name'], notification['value'])
#                 logger.info(f"Notification sent to user {notification['user_id']} for stock {notification['stock_name']}.")
        
#     except Exception as e:
#         logger.error(f"Error checking notifications: {e}")
#     finally:
#         cursor.close()
#         conn.close()
        
# @celery_app.task
# def check_and_send_notifications():
#     """Check forex rates and send notifications for any thresholds that are exceeded."""
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)
    
#     try:
#         cursor.execute("""
#             SELECT n.notification_id, n.threshold, n.user_id, n.stock_id, s.stock_name, s.value
#             FROM NOTIFICATIONS n
#             JOIN STOCK s ON n.stock_id = s.stock_id
#         """)
#         notifications = cursor.fetchall()
        
#         for notification in notifications:
#             if notification['value'] >= notification['threshold']:
#                 # Call your send_notification function to notify the user
#                 send_notification(notification['user_id'], notification['stock_name'], notification['value'])
#                 logger.info(f"Notification sent to user {notification['user_id']} for stock {notification['stock_name']}.")
        
#     except Exception as e:
#         logger.error(f"Error checking notifications: {e}")
#     finally:
#         cursor.close()
#         conn.close()
=======
    """Render the password reset page."""
    return templates.TemplateResponse("notifications.html", {"request": request})

@app.get("/news", response_class=HTMLResponse)
async def news(request: Request):
    return templates.TemplateResponse("news.html", {"request": request})
>>>>>>> 878e7b8b05f9e1fd92d51a18686bd6abdf3eccfd
