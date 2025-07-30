import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from datetime import datetime

def fetch_stock_data(api_key, symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={api_key}&outputsize=full"
    response = requests.get(url)
    data = response.json()
    
    if 'Time Series (Daily)' not in data:
        print("Error fetching data:", data.get('Note', data))
        return None
    
    df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index', dtype=float)
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns={
        '1. open': 'open',
        '2. high': 'high',
        '3. low': 'low',
        '4. close': 'close',
        '5. adjusted close': 'adj_close',
        '6. volume': 'volume'
    })
    df = df.sort_index()  # Sort ascending by date
    return df[['close', 'volume']]

def calculate_ants_indicator(df, window=15):
    df = df.copy()
    
    # Momentum: Count days where close > previous close
    df['up'] = (df['close'] > df['close'].shift(1)).astype(int)
    df['momentum'] = df['up'].rolling(window=window).sum()
    
    # Volume: Compare current 15-day avg volume vs previous 15-day avg volume
    df['vol_sma'] = df['volume'].rolling(window=window).mean()
    df['prev_vol_sma'] = df['vol_sma'].shift(window)
    df['volume_cond'] = df['vol_sma'] >= 1.2 * df['prev_vol_sma']
    
    # Price: 20% increase over 15 days
    df['price_cond'] = (df['close'] / df['close'].shift(window)) >= 1.20
    
    # Determine Ant colors
    conditions = [
        (df['momentum'] >= 12) & df['volume_cond'] & df['price_cond'],  # Green
        (df['momentum'] >= 12) & df['price_cond'],                      # Blue
        (df['momentum'] >= 12) & df['volume_cond'],                     # Yellow
        (df['momentum'] >= 12)                                          # Gray
    ]
    colors = ['green', 'blue', 'yellow', 'gray']
    df['ant_color'] = np.select(conditions, colors, default=None)
    
    # Filter relevant columns and drop NaN rows (due to window calculations)
    result = df[['close', 'ant_color']].copy()
    result = result[result['ant_color'].notnull()]
    return result

def plot_ants_indicator(price_data, ants_data):
    plt.figure(figsize=(14, 7))
    
    # Plot price
    plt.plot(price_data.index, price_data['close'], label='Price', color='black')
    
    # Plot ants
    for date, row in ants_data.iterrows():
        color = row['ant_color']
        plt.scatter(date, price_data.loc[date, 'close'] * 1.01, 
                    color=color, edgecolor='black', s=100, 
                    label=f'{color.capitalize()} Ant' if date == ants_data.index[0] else "")
    
    plt.title('Ants Indicator')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    plt.show()

# Configuration
API_KEY = 'JQUQY9GIBCW31BTR'  # Replace with your API key
SYMBOL = 'IBM'  # Example stock symbol

# Fetch and process data
df = fetch_stock_data(API_KEY, SYMBOL)
if df is not None:
    ants_data = calculate_ants_indicator(df)
    plot_ants_indicator(df, ants_data)
    print(ants_data[['ant_color']].tail(20))  # Show recent ants