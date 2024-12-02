from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from passlib.context import CryptContext
from api.jwt_auth import create_access_token
from api.dashboard import fetch_forex_data, plot_forex_data

import os
import logging
import mysql.connector
from datetime import timedelta

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


# @app.post("/fill_database", response_class=HTMLResponse)
# async def fill_database():
    