# Standard library imports
import os
import logging
import jwt
import smtplib
import requests
import mysql.connector

from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Third-party library imports
from dotenv import load_dotenv
from email_validator import validate_email, EmailNotValidError
from passlib.context import CryptContext
from pydantic import BaseModel

# Database imports
from database.db import drop_tables, create_tables, create_all_stored_procedures

# FastAPI imports
from fastapi import FastAPI, Request, Form, HTTPException, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Local application imports
from api.jwt_auth import create_access_token, create_email_verification_token, verify_access_token
from api.dashboard import fetch_forex_data, plot_forex_data, fetch_news_for_currency
from jobs.celery import send_notification

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

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

NEWS_API_KEY=os.getenv('NEWS_API_KEY')

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
        logger.info("Email sent successfully")
    except Exception as e:
        logger.error(f"Error sending email: {e}")


def verify_password(plain_password, hashed_password):
    """Verify if the password matches the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str):
    """Hash a password."""
    return pwd_context.hash(password)


def set_auth_cookie(response: Response, user_id: int):
    """Set the authentication cookie for the user."""
    access_token = create_access_token(data={"sub": str(user_id)}, expires_delta=timedelta(minutes=30))
    response.set_cookie(
        "access_token", access_token, httponly=True, secure=True, max_age=1800
    )

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = verify_access_token(token)  # Verify the JWT token
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token or expired")
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/register")
async def register_user(request: Request, name: str = Form(...), surname: str = Form(...),email: str = Form(...), password: str = Form(...)):
    """Register a new user and send email verification."""
    try:
        valid = validate_email(email)
        email = valid.email  
    except EmailNotValidError as e:
        return {"Error_Message": f"Invalid email format: {str(e)}"}
    
    hashed_password = hash_password(password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO USER (email, password, username, registration_date, lastname, name)
            VALUES (%s, %s, %s, NOW(), %s, %s)
        """, (email, hashed_password, email.split('@')[0], surname, name)) 
        conn.commit()
        
        verification_token = create_email_verification_token(email)
        
        verification_link = f"http://localhost:8000/verify_email?token={verification_token}"
        
        email_body = templates.get_template("verification.html").render(
            name=name,
            verification_link=verification_link
        )

        send_email(email, "Email Verification", email_body)
        
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        conn.rollback()
        return {"Error_Message": f"An error occurred while registering the user: {str(e)}"}
    finally:
        cursor.close()
        conn.close()
        
