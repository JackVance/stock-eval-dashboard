"""Merges YFinance (prices, company info) + SEC EDGAR (10+ yr financials)."""
import logging
from datetime import date

from models import BalanceSheet, CompanyInfo, FinancialStatement, PriceData, StockData

from .base import StockDataProvider
from .sec_edgar_provider import SecEdgarProvider
from .yfinance_provider import YFinanceProvider

logger = logging.getLogger(__name__)


class CompositeProvider:
    """SEC EDGAR for financials/balance sheets, YFinance for everything else.
    Falls back to YFinance-only if EDGAR lookup fails."""

    def __init__(self) -> None:
        self.yfinance = YFinanceProvider()
        self.sec_edgar = SecEdgarProvider()

    def get_stock_data(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> StockData:
        prices = self.yfinance.get_prices(ticker, start_date, end_date)
        info = self.yfinance.get_company_info(ticker)
        financials = self._get_financials_with_fallback(ticker)
        balance_sheets = self._get_balance_sheets_with_fallback(ticker)

        return StockData(
            prices=prices,
            info=info,
            financials=financials,
            balance_sheets=balance_sheets,
        )

    def _get_financials_with_fallback(self, ticker: str) -> list[FinancialStatement]:
        try:
            financials = self.sec_edgar.get_financials(ticker)
            if financials:
                logger.info(f"Got {len(financials)} years of financials from SEC EDGAR")
                return financials
        except Exception as e:
            logger.warning(f"SEC EDGAR financials failed for {ticker}: {e}")

        logger.info(f"Falling back to YFinance for {ticker} financials")
        return self.yfinance.get_financials(ticker)

    def _get_balance_sheets_with_fallback(self, ticker: str) -> list[BalanceSheet]:
        try:
            balance_sheets = self.sec_edgar.get_balance_sheets(ticker)
            if balance_sheets:
                logger.info(f"Got {len(balance_sheets)} balance sheets from SEC EDGAR")
                return balance_sheets
        except Exception as e:
            logger.warning(f"SEC EDGAR balance sheets failed for {ticker}: {e}")

        logger.info(f"Falling back to YFinance for {ticker} balance sheets")
        return self.yfinance.get_balance_sheets(ticker)
