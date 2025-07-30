import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
    df = df.sort_index()
    return df[['close', 'volume']]

def calculate_ants_indicator(df, window=15):
    df = df.copy()
    
    # Momentum: Count days where close > previous close
    df['up'] = (df['close'] > df['close'].shift(1)).astype(int)
    df['momentum'] = df['up'].rolling(window=window).sum()
    
    # Volume: Compare current 15-day avg volume vs previous 15-day avg volume
    df['vol_sma'] = df['volume'].rolling(window=window).mean()
    df['prev_vol_sma'] = df['vol_sma'].shift(window)
    df['volume_met'] = df['vol_sma'] >= 1.20 * df['prev_vol_sma']
    
    # Price: 20% increase over 15 days
    df['price_met'] = (df['close'] / df['close'].shift(window)) >= 1.20
    
    # Determine Ant colors
    conditions = [
        (df['momentum'] >= 12) & df['volume_met'] & df['price_met'],  # Green
        (df['momentum'] >= 12) & df['price_met'],                      # Blue
        (df['momentum'] >= 12) & df['volume_met'],                     # Yellow
        (df['momentum'] >= 12)                                         # Gray
    ]
    colors = ['green', 'blue', 'yellow', 'gray']
    df['ant_color'] = np.select(conditions, colors, default=None)
    df['ant_size'] = np.where(df['ant_color'].notnull(), 10, 0)
    
    return df

def plot_interactive_ants_indicator(df):
    # Create subplots with shared x-axis
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.05,
                       row_heights=[0.7, 0.3])
    
    # Price and Ants plot
    fig.add_trace(go.Scatter(
        x=df.index, y=df['close'], 
        mode='lines', name='Price',
        line=dict(color='black', width=2)
    ), row=1, col=1)
    
    # Add colored ants using scatter plots
    color_map = {'green': 'Green Ants', 'blue': 'Blue Ants', 
                 'yellow': 'Yellow Ants', 'gray': 'Gray Ants'}
    
    for color in color_map:
        color_df = df[df['ant_color'] == color]
        fig.add_trace(go.Scatter(
            x=color_df.index, y=color_df['close'] * 1.01,
            mode='markers', name=color_map[color],
            marker=dict(
                color=color,
                size=10,
                line=dict(width=1, color='black')
            ),
            hovertemplate='Date: %{x}<br>Price: %{y:.2f}<br>Type: ' + color_map[color]
        ), row=1, col=1)
    
    # Volume plot
    fig.add_trace(go.Bar(
        x=df.index, y=df['volume'],
        name='Volume',
        marker=dict(color='blue', opacity=0.5)
    ), row=2, col=1)
    
    # Update layout
    fig.update_layout(
        title='Ants Indicator - Interactive Analysis',
        hovermode='x unified',
        height=800,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    # Add custom hover information
    fig.update_traces(
        selector=dict(type='scatter', mode='markers'),
        hovertemplate="Date: %{x}<br>Price: %{y:.2f}<br>Type: %{fullData.name}"
    )
    
    fig.show()

# Configuration
API_KEY = 'JQUQY9GIBCW31BTR'  # Replace with your API key
SYMBOL = 'BTCUSD'  # Example stock symbol

# Fetch and process data
df = fetch_stock_data(API_KEY, SYMBOL)
if df is not None:
    ants_df = calculate_ants_indicator(df)
    plot_interactive_ants_indicator(ants_df)
    
    # Show recent ants in a table
    recent_ants = ants_df[ants_df['ant_color'].notnull()].tail(20)
    if not recent_ants.empty:
        print("\nRecent Ants Detected:")
        print(recent_ants[['close', 'ant_color']])
    else:
        print("\nNo Ants detected in recent data")