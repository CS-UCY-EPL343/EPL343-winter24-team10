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
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email_validator import validate_email, EmailNotValidError

import os
import jwt
import smtplib
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


NEWS_API_KEY='09a61846155e40b08a46dba4aa59ef41'

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
        
        # Render the email body using the template
        email_body = templates.env.get_template("verification.html").render(<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Your Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(to right, #6a11cb, #2575fc);
            margin: 0;
            padding: 0;
            line-height: 1.5;
        }
        .email-container {
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        h1 {
            font-size: 28px;
            color: #333;
            margin-bottom: 20px;
            font-weight: bold;
            text-align: center;
            background: -webkit-linear-gradient(45deg, #6a11cb, #2575fc);
            -webkit-background-clip: text;
            color: transparent;
        }
        p {
            font-size: 16px;
            color: #666;
            margin-bottom: 25px;
            text-align: center;
        }
        .button {
            display: inline-block;
            padding: 12px 25px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-size: 18px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: background-color 0.3s ease;
            margin: 0 auto;
            display: block;
        }
        .button:hover {
            background-color: #0056b3;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            font-size: 14px;
            color: #888;
        }
        .footer a {
            color: #007bff;
            text-decoration: none;
        }
        /* Responsive Styles */
        @media (max-width: 600px) {
            .email-container {
                padding: 20px;
            }
            h1 {
                font-size: 24px;
            }
            .button {
                padding: 12px 20px;
                font-size: 16px;
            }
        }
    </style>
</head>
<body>
    <div class="email-container">
        <!-- Email Content -->
        <div class="content">
            <h1>Welcome to Your Dashboard, {{name}}!</h1>
            <p>We're excited to have you onboard. To get started, please verify your email address by clicking the button below.</p>
            <a href="{{verification_link}}" class="button">Verify My Email</a>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>If you did not register for this account, you can ignore this email or <a href="mailto:support@example.com">contact support</a>.</p>
        </div>
    </div>
</body>
</html>

            name=name,
            verification_link=verification_link
        )
        
        # Send the email
        send_email(email, "Email Verification", email_body)
        
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        conn.rollback()
        return {"Error_Message": f"An error occurred while registering the user: {str(e)}"}
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
        try:
            # Prepare data for insertion
            source_id = article['source']['id']
            source_name = article['source']['name']
            author = article.get('author', 'Unknown')  # Handle missing author field
            title = article['title']
            description = article['description']
            url = article['url']
            url_to_image = article.get('urlToImage', None)
            published_at = datetime.strptime(article['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
            content = article.get('content', None)

            # Insert the article into the database or update on duplicate
            cursor.execute("""
                INSERT INTO news_articles (
                    source_id, source_name, author, title, description, url, url_to_image, published_at, content
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    source_name = VALUES(source_name),
                    author = VALUES(author),
                    title = VALUES(title),
                    description = VALUES(description),
                    url_to_image = VALUES(url_to_image),
                    published_at = VALUES(published_at),
                    content = VALUES(content)
            """, (source_id, source_name, author, title, description, url, url_to_image, published_at, content))

            conn.commit()
        except Exception as e:
            print(f"Error inserting article: {e}")
            conn.rollback()

    cursor.close()
    conn.close()



@app.post("/fill_news", response_class=HTMLResponse)
async def fill_news(request: Request):
    """Fetch news articles from the News API and store them in the database."""

    # Define the query parameters for the API request for multiple currencies
    currencies = ["USD", "EUR", "GBP", "JPY", "AED", "AUD"]  # Add all required currencies here

    for currency in currencies:
        url = f"https://newsapi.org/v2/everything?q={currency}&from=2024-11-02&sortBy=publishedAt&language=en&apiKey={NEWS_API_KEY}"

        try:
            # Fetch news articles from the API
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses

            data = response.json()

            if data.get("status") == "ok":
                articles = data["articles"]
                # Save the fetched articles into the database for the current currency
                save_articles_to_db(articles)
                print(f"Saved news for {currency}")
            else:
                print(f"Failed to fetch news for {currency}: {data.get('message')}")
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from News API for {currency}: {e}")

    return templates.TemplateResponse("dashboard.html", {"request": request, "message": "Database filled with news articles for all currencies."})


@app.get("/news", response_class=HTMLResponse)
async def news(request: Request, currency: str = "USD"):
    """Fetch and display forex data and related news for a given currency."""

    # Fetch all news and filter by the selected currency
    news_articles = fetch_news_for_currency(currency)

    # Render the dashboard page with the filtered news articles
    return templates.TemplateResponse("news.html", {
        "request": request,
        "currency": currency,
        "news_articles": news_articles  # Pass the filtered news articles to the template
    })

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    """Render the password reset page."""
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/notifications", response_class=HTMLResponse)
async def notifications(request: Request):
    """Render the password reset page."""
    return templates.TemplateResponse("notifications.html", {"request": request})

@app.get("/news", response_class=HTMLResponse)
async def news(request: Request):
    return templates.TemplateResponse("news.html", {"request": request})