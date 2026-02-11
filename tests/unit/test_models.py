"""Tests for data models."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "lambda"))

from models import (
    BalanceSheet,
    CompanyInfo,
    FinancialStatement,
    PriceData,
    StockData,
)


class TestPriceData:

    def test_to_dict(self):
        data = PriceData(
            dates=["2024-01-01", "2024-01-02"],
            open=[100.0, 101.0],
            high=[102.0, 103.0],
            low=[99.0, 100.0],
            close=[101.0, 102.0],
            volume=[1000000, 1100000],
            ma50=[100.5, 100.6],
            ma200=[99.0, 99.1],
        )

        result = data.to_dict()

        assert result["dates"] == ["2024-01-01", "2024-01-02"]
        assert result["close"] == [101.0, 102.0]
        assert result["ma50"] == [100.5, 100.6]


class TestCompanyInfo:

    def test_to_dict(self):
        info = CompanyInfo(
            symbol="AAPL",
            name="Apple Inc.",
            short_name="Apple",
            website="https://apple.com",
            sector="Technology",
            industry="Consumer Electronics",
            summary="Apple designs...",
            current_price=185.50,
            market_cap=2900000000000,
            trailing_pe=28.5,
            forward_pe=26.0,
            ebitda=130000000000,
            total_debt=110000000000,
        )

        result = info.to_dict()

        assert result["symbol"] == "AAPL"
        assert result["shortName"] == "Apple"
        assert result["currentPrice"] == 185.50
        assert result["trailingPe"] == 28.5


class TestFinancialStatement:

    def test_to_dict_with_nulls(self):
        stmt = FinancialStatement(
            date="2023-09-30",
            total_revenue=383000000000,
            net_income=96000000000,
            research_and_development=None,
        )

        result = stmt.to_dict()

        assert result["date"] == "2023-09-30"
        assert result["totalRevenue"] == 383000000000
        assert result["researchAndDevelopment"] is None


class TestBalanceSheet:

    def test_to_dict(self):
        bs = BalanceSheet(
            date="2023-09-30",
            total_assets=352000000000,
            total_liabilities=290000000000,
            current_assets=143000000000,
            current_liabilities=145000000000,
        )

        result = bs.to_dict()

        assert result["totalAssets"] == 352000000000
        assert result["currentAssets"] == 143000000000


class TestStockData:

    def test_to_dict(self):
        prices = PriceData(
            dates=["2024-01-01"],
            open=[100.0],
            high=[102.0],
            low=[99.0],
            close=[101.0],
            volume=[1000000],
            ma50=[100.5],
            ma200=[99.0],
        )
        info = CompanyInfo(
            symbol="TEST",
            name="Test Inc",
            short_name="Test",
            website="",
            sector="",
            industry="",
            summary="",
            current_price=100.0,
            market_cap=1000000000,
            trailing_pe=None,
            forward_pe=None,
            ebitda=None,
            total_debt=None,
        )

        data = StockData(
            prices=prices,
            info=info,
            financials=[],
            balance_sheets=[],
        )

        result = data.to_dict()

        assert "prices" in result
        assert "info" in result
        assert result["info"]["symbol"] == "TEST"
        assert result["financials"] == []
