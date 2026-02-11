"""Interface that all stock data providers must implement."""
from abc import ABC, abstractmethod
from datetime import date

from models import BalanceSheet, CompanyInfo, FinancialStatement, PriceData


class StockDataProvider(ABC):
    """All results ordered newest-first."""

    @abstractmethod
    def get_prices(self, ticker: str, start_date: date, end_date: date) -> PriceData: ...

    @abstractmethod
    def get_company_info(self, ticker: str) -> CompanyInfo: ...

    @abstractmethod
    def get_financials(self, ticker: str) -> list[FinancialStatement]: ...

    @abstractmethod
    def get_balance_sheets(self, ticker: str) -> list[BalanceSheet]: ...
