"""Configuration loaded from environment variables."""
import os


class Config:
    TABLE_NAME: str = os.environ.get("TABLE_NAME", "StockDashboard")
    TICKERS_PK: str = "TICKERS"

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

    # Data fetching
    PRICE_LOOKBACK_DAYS: int = 400  # Extra days for 200-day MA calculation
    DEFAULT_YEARS_BACK: int = 3

    # SEC EDGAR - requires User-Agent with contact info per SEC guidelines
    SEC_USER_AGENT: str = os.environ.get(
        "SEC_USER_AGENT",
        "StockDashboard/1.0 (stockdashboard@example.com)",
    )
    SEC_BASE_URL: str = "https://data.sec.gov"
    SEC_TICKERS_URL: str = "https://www.sec.gov/files/company_tickers.json"

    # Logging
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")


config = Config()
