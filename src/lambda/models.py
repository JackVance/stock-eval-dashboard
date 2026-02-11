"""API response models. All to_dict() methods output camelCase for JSON."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PriceData:
    """OHLCV + 50/200-day moving averages."""

    dates: list[str]
    open: list[float]
    high: list[float]
    low: list[float]
    close: list[float]
    volume: list[int]
    ma50: list[float | None]
    ma200: list[float | None]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dates": self.dates,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "ma50": self.ma50,
            "ma200": self.ma200,
        }


@dataclass
class CompanyInfo:

    symbol: str
    name: str
    short_name: str
    website: str
    sector: str
    industry: str
    summary: str
    current_price: float
    market_cap: int
    trailing_pe: float | None
    forward_pe: float | None
    ebitda: int | None
    total_debt: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "shortName": self.short_name,
            "website": self.website,
            "sector": self.sector,
            "industry": self.industry,
            "summary": self.summary,
            "currentPrice": self.current_price,
            "marketCap": self.market_cap,
            "trailingPe": self.trailing_pe,
            "forwardPe": self.forward_pe,
            "ebitda": self.ebitda,
            "totalDebt": self.total_debt,
        }


@dataclass
class FinancialStatement:
    """Single fiscal year from 10-K filing."""

    date: str
    total_revenue: int | None = None
    cost_of_revenue: int | None = None
    operating_expense: int | None = None
    operating_income: int | None = None
    net_income: int | None = None
    research_and_development: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "totalRevenue": self.total_revenue,
            "costOfRevenue": self.cost_of_revenue,
            "operatingExpense": self.operating_expense,
            "operatingIncome": self.operating_income,
            "netIncome": self.net_income,
            "researchAndDevelopment": self.research_and_development,
        }


@dataclass
class BalanceSheet:
    """Single-period balance sheet. Detailed fields feed the sunburst chart."""

    date: str
    total_assets: int
    total_liabilities: int
    current_assets: int | None = None
    current_liabilities: int | None = None
    non_current_assets: int | None = None
    non_current_liabilities: int | None = None
    inventory: int | None = None
    receivables: int | None = None
    cash_and_equivalents: int | None = None
    short_term_investments: int | None = None
    other_current_assets: int | None = None
    net_ppe: int | None = None
    investments_and_advances: int | None = None
    goodwill_and_intangibles: int | None = None
    other_non_current_assets: int | None = None
    payables: int | None = None
    current_deferred_liabilities: int | None = None
    current_debt: int | None = None
    other_current_liabilities: int | None = None
    long_term_debt: int | None = None
    other_non_current_liabilities: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "totalAssets": self.total_assets,
            "totalLiabilities": self.total_liabilities,
            "currentAssets": self.current_assets,
            "currentLiabilities": self.current_liabilities,
            "nonCurrentAssets": self.non_current_assets,
            "nonCurrentLiabilities": self.non_current_liabilities,
            "inventory": self.inventory,
            "receivables": self.receivables,
            "cashAndEquivalents": self.cash_and_equivalents,
            "shortTermInvestments": self.short_term_investments,
            "otherCurrentAssets": self.other_current_assets,
            "netPpe": self.net_ppe,
            "investmentsAndAdvances": self.investments_and_advances,
            "goodwillAndIntangibles": self.goodwill_and_intangibles,
            "otherNonCurrentAssets": self.other_non_current_assets,
            "payables": self.payables,
            "currentDeferredLiabilities": self.current_deferred_liabilities,
            "currentDebt": self.current_debt,
            "otherCurrentLiabilities": self.other_current_liabilities,
            "longTermDebt": self.long_term_debt,
            "otherNonCurrentLiabilities": self.other_non_current_liabilities,
        }


@dataclass
class StockData:
    """Top-level response combining all data for a ticker."""

    prices: PriceData
    info: CompanyInfo
    financials: list[FinancialStatement]
    balance_sheets: list[BalanceSheet]

    def to_dict(self) -> dict[str, Any]:
        return {
            "prices": self.prices.to_dict(),
            "info": self.info.to_dict(),
            "financials": [f.to_dict() for f in self.financials],
            "balanceSheets": [b.to_dict() for b in self.balance_sheets],
        }
