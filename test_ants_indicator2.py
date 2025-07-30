import pandas as pd
import numpy as np
import yfinance as yf

# Ants Indicator - Momentum, Price, and Volume Analysis
def ants_indicator(df, period=15, price_threshold=1.20, volume_threshold=1.20):
    # Parameters
    period = period
    price_threshold = price_threshold
    volume_threshold = volume_threshold

    # Conditions
    chg_up = df['Close'] > df['Close'].shift(1)
    cond1 = chg_up.rolling(window=period).sum() >= 12
    cond2 = df['Close'].rolling(window=period).mean() > price_threshold * df['Close'].rolling(window=50).mean()
    cond3 = df['Volume'].rolling(window=period).mean() > volume_threshold * df['Volume'].rolling(window=50).mean()

    # Initialize counters
    count1 = pd.Series(0, index=df.index, dtype=int)
    count2 = pd.Series(0, index=df.index, dtype=int)
    count3 = pd.Series(0, index=df.index, dtype=int)
    count4 = pd.Series(0, index=df.index, dtype=int)

    # Iterate through bars to calculate conditions
    for i in range(period - 1, len(df)):
        if cond1.iloc[i].item():  # Use .item() to get scalar boolean
            count1.iloc[max(0, i - period + 1):i + 1] = 1
        if cond2.iloc[i].item():  # Use .item() for cond2
            count2.iloc[i] += 2
        if cond3.iloc[i].item():  # Use .item() for cond3
            count3.iloc[i] += 3
        count4.iloc[i] = count1.iloc[i] + count2.iloc[i] + count3.iloc[i]

    # Exploration DataFrame
    exploration = pd.DataFrame({
        'Momentum': count1,
        'Price': count2,
        'Volume': count3,
        'Ants Score': count4
    }, index=df.index)

    return exploration

# Fetch GOOG stock data using yfinance
ticker = 'GOOG'
start_date = '2024-01-01'
end_date = '2025-07-26'
df = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False)
df.name = ticker  # Set DataFrame name

# Select required columns and handle multi-level columns if present
if isinstance(df.columns, pd.MultiIndex):
    df = df.xs(ticker, axis=1, level=1) if ticker in df.columns.levels[1] else df
else:
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

# Ensure simple DatetimeIndex
if not isinstance(df.index, pd.DatetimeIndex):
    df.index = pd.to_datetime(df.index)

# Handle missing data
df = df[['Close', 'Volume', 'High']].dropna()

# Run Ants Indicator
ants_result = ants_indicator(df)
print(ants_result)