@app.get("/register", response_class=HTMLResponse)
async def get_register_page(request: Request):
    """Render the register page."""
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/verify_email")
async def verify_email(request: Request, token: str):
    """Verify the user's email using the token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")
        
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
async def get_login_page(request: Request):
    """Render the login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    """Authenticate the user and update last login time."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Password, user_id, last_logged_in FROM USER WHERE Email = %s", (email,))
        result = cursor.fetchone()
        if result:
            stored_password, user_id, last_logged_in = result
            if verify_password(password, stored_password):
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("UPDATE USER SET last_logged_in = %s WHERE user_id = %s", (current_time, user_id))
                conn.commit()  
                
                access_token = create_access_token(data={"sub": str(user_id)}, expires_delta=timedelta(minutes=30))
                
                response = RedirectResponse(url="/home", status_code=303)
                response.set_cookie("access_token", access_token, httponly=True, secure=True, max_age=1800)
                return response
        return templates.TemplateResponse("login.html", {"request": request, "Error_Message": "Incorrect Email or Password"})
    except Exception as e:
        logger.error(f"Login error: {e}")
        return templates.TemplateResponse("login.html", {"request": request, "Error_Message": "An error occurred"})
    finally:
        cursor.close()
        conn.close()

@app.get("/home", response_class=HTMLResponse)
async def home(request: Request, user_id: int = Depends(get_current_user)):
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT username
    FROM USER WHERE user_id = %s""", (user_id,))
    result = cursor.fetchone()
    username = result[0] if result else "Guest"

    cursor.close()
    conn.close()
    
    return templates.TemplateResponse("home.html", {"request": request, "username":username})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user_id: int = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT username
    FROM USER WHERE user_id = %s""", (user_id,))
    result = cursor.fetchone()
    username = result[0] if result else "Guest"

    cursor.close()
    conn.close()
    
    return templates.TemplateResponse("dashboard.html", {"request": request, "username": username})

@app.post("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, currency2: str = Form(...), user_id: int = Depends(get_current_user)):
    currency1 = "USD" 
    start_date = "2014-11-07" 
    end_date = datetime.today()
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT username
    FROM USER WHERE user_id = %s""", (user_id,))
    result = cursor.fetchone()
    username = result[0] if result else "Guest"

    cursor.close()
    conn.close()
    
    forex_data = fetch_forex_data(currency1, currency2, start_date, end_date.strftime('%Y-%m-%d'))

    graph_data = plot_forex_data(forex_data, currency1, currency2)

    if graph_data is None:
        error_message = "No data available for the selected currencies and date range."
        return templates.TemplateResponse(
            "dashboard.html", 
            {"request": request, "error_message": error_message, "username": username}
        )

    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "graph_data": graph_data, 
            "currency1": currency1, 
            "currency2": currency2, 
            "username": username
        }
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
    currency_pairs = ["USD/EUR", "USD/GBP", "USD/JPY", "USD/AUD", "USD/CAD", "USD/CHF", "USD/NZD"]

    for pair in currency_pairs:
        params = {
            "function": "FX_DAILY",
            "from_symbol": pair.split('/')[0],
            "to_symbol": pair.split('/')[1],
            "apikey": ALPHA_VANTAGE_API_KEY,
            "outputsize": "full",  
            "datatype": "json"
        }
        
        response = requests.get(ALPHA_VANTAGE_URL, params=params)
        
        if response.status_code == 200:
            forex_data = response.json()
            if "Time Series FX (Daily)" in forex_data:
                data = forex_data["Time Series FX (Daily)"]

                conn = get_db_connection()
                cursor = conn.cursor()
                try:
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

    return HTMLResponse(content="Database successfully filled with forex data!")

def save_articles_to_db(articles):
    conn = get_db_connection()
    cursor = conn.cursor()

    for article in articles:
        title = article['title']
        description = article['description']
        content = article['content']
        url = article['url']
        urlToImage = article['urlToImage']
        
        published_at_str = article['publishedAt']
        published_at = datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ")
        
        try:
            cursor.execute("""
                INSERT INTO news_articles (title, description, content, url, published_at, url_to_image)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (title, description, content, url, published_at, urlToImage))  
            conn.commit()
        except Exception as e:
            logger.error(f"Error saving article: {e}")
            conn.rollback()
    cursor.close()
    conn.close()


@app.get("/fetch_news", response_class=HTMLResponse)
async def fetch_news(request: Request):
    url = f"https://newsapi.org/v2/everything?q=AUD&apiKey={NEWS_API_KEY}"
    logging.error(url)
    response = requests.get(url)
    news = response.json()
    if news['status'] == 'ok':
        articles = news['articles']
        save_articles_to_db(articles)
    # return templates.TemplateResponse("news.html", {"request": request, "articles": articles, "currency": "USD"})

@app.get("/news", response_class=HTMLResponse)
async def news(request: Request, currency: str = "USD", user_id: int = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT username
    FROM USER WHERE user_id = %s""", (user_id,))
    result = cursor.fetchone()
    username = result[0] if result else "Guest"

    cursor.close()
    conn.close()

    news_articles = fetch_news_for_currency(currency)

    return templates.TemplateResponse("news.html", {
        "request": request,
        "currency": currency,
        "news_articles": news_articles,
        "username": username
    })

