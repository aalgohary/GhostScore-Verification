import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
ALPHA_VANTAGE_API_KEY_PREMIUM = os.getenv("ALPHA_VANTAGE_API_KEY_PREMIUM")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")

# API endpoints configuration
API_CONFIG = {
    "alpha_vantage": {
        "base_url": "https://www.alphavantage.co/query",
        "key_param": "apikey",
        "rate_limit": 150  # requests per minute
    },
    "finnhub": {
        "base_url": "https://finnhub.io/api/v1",
        "key_param": "token",
        "rate_limit": 60
    }
}

# App configuration
CACHE_EXPIRATION = 3600  # 1 hour in seconds