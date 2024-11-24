import requests
import logging
import os
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

templates = Jinja2Templates(directory="/app/frontend/templates")

MAJOR_CURRENCIES = {
    "USD": "US Dollar",
    "EUR": "Euro",
    "GBP": "British Pound",
    "JPY": "Japanese Yen",
    "AUD": "Australian Dollar",
    "CAD": "Canadian Dollar",
    "CHF": "Swiss Franc",
    "NZD": "New Zealand Dollar",
}

MAJOR_CRYPTOCURRENCIES = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "XRP": "Ripple",
    "LTC": "Litecoin",
    "BCH": "Bitcoin Cash",
    "ADA": "Cardano",
    "DOT": "Polkadot",
}

OPEN_EXCHANGE_API_URL = "https://openexchangerates.org/api"
API_KEY = os.getenv("OPEN_EXCHANGE_API_KEY")


def get_available_currencies():
    """Return a combined list of available currencies and cryptocurrencies."""
    return {**MAJOR_CURRENCIES, **MAJOR_CRYPTOCURRENCIES}


async def fetch_exchange_rate(base_currency: str, target_currency: str):
    """Fetch the exchange rate for the given currency pair from the Open Exchange Rates API."""
    try:
        if not API_KEY:
            raise ValueError("API Key is not set.")

        if base_currency == target_currency:
            return 1.0  # No conversion needed, return 1

        rate_response = requests.get(
            f"{OPEN_EXCHANGE_API_URL}/convert/{base_currency}/{target_currency}?app_id={API_KEY}"
        )
        rate_response.raise_for_status()
        rate_data = rate_response.json()

        return rate_data.get("rate", None)

    except requests.RequestException as e:
        logger.error(f"Error fetching exchange rate: {e}")
        return None


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the index page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """Render the login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    """Render the registration page."""
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the dashboard with available currencies."""
    currencies = get_available_currencies()
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "currencies": currencies}
    )


@app.post("/dashboard", response_class=HTMLResponse)
async def process_selection(
    request: Request,
    currency1: str = Form(...),
    currency2: str = Form(...),
    crypto1: str = Form(...),
    crypto2: str = Form(...),
):
    """Process the currency and crypto selections and fetch the exchange rate."""
    currencies = get_available_currencies()

    currency_rate = await fetch_exchange_rate(currency1, currency2)
    crypto_rate = await fetch_exchange_rate(crypto1, crypto2)  # Adjust as needed

    if currency_rate is None or crypto_rate is None:
        raise HTTPException(status_code=500, detail="Error fetching exchange rates")

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "currencies": currencies,
            "currency1": currency1,
            "currency2": currency2,
            "crypto1": crypto1,
            "crypto2": crypto2,
            "currency_rate": currency_rate,
            "crypto_rate": crypto_rate,
        },
    )