@app.get("/notifications", response_class=HTMLResponse)
async def notifications(request: Request, user_id: int = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  
    
    try:
        cursor.callproc('GetUserNotifications', (user_id,))
        
        cursor.execute("SELECT n.notification_id, n.threshold, n.date_created, s.stock_name, s.close_price AS latest_price "
                       "FROM NOTIFICATIONS n "
                       "JOIN STOCK s ON n.stock_id = s.stock_id "
                       "WHERE n.user_id = %s ORDER BY n.date_created DESC", (user_id,))
        
        notifications = cursor.fetchall()
        
        cursor.close()
        conn.close()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT username
        FROM USER WHERE user_id = %s""", (user_id,))
        result = cursor.fetchone()
        username = result[0] if result else "Guest"
        
        return templates.TemplateResponse("notifications.html", {
            "request": request, 
            "notifications": notifications,
            "user_id": user_id,
            'username': username
        })
    
    except mysql.connector.Error as e:
        logging.error(f"MySQL error: {e}")
        return templates.TemplateResponse("notifications.html", {
            "request": request, "Error_Message": "Database error while fetching notifications."
        })
    
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return templates.TemplateResponse("notifications.html", {
            "request": request, "Error_Message": "An unexpected error occurred."
        })
    
    finally:
        cursor.close()
        conn.close()


@app.post("/notifications", response_class=HTMLResponse)
async def notifications_post(request: Request, 
                              threshold: float = Form(...), 
                              currency: str = Form(...), 
                              user_id: int = Depends(get_current_user)):
    """Save a new notification in the database."""
    logging.info(f"Received data: threshold={threshold}, currency={currency}, user_id={user_id}")
    currency_in=f'USD/{currency}'
    
    if threshold <= 0:
        return templates.TemplateResponse("notifications.html", {
            "request": request, "Error_Message": "Threshold must be positive"
        })
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.callproc('InsertNotification', (threshold, user_id, currency_in))
        conn.commit()
        logging.info(f"Notification saved for user {user_id}, threshold {threshold}, currency {currency_in}.")
        return RedirectResponse(url="/notifications", status_code=303)
    
    except mysql.connector.Error as e:
        logging.error(f"MySQL error: {e}")
        conn.rollback()
        return templates.TemplateResponse("notifications.html", {
            "request": request, "Error_Message": "Database error while saving the notification."
        })
    
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        conn.rollback()
        return templates.TemplateResponse("notifications.html", {
            "request": request, "Error_Message": "An unexpected error occurred."
        })
    
    finally:
        cursor.close()
        conn.close()

@app.post("/notifications/{notification_id}/delete", response_class=RedirectResponse)
async def delete_notification(request: Request, notification_id: int, user_id: int = Depends(get_current_user)):
    """Delete a notification from the database."""
    logging.info(f"Attempting to delete notification ID {notification_id} for user {user_id}")
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Call the stored procedure to delete the notification
        cursor.callproc('DeleteNotification', (notification_id,))
        conn.commit()

        logging.info(f"Notification ID {notification_id} deleted successfully for user {user_id}.")
        return RedirectResponse(url="/notifications", status_code=303)

    except mysql.connector.Error as e:
        logging.error(f"MySQL error: {e}")
        conn.rollback()
        return templates.TemplateResponse("notifications.html", {
            "request": request, "Error_Message": "Database error while deleting the notification."
        })

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        conn.rollback()
        return templates.TemplateResponse("notifications.html", {
            "request": request, "Error_Message": "An unexpected error occurred."
        })

    finally:
        cursor.close()
        conn.close()
@app.post("/notifications/{notification_id}/delete", response_class=RedirectResponse)
async def delete_notification(request: Request, notification_id: int, user_id: int = Depends(get_current_user)):
    """Delete a notification from the database."""
    logging.info(f"Attempting to delete notification ID {notification_id} for user {user_id}")
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Call the stored procedure to delete the notification
        cursor.callproc('DeleteNotification', (notification_id,))
        conn.commit()

        logging.info(f"Notification ID {notification_id} deleted successfully for user {user_id}.")
        return RedirectResponse(url="/notifications", status_code=303)

    except mysql.connector.Error as e:
        logging.error(f"MySQL error: {e}")
        conn.rollback()
        return templates.TemplateResponse("notifications.html", {
            "request": request, "Error_Message": "Database error while deleting the notification."
        })

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        conn.rollback()
        return templates.TemplateResponse("notifications.html", {
            "request": request, "Error_Message": "An unexpected error occurred."
        })

    finally:
        cursor.close()
        conn.close()
        
@app.get("/trends", response_class=HTMLResponse)
async def trends(request: Request, user_id: int = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT username
    FROM USER WHERE user_id = %s""", (user_id,))
    result = cursor.fetchone()
    username = result[0] if result else "Guest"

    cursor.close()
    conn.close()
    
    return templates.TemplateResponse("trends.html", {"request": request, "username": username})

