import os
import logging
import mysql.connector
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.mount("/static", StaticFiles(directory="/app/frontend/static"), name="static")

app.mount("/pictures", StaticFiles(directory="/app/frontend/pictures"), name="pictures")


templates = Jinja2Templates(directory="/app/frontend/templates")

DB_HOST = os.getenv("DB_HOST", "mariadb")
DB_PORT = os.getenv("DB_PORT", 3306)
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rootpassword")
DB_NAME = os.getenv("DB_NAME", "mydatabase")

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        collation='utf8mb4_general_ci'
    )

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the index page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    """Render the registration page."""
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_user(request: Request, name: str = Form(...), surname: str = Form(...), 
                         email: str = Form(...), password: str = Form(...)):
    """Register a new user with the given email, username, first name, and last name."""
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO USER (Email, Password, Username) VALUES (%s, %s, %s)", 
            (email, password, name)
        )
        conn.commit()
        logger.info(f"User {name} with email {name} registered successfully.")
        return HTMLResponse(content=f"User {name} with email {name} registered successfully.", status_code=200)

    except Exception as e:
        conn.rollback()
        logger.error(f"Error registering user: {e}")
        return templates.TemplateResponse("register.html", {"request": request, "Error_Message": 'Email Already Exists'})

    finally:
        cursor.close()
        conn.close()

@app.get("/login", response_class=HTMLResponse)
async def register(request: Request):
    """Render the login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    """Check if the user exists and validate the password."""
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT Password FROM USER WHERE Email = %s", (email,))
        result = cursor.fetchone()

        if result:
            stored_password = result[0]
            
            if stored_password == password:
                logger.info(f"User with email {email} logged in successfully.")
                return HTMLResponse(content=f"User {email} logged in successfully.", status_code=200)
            else:
                return templates.TemplateResponse("login.html", {"request": request, "Error_Message": "Incorrect Email or Password"})
        else:
            return templates.TemplateResponse("login.html", {"request": request, "Error_Message": "Incorrect Email or Password"})

    except Exception as e:
        logger.error(f"Error during login: {e}")
        return templates.TemplateResponse("login.html", {"request": request, "Error_Message": "An error occurred during login"})

    finally:
        cursor.close()
        conn.close()
<<<<<<< Updated upstream
=======
from datetime import datetime, timedelta


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/dashboard", response_class=HTMLResponse)
async def dashboard_post(request: Request, currency1: str = Form(...), currency2: str = Form(...)):
    """Generate and display the forex dashboard."""
    try:
        # Calculate the start date (30 days ago) and end date (current date)
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Fetch forex data with dynamic start_date (30 days ago) and end_date (current date)
        forex_data = fetch_forex_data(currency1, currency2, start_date, end_date)
        
        # Create the forex graph with the same date range
        graph_data = create_forex_graph(currency1, currency2, forex_data)
        
        return templates.TemplateResponse(
            "dashboard.html", {
                "request": request,
                "currency1": currency1,
                "currency2": currency2,
                "graph_data": graph_data,
            }
        )
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        return templates.TemplateResponse(
            "dashboard.html", {"request": request, "error_message": "Error fetching forex data."}
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
    # Add password reset logic
    return templates.TemplateResponse("password_changed.html", {"request": request})


@app.get("/profile", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the dashboard page."""
    return templates.TemplateResponse("profile.html", {"request": request})
    
@app.get("/notifications", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the dashboard page."""
    return templates.TemplateResponse("notifications.html", {"request": request})
>>>>>>> Stashed changes
