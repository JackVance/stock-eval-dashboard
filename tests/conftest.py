"""Shared test fixtures for model factories and AWS mocks."""
import sys
from pathlib import Path

import pytest

# Make Lambda source importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "lambda"))

from models import (
    BalanceSheet,
    CompanyInfo,
    FinancialStatement,
    PriceData,
    StockData,
)


@pytest.fixture
def sample_prices():
    return PriceData(
        dates=["2024-01-02", "2024-01-03", "2024-01-04"],
        open=[185.0, 186.0, 187.0],
        high=[186.5, 187.5, 188.0],
        low=[184.0, 185.0, 186.0],
        close=[186.0, 187.0, 187.5],
        volume=[50_000_000, 48_000_000, 52_000_000],
        ma50=[182.0, 182.1, 182.2],
        ma200=[178.0, 178.1, 178.2],
    )


@pytest.fixture
def sample_info():
    return CompanyInfo(
        symbol="AAPL",
        name="Apple Inc.",
        short_name="Apple",
        website="https://www.apple.com",
        sector="Technology",
        industry="Consumer Electronics",
        summary="Apple Inc. designs and manufactures consumer electronics.",
        current_price=186.0,
        market_cap=2_900_000_000_000,
        trailing_pe=28.5,
        forward_pe=26.0,
        ebitda=130_000_000_000,
        total_debt=110_000_000_000,
    )


@pytest.fixture
def sample_financials():
    return [
        FinancialStatement(
            date="2023-09-30",
            total_revenue=383_000_000_000,
            cost_of_revenue=214_000_000_000,
            operating_expense=55_000_000_000,
            operating_income=114_000_000_000,
            net_income=97_000_000_000,
            research_and_development=30_000_000_000,
        ),
        FinancialStatement(
            date="2022-09-24",
            total_revenue=394_000_000_000,
            cost_of_revenue=223_000_000_000,
            operating_expense=52_000_000_000,
            operating_income=119_000_000_000,
            net_income=100_000_000_000,
            research_and_development=26_000_000_000,
        ),
    ]


@pytest.fixture
def sample_balance_sheets():
    return [
        BalanceSheet(
            date="2023-09-30",
            total_assets=352_000_000_000,
            total_liabilities=290_000_000_000,
            current_assets=143_000_000_000,
            current_liabilities=145_000_000_000,
        ),
    ]


@pytest.fixture
def sample_stock_data(sample_prices, sample_info, sample_financials, sample_balance_sheets):
    return StockData(
        prices=sample_prices,
        info=sample_info,
        financials=sample_financials,
        balance_sheets=sample_balance_sheets,
    )


def make_api_event(method: str, path: str, body: str | None = None, query: dict | None = None):
    """Build a minimal HTTP API Gateway v2 event."""
    event = {
        "requestContext": {
            "http": {
                "method": method,
                "path": path,
            }
        },
        "queryStringParameters": query,
    }
    if body is not None:
        event["body"] = body
    return event