@app.post("/trends", response_class=HTMLResponse)
async def handle_trends_form(request: Request):
    """Handle POST request from trends page."""
    form_data = await request.form()
    action = form_data.get("action")  # Action to determine what button was clicked

    if action == "Get Stock Prediction":
        stock_name = form_data.get("currency_pair")
        return await get_stock_prediction(stock_name)
    elif action == "Get Stock Change":
        start_date = form_data.get("start_date")
        end_date = form_data.get("end_date")
        return await get_stock_change(start_date, end_date)
    elif action == "Get Most Popular Stock":
        return await get_most_popular_stock()

    return {"message": "Action not recognized"}

async def get_stock_prediction(stock_name: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.callproc("GetStockPredictionByName", [stock_name])
        result = cursor.fetchone()

        if result:
            return {"prediction": result["prediction"]}
        else:
            raise HTTPException(status_code=404, detail="Prediction not found")
    
    except Exception as e:
        logging.error(f"Error in stock prediction: {e}")
        raise HTTPException(status_code=500, detail="Error fetching stock prediction")
    
    finally:
        cursor.close()
        conn.close()

async def get_stock_change(start_date: str, end_date: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.callproc("CalculateStockPercentageChange", [start_date, end_date])
        result = cursor.fetchall()

        if result:
            return {"stock_changes": result}
        else:
            raise HTTPException(status_code=404, detail="No data found for the given date range")

    except Exception as e:
        logging.error(f"Error fetching stock change: {e}")
        raise HTTPException(status_code=500, detail="Error fetching stock change")

    finally:
        cursor.close()
        conn.close()

async def get_most_popular_stock():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.callproc("FindMostPopularStock")
        result = cursor.fetchall()

        if result:
            return {"most_popular_stocks": result}
        else:
            raise HTTPException(status_code=404, detail="No popular stocks found")

    except Exception as e:
        logging.error(f"Error fetching most popular stock: {e}")
        raise HTTPException(status_code=500, detail="Error fetching popular stocks")

    finally:
        cursor.close()
        conn.close()

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, user_id: int = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT user_id, username, email, password, lvl, last_logged_in, status, registration_date
            FROM USER WHERE user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        
        if user:
            user_data = {
                "user_id": user[0],
                "username": user[1],
                "email": user[2],
                "password": user[3],
                "lvl": user[4],
                "last_logged_in": user[5],
                "status": user[6],
                "registration_date": user[7]
            }
            logging.error(user_data)
            return templates.TemplateResponse("profile.html", {"request": request, "user": user_data})
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error fetching user data: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        cursor.close()
        conn.close()
        
@app.post("/profile", response_class=HTMLResponse)
async def change_password(request: Request, 
                           current_password: str = Form(...), 
                           new_password: str = Form(...), 
                           confirm_password: str = Form(...), 
                           user_id: int = Depends(get_current_user)):
    """Change the user's password."""
    
    if new_password != confirm_password:
        return templates.TemplateResponse("profile.html", {"request": request, "Error_Message": "New passwords do not match."})

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT password FROM USER WHERE user_id = %s
        """, (user_id,))
        result = cursor.fetchone()

        if result:
            stored_password = result[0]
            if verify_password(current_password, stored_password):
                hashed_new_password = hash_password(new_password)

                cursor.execute("""
                    UPDATE USER SET password = %s WHERE user_id = %s
                """, (hashed_new_password, user_id))
                conn.commit()

                return templates.TemplateResponse("profile.html", {"request": request, "Success_Message": "Password changed successfully."})
            else:
                return templates.TemplateResponse("profile.html", {"request": request, "Error_Message": "Current password is incorrect."})
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return templates.TemplateResponse("profile.html", {"request": request, "Error_Message": "An error occurred while changing the password."})
    finally:
        cursor.close()
        conn.close()

@app.get("/converter", response_class=HTMLResponse)
async def converter(request: Request, user_id: int = Depends(get_current_user)):
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT username
    FROM USER WHERE user_id = %s""", (user_id,))
    result = cursor.fetchone()
    username = result[0]

    cursor.close()
    conn.close()
    
    return templates.TemplateResponse("converter.html", {"request": request, "username":username})