from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from passlib.context import CryptContext
from api.jwt_auth import create_access_token
from api.dashboard import fetch_forex_data, plot_forex_data
from datetime import timedelta

import os
import logging
import requests
import mysql.connector

load_dotenv()

# Logging configuration
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
OPEN_EXCHANGE_RATES_API_KEY = os.getenv("OPEN_EXCHANGE_RATES_API_KEY")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALPHA_VANTAGE_API_KEY = 'Z9PPR7T1ICWXAP1P'
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

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
    """Register a new user."""
    hashed_password = hash_password(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO USER (Email, Password, Username) VALUES (%s, %s, %s)", (email, hashed_password, name))
        conn.commit()
        logger.info(f"User {name} with email {email} registered successfully.")
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        conn.rollback()
        logger.error(f"Error registering user: {e}")
        return templates.TemplateResponse("register.html", {"request": request, "Error_Message": "Email Already Exists"})
    finally:
        cursor.close()
        conn.close()


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
                access_token = create_access_token(data={"sub": str(user_id)}, expires_delta=timedelta(minutes=30))
                response = RedirectResponse(url="/dashboard", status_code=303)
                response.set_cookie("access_token", access_token, httponly=True, secure=True, max_age=1800)
                return response
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
    start_date = "2020-12-01" 
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
                            values["5. volume"]  # Assuming 'value' is the volume
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
