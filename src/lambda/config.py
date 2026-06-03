"""Configuration loaded from environment variables."""

import os


class Config:
    TABLE_NAME: str = os.environ.get("TABLE_NAME", "StockDashboard")
    TICKERS_PK: str = "TICKERS"
    TOP_TICKERS_PK: str = "TOP_TICKERS"

    # How many to keep when refreshing the auto-managed top-by-market-cap list
    TOP_N: int = 20

    # Default tickers to show in dropdown
    DEFAULT_TICKERS: list[str] = [
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "NVDA",
        "META",
        "TSLA",
        "BRK-B",
        "V",
        "JNJ",
    ]

    # Candidate pool the weekly refresh scans for top-N by market cap.
    # Curated large-caps across sectors — broad enough that the top 10 is
    # always inside this set even after multi-year reshuffling.
    CANDIDATE_TICKERS: list[str] = [
        # Mega-cap tech
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "NVDA",
        "META",
        "TSLA",
        "AVGO",
        "ORCL",
        "ADBE",
        "CRM",
        "NFLX",
        "AMD",
        "INTC",
        "CSCO",
        "QCOM",
        "TXN",
        "IBM",
        "NOW",
        "INTU",
        # Financial
        "BRK-B",
        "JPM",
        "V",
        "MA",
        "BAC",
        "WFC",
        "GS",
        "MS",
        "AXP",
        "BLK",
        # Healthcare
        "LLY",
        "UNH",
        "JNJ",
        "ABBV",
        "MRK",
        "PFE",
        "TMO",
        "ABT",
        "DHR",
        "AMGN",
        # Consumer
        "WMT",
        "COST",
        "HD",
        "PG",
        "KO",
        "PEP",
        "MCD",
        "NKE",
        "SBUX",
        "DIS",
        # Industrial / Energy / Other
        "XOM",
        "CVX",
        "GE",
        "CAT",
        "UNP",
        "BA",
        "RTX",
        "HON",
        "LMT",
        "T",
        "VZ",
        "CMCSA",
        "LIN",
    ]

    # Data fetching
    PRICE_LOOKBACK_DAYS: int = 400  # Extra days for 200-day MA calculation
    DEFAULT_YEARS_BACK: int = 3

    # SEC EDGAR - requires User-Agent with contact info per SEC guidelines
    SEC_USER_AGENT: str = os.environ.get(
        "SEC_USER_AGENT",
        "StockDashboard/1.0 (jackvanced@gmail.com)",
    )
    SEC_BASE_URL: str = "https://data.sec.gov"
    SEC_TICKERS_URL: str = "https://www.sec.gov/files/company_tickers.json"

    # Logging
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")


config = Config()
