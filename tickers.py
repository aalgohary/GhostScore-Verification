# Supported tickers categorized by market
TICKERS = {
    "Technology": [
        "AAPL", "MSFT", "GOOG", "GOOGL", "AMZN", "META", "NVDA", 
        "TSLA", "ADBE", "INTC", "CSCO", "CRM", "AMD", "QCOM"
    ],
    "Finance": [
        "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", 
        "SCHW", "AXP", "PYPL", "V", "MA"
    ],
    "Healthcare": [
        "JNJ", "PFE", "UNH", "MRK", "ABT", "TMO", "AMGN", 
        "GILD", "BMY", "CVS", "LLY", "DHR"
    ],
    "Consumer": [
        "WMT", "PG", "KO", "PEP", "COST", "MCD", "NKE", 
        "TGT", "HD", "LOW", "DIS", "SBUX"
    ],
    "Industrial": [
        "BA", "CAT", "HON", "GE", "MMM", "UNP", "UPS", 
        "FDX", "DE", "RTX", "LMT", "GD"
    ]
}

# All tickers combined
ALL_TICKERS = [
    ticker for sector in TICKERS.values() for ticker in sector
]