"""Unit tests for CompositeProvider fallback logic."""
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "lambda"))

from providers.composite import CompositeProvider


@pytest.fixture
def provider():
    p = CompositeProvider()
    p.yfinance = MagicMock()
    p.sec_edgar = MagicMock()
    return p


class TestGetStockData:

    def test_uses_yfinance_for_prices_and_info(self, provider, sample_prices, sample_info):
        provider.yfinance.get_prices.return_value = sample_prices
        provider.yfinance.get_company_info.return_value = sample_info
        provider.sec_edgar.get_financials.return_value = []
        provider.sec_edgar.get_balance_sheets.return_value = []
        provider.yfinance.get_financials.return_value = []
        provider.yfinance.get_balance_sheets.return_value = []

        result = provider.get_stock_data("AAPL", date(2024, 1, 1), date(2024, 12, 31))

        provider.yfinance.get_prices.assert_called_once()
        provider.yfinance.get_company_info.assert_called_once()
        assert result.prices == sample_prices
        assert result.info == sample_info


class TestFinancialsFallback:

    def test_uses_sec_edgar_when_available(self, provider, sample_prices, sample_info, sample_financials):
        provider.yfinance.get_prices.return_value = sample_prices
        provider.yfinance.get_company_info.return_value = sample_info
        provider.sec_edgar.get_financials.return_value = sample_financials
        provider.sec_edgar.get_balance_sheets.return_value = []
        provider.yfinance.get_balance_sheets.return_value = []

        result = provider.get_stock_data("AAPL", date(2024, 1, 1), date(2024, 12, 31))

        assert result.financials == sample_financials
        provider.yfinance.get_financials.assert_not_called()

    def test_falls_back_to_yfinance_on_sec_error(self, provider, sample_prices, sample_info, sample_financials):
        provider.yfinance.get_prices.return_value = sample_prices
        provider.yfinance.get_company_info.return_value = sample_info
        provider.sec_edgar.get_financials.side_effect = Exception("SEC down")
        provider.yfinance.get_financials.return_value = sample_financials
        provider.sec_edgar.get_balance_sheets.return_value = []
        provider.yfinance.get_balance_sheets.return_value = []

        result = provider.get_stock_data("AAPL", date(2024, 1, 1), date(2024, 12, 31))

        assert result.financials == sample_financials
        provider.yfinance.get_financials.assert_called_once_with("AAPL")

    def test_falls_back_to_yfinance_when_sec_returns_empty(self, provider, sample_prices, sample_info, sample_financials):
        provider.yfinance.get_prices.return_value = sample_prices
        provider.yfinance.get_company_info.return_value = sample_info
        provider.sec_edgar.get_financials.return_value = []
        provider.yfinance.get_financials.return_value = sample_financials
        provider.sec_edgar.get_balance_sheets.return_value = []
        provider.yfinance.get_balance_sheets.return_value = []

        result = provider.get_stock_data("AAPL", date(2024, 1, 1), date(2024, 12, 31))

        assert result.financials == sample_financials
        provider.yfinance.get_financials.assert_called_once()


class TestBalanceSheetFallback:

    def test_uses_sec_edgar_when_available(self, provider, sample_prices, sample_info, sample_balance_sheets):
        provider.yfinance.get_prices.return_value = sample_prices
        provider.yfinance.get_company_info.return_value = sample_info
        provider.sec_edgar.get_financials.return_value = []
        provider.yfinance.get_financials.return_value = []
        provider.sec_edgar.get_balance_sheets.return_value = sample_balance_sheets

        result = provider.get_stock_data("AAPL", date(2024, 1, 1), date(2024, 12, 31))

        assert result.balance_sheets == sample_balance_sheets
        provider.yfinance.get_balance_sheets.assert_not_called()

    def test_falls_back_to_yfinance_on_sec_error(self, provider, sample_prices, sample_info, sample_balance_sheets):
        provider.yfinance.get_prices.return_value = sample_prices
        provider.yfinance.get_company_info.return_value = sample_info
        provider.sec_edgar.get_financials.return_value = []
        provider.yfinance.get_financials.return_value = []
        provider.sec_edgar.get_balance_sheets.side_effect = Exception("SEC down")
        provider.yfinance.get_balance_sheets.return_value = sample_balance_sheets

        result = provider.get_stock_data("AAPL", date(2024, 1, 1), date(2024, 12, 31))

        assert result.balance_sheets == sample_balance_sheets
        provider.yfinance.get_balance_sheets.assert_called_once_with("AAPL")
