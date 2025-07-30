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

def calculate_ants_score(df, window=15, price_threshold=1.20, volume_threshold=1.20):
    """
    Calculate Ants indicator numerical score (0-4) based on TradingView logic:
    0: No conditions met
    1: Momentum only (Gray)
    2: Momentum + Price (Blue)
    3: Momentum + Volume (Yellow)
    4: All conditions met (Green)
    """
    df = df.copy()
    
    # Momentum: Up in ≥12 of last 15 days
    df['up'] = (df['close'] > df['close'].shift(1)).astype(int)
    df['momentum'] = df['up'].rolling(window=window).sum()
    
    # Volume: 15-day avg volume vs. prior 15-day avg (20% increase)
    df['vol_sma'] = df['volume'].rolling(window=window).mean()
    df['prev_vol_sma'] = df['vol_sma'].shift(window)  # Prior 15-day avg
    df['volume_met'] = df['vol_sma'] >= volume_threshold * df['prev_vol_sma']
    
    # Price: 20% increase over 15 days
    df['price_met'] = (df['close'] / df['close'].shift(window)) >= price_threshold
    
    # Numerical Score (0-4)
    conditions = [
        (df['momentum'] >= 12) & df['volume_met'] & df['price_met'],  # 4 = Green
        (df['momentum'] >= 12) & df['price_met'],                     # 2 = Blue
        (df['momentum'] >= 12) & df['volume_met'],                    # 3 = Yellow
        (df['momentum'] >= 12)                                        # 1 = Gray
    ]
    scores = [4, 2, 3, 1]  # Order matters: check strictest first!
    df['ants_score'] = np.select(conditions, scores, default=0)
    
    return df['ants_score']

# Fetch data (using your existing function)
df = fetch_stock_data('JQUQY9GIBCW31BTR', "IBM")

# Calculate Ants score
ants_score = calculate_ants_score(df)

# Filter days with Ants (score > 0)
ants_present = ants_score[ants_score > 0]
print(ants_present.tail(15))