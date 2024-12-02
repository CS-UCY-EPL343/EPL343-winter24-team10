import requests
import logging
import mysql.connector
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import plotly.graph_objects as go
import plotly.express as px
import json

# Initialize FastAPI app and templates
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection function using environment variables
def get_db_connection():
    """
    Establish and return a database connection using environment variables.
    """
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", 3306),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        logger.info("Successfully connected to the database.")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Error connecting to database: {err}")
        raise

def fetch_forex_data(currency1, currency2, start_date, end_date):
    """
    Fetch forex data from the STOCK table for a specific currency pair and date range.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Assuming the stock_name contains the currency pair, e.g., "USD/EUR"
        currency_pair = f"{currency1}/{currency2}"

        query = """
        SELECT date, close_price
        FROM STOCK
        WHERE stock_name = %s
        AND date BETWEEN %s AND %s
        ORDER BY date
        """
        cursor.execute(query, (currency_pair, start_date, end_date))
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return data

    except mysql.connector.Error as err:
        logger.error(f"Error fetching forex data: {err}")
        return None


def plot_forex_data(data, currency1, currency2):
    """
    Plot the forex data using Plotly.
    """
    if not data:
        return None

    # Extract the date and exchange_rate (close_price) values
    dates = [item['date'] for item in data]
    exchange_rates = [item['close_price'] for item in data]

    # Create a Plotly line chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=exchange_rates,
        mode='lines+markers',
        name=f'{currency1} to {currency2}',
        line=dict(color='green', width=2),
        marker=dict(size=6, color='red')
    ))

    # Customize the layout
    fig.update_layout(
        title=f"Exchange Rate: {currency1} to {currency2}",
        xaxis_title="Date",
        yaxis_title="Exchange Rate",
        paper_bgcolor="black",
        plot_bgcolor="black",
        font=dict(color="white"),
        hovermode="closest",
        dragmode="zoom"
    )

    # Convert the Plotly figure to JSON for rendering in the template
    return fig.to_json()

 