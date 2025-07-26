import requests
import pandas as pd
import time
from config import API_CONFIG, ALPHA_VANTAGE_API_KEY_PREMIUM, FINNHUB_API_KEY

# Rate limiting decorator
def rate_limited(max_per_minute):
    min_interval = 60.0 / max_per_minute
    
    def decorate(func):
        last_time_called = [0.0]
        
        def rate_limited_function(*args, **kwargs):
            elapsed = time.time() - last_time_called[0]
            wait = min_interval - elapsed
            if wait > 0:
                time.sleep(wait)
            last_time_called[0] = time.time()
            return func(*args, **kwargs)
        return rate_limited_function
    return decorate

@rate_limited(API_CONFIG["alpha_vantage"]["rate_limit"])
def get_alpha_vantage_data(ticker, function="TIME_SERIES_DAILY", **params):
    """Generic Alpha Vantage API fetcher with error handling"""
    base_params = {
        "function": function,
        "symbol": ticker,
        "datatype": "json",
        "outputsize": "compact",
        "apikey": ALPHA_VANTAGE_API_KEY_PREMIUM
    }
    base_params.update(params)
    
    try:
        response = requests.get(API_CONFIG["alpha_vantage"]["base_url"], params=base_params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {function} for {ticker}: {str(e)}")
        return None

def get_ohlcv_data(ticker, source="alpha_vantage"):
    """Fetch OHLCV data with improved error handling"""
    try:
        if source == "alpha_vantage":
            data = get_alpha_vantage_data(ticker)
            if not data:
                return None
                
            time_series = data.get("Time Series (Daily)", {})
            if not time_series:
                print(f"No time series data found for {ticker}")
                return None
                
            latest_date = next(iter(time_series))
            ohlc_data = time_series[latest_date]
            
            return {
                "Open": float(ohlc_data["1. open"]),
                "High": float(ohlc_data["2. high"]),
                "Low": float(ohlc_data["3. low"]),
                "Close": float(ohlc_data["4. close"]),
                "Volume": int(ohlc_data["5. volume"])
            }
            
    except Exception as e:
        print(f"Error fetching OHLCV data for {ticker}: {str(e)}")
        return None

def calculate_52weekhigh(ticker):
    """Calculate 52-week high percentage with caching"""
    try:
        # Get weekly data with full output size to ensure we have enough data points
        weekly_data = get_alpha_vantage_data(ticker, function="TIME_SERIES_WEEKLY", outputsize="full")
        if not weekly_data:
            return None
            
        weekly_series = weekly_data.get("Weekly Time Series", {})
        if not weekly_series:
            return None
            
        # Convert to sorted list of (date, values) tuples
        sorted_weekly = sorted(
            [(date, float(values["2. high"])) for date, values in weekly_series.items()],
            key=lambda x: x[0],
            reverse=True
        )
        
        # Ensure we have at least 52 weeks of data
        if len(sorted_weekly) < 52:
            return None
            
        # Get the highest high from last 52 weeks
        fifty_two_week_high = max([high for date, high in sorted_weekly[:52]])
        
        # Get current close from daily data
        daily_data = get_alpha_vantage_data(ticker)
        if not daily_data:
            return None
            
        time_series = daily_data.get("Time Series (Daily)", {})
        if not time_series:
            return None
            
        latest_date = next(iter(time_series))
        current_close = float(time_series[latest_date]["4. close"])
        
        # Calculate percentage difference
        return ((current_close - fifty_two_week_high) / fifty_two_week_high) * 100
        
    except Exception as e:
        print(f"Error calculating 52-week high for {ticker}: {str(e)}")
        return None

def get_technical_indicators(ticker, source="alpha_vantage"):
    """Fetch all technical indicators with exact quarterly and indicator calculations"""
    indicators = {}
    
    try:
        if source != "alpha_vantage":
            raise ValueError("Only alpha_vantage source is currently supported")
        
        # 1. Get daily OHLCV data for historical closes
        daily_data = get_alpha_vantage_data(ticker)
        if not daily_data:
            raise ValueError("No daily price data available")
            
        time_series = daily_data.get("Time Series (Daily)", {})
        if not time_series:
            raise ValueError("Empty time series data")
        
        # Convert to sorted list of (date, values) pairs
        sorted_daily = sorted(time_series.items(), key=lambda x: x[0], reverse=True)
        
        # 2. Add historical close prices (up to 24 days back)
        close_lookbacks = {f"Close-{i}": None for i in range(25)}
        close_lookbacks.pop("Close-0")  # We already have current close
        
        for i in range(1, 25):
            if i < len(sorted_daily):
                close_lookbacks[f"Close-{i}"] = float(sorted_daily[i][1]["4. close"])
        
        indicators.update(close_lookbacks)
        
        # Get 52-week high
        indicators["52weekhigh"] = calculate_52weekhigh(ticker)
        
        # MACD Calculations
        macd_data = {}
        for timeframe in ["daily", "weekly", "monthly"]:
            data = get_alpha_vantage_data(
                ticker,
                function="MACD",
                interval=timeframe,
                series_type="close",
                fastperiod=12,
                slowperiod=26,
                signalperiod=9,
                fastmatype=1,  # SMA
                slowmatype=1,  # SMA
                signalmatype=1  # SMA
            )
            
            if not data:
                continue
                
            # The response key varies slightly by timeframe
            tech_key = f"Technical Analysis: MACDEXT"
            tech_data = data.get(tech_key, {})
            if not tech_data:
                continue
                
            # Store all monthly data points for quarterly calculation
            if timeframe == "monthly":
                monthly_points = []
                for date, values in list(tech_data.items())[:3]:  # Last 3 months
                    try:
                        monthly_points.append({
                            "macd": float(values["MACD"]),
                            "signal": float(values["MACD_Signal"])
                        })
                    except (KeyError, ValueError):
                        continue
                
                if monthly_points:
                    macd_data["monthly_points"] = monthly_points
            
            # Get the latest data point
            if not tech_data:
                continue
                
            latest_date = next(iter(tech_data))
            prefix = timeframe.capitalize()
            
            try:
                macd_value = float(tech_data[latest_date]["MACD"])
                signal_value = float(tech_data[latest_date]["MACD_Signal"])
                
                indicators.update({
                    f"macd{prefix}": macd_value,
                    f"macdSignal{prefix}": signal_value,
                    f"macdIndicator{prefix}": 1 if macd_value > signal_value else 0
                })
            except (KeyError, ValueError):
                continue
        
        # Calculate quarterly from last 3 months
        if "monthly_points" in macd_data and len(macd_data["monthly_points"]) >= 3:
            last_3_months = macd_data["monthly_points"][:3]
            quarterly_macd = sum(p["macd"] for p in last_3_months) / 3
            quarterly_signal = sum(p["signal"] for p in last_3_months) / 3
            
            indicators.update({
                "macdQuarterly": quarterly_macd,
                "macdSignalQuarterly": quarterly_signal,
                "macdIndicatorQuarterly": 1 if quarterly_macd > quarterly_signal else 0
            })
        
        # Calculate totals using only strict 1/0 indicators
        macd_indicators = [
            indicators.get("macdIndicatorDaily"),
            indicators.get("macdIndicatorWeekly"),
            indicators.get("macdIndicatorMonthly"),
            indicators.get("macdIndicatorQuarterly")
        ]
        
        # Count only valid indicators (not None)
        valid_indicators = [i for i in macd_indicators if i is not None]
        indicators["macdCount"] = sum(1 for i in valid_indicators if i == 1)
        indicators["macdTotal"] = len(valid_indicators)
        
        return indicators
        
    except Exception as e:
        print(f"Error in get_technical_indicators for {ticker}: {str(e)}")
        return indicators  # Return whatever we have so far