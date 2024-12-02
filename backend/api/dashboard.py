import requests
import plotly.graph_objects as go
import logging
from datetime import datetime, timedelta

# Set up logging (for debugging purposes)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_forex_data(currency1, currency2, start_date, end_date):
    """
    Fetch historical forex data from Alpha Vantage API.
    """
    api_key = 'YOUR_API_KEY'  # Replace with your new API key
    url = f"https://www.alphavantage.co/query"
    
    params = {
        "function": "FX_DAILY",
        "from_symbol": currency1,
        "to_symbol": currency2,
        "apikey": api_key,
        "outputsize": "full"  # Get full data for longer date ranges
    }

    response = requests.get(url, params=params)
    logger.info(f"API Response: {response.text}")  # Log the full response for debugging

    if response.status_code == 200:
        data = response.json()
        if "Time Series FX (Daily)" not in data:
            error_message = data.get('Error Message', 'Unknown error')
            raise Exception(f"Error fetching forex data: {error_message}")
        
        rates = data["Time Series FX (Daily)"]
        return {date: {'exchangeRate': float(info['4. close'])} for date, info in rates.items()}
    else:
        raise Exception(f"Error fetching data: {response.status_code} - {response.text}")


def create_forex_graph(base_currency: str, target_currency: str, forex_data):
    """
    Create an interactive graph for forex data over time.

    Args:
        base_currency (str): The base currency (e.g., "USD").
        target_currency (str): The target currency (e.g., "EUR").
        forex_data (dict): Historical forex rates.

    Returns:
        str: JSON data for the Plotly graph.
    """
    dates = []
    exchange_rates = []

    # Collect dates and exchange rates
    for date, rate_data in forex_data.items():
        dates.append(date)
        exchange_rates.append(rate_data['exchangeRate'])

    # Create a Plotly graph with the historical data
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=exchange_rates,
        mode="lines+markers",  # Show a line connecting the dots
        name=f"{base_currency}/{target_currency}",
        text=[f"{base_currency}/{target_currency}: {rate:.2f}" for rate in exchange_rates],
        textposition="top center",  # Position the text above the marker
        marker=dict(size=6, color='blue')  # Customize the marker appearance
    ))

    # Update layout with titles and axis labels
    fig.update_layout(
        title=f"Exchange Rate: {base_currency} to {target_currency}",
        xaxis_title="Date",
        yaxis_title="Exchange Rate",
        hovermode="closest",
        showlegend=False  # Remove legend since we only have one data point
    )
    
    # Return the JSON for the Plotly graph
    return fig.to_json()
