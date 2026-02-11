"""10+ years of audited financials from SEC EDGAR XBRL API."""
import json
import logging
from datetime import date, datetime
from typing import Any

import requests

from config import config
from models import BalanceSheet, CompanyInfo, FinancialStatement, PriceData

from .base import StockDataProvider

logger = logging.getLogger(__name__)


class SecEdgarProvider(StockDataProvider):
    """Prices and company info raise NotImplementedError — use YFinance for those."""

    _cik_cache: dict[str, str] = {}
    _company_tickers: dict[str, dict[str, Any]] | None = None

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": config.SEC_USER_AGENT,
                "Accept-Encoding": "gzip, deflate",
            }
        )

    def _get_cik(self, ticker: str) -> str:
        """Ticker -> 10-digit zero-padded CIK. Cached after first lookup."""
        ticker_upper = ticker.upper().replace("-", ".")

        if ticker_upper in self._cik_cache:
            return self._cik_cache[ticker_upper]

        if self._company_tickers is None:
            url = config.SEC_TICKERS_URL
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            self._company_tickers = {}
            for entry in data.values():
                t = entry.get("ticker", "").upper()
                cik = str(entry.get("cik_str", "")).zfill(10)
                self._company_tickers[t] = {"cik": cik, "title": entry.get("title", "")}

        if ticker_upper not in self._company_tickers:
            raise ValueError(f"Ticker {ticker} not found in SEC EDGAR")

        cik = self._company_tickers[ticker_upper]["cik"]
        self._cik_cache[ticker_upper] = cik
        return cik

    def _get_company_facts(self, ticker: str) -> dict[str, Any]:
        """Full XBRL companyfacts JSON for a ticker."""
        cik = self._get_cik(ticker)
        url = f"{config.SEC_BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json"

        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _extract_annual_values(
        self,
        facts: dict[str, Any],
        taxonomy: str,
        concept: str,
    ) -> dict[str, int]:
        """fiscal_year_end_date -> value, filtered to 10-K filings spanning 340-400 days."""
        result: dict[str, int] = {}

        try:
            concept_data = facts["facts"][taxonomy][concept]["units"]
            for unit_type, entries in concept_data.items():
                if unit_type not in ("USD", "shares"):
                    continue
                for entry in entries:
                    if entry.get("form") != "10-K":
                        continue
                    # Frame with "Q" indicates quarterly data leaked into 10-K
                    if "frame" in entry and "Q" in entry.get("frame", ""):
                        continue

                    start_str = entry.get("start", "")
                    end_str = entry.get("end", "")
                    if not start_str or not end_str:
                        continue

                    try:
                        start_dt = datetime.strptime(start_str, "%Y-%m-%d")
                        end_dt = datetime.strptime(end_str, "%Y-%m-%d")
                        period_days = (end_dt - start_dt).days

                        if period_days < 340 or period_days > 400:
                            continue
                    except ValueError:
                        continue

                    val = entry.get("val")
                    if end_str and val is not None:
                        result[end_str] = int(val)
        except KeyError:
            pass

        return result

    def get_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> PriceData:
        """SEC EDGAR doesn't provide price data."""
        raise NotImplementedError("SEC EDGAR does not provide price data. Use YFinanceProvider.")

    def get_company_info(self, ticker: str) -> CompanyInfo:
        """SEC EDGAR provides limited company info."""
        raise NotImplementedError(
            "SEC EDGAR provides limited company info. Use YFinanceProvider."
        )

    def _merge_annual_values(self, *dicts: dict[str, int]) -> dict[str, int]:
        """First-wins merge across alternative XBRL concept tags for the same date."""
        result: dict[str, int] = {}
        for d in dicts:
            for date, val in d.items():
                if date not in result:
                    result[date] = val
        return result

    def get_financials(self, ticker: str) -> list[FinancialStatement]:
        facts = self._get_company_facts(ticker)

        # Merge alternative XBRL tags — companies change reporting concepts over time
        revenue = self._merge_annual_values(
            self._extract_annual_values(facts, "us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
            self._extract_annual_values(facts, "us-gaap", "Revenues"),
            self._extract_annual_values(facts, "us-gaap", "SalesRevenueNet"),
        )

        cost_of_revenue = self._merge_annual_values(
            self._extract_annual_values(facts, "us-gaap", "CostOfRevenue"),
            self._extract_annual_values(facts, "us-gaap", "CostOfGoodsAndServicesSold"),
        )

        operating_expense = self._extract_annual_values(facts, "us-gaap", "OperatingExpenses")

        operating_income = self._extract_annual_values(facts, "us-gaap", "OperatingIncomeLoss")

        net_income = self._extract_annual_values(facts, "us-gaap", "NetIncomeLoss")

        rnd = self._extract_annual_values(facts, "us-gaap", "ResearchAndDevelopmentExpense")

        all_dates = set()
        for data in [revenue, cost_of_revenue, operating_expense, operating_income, net_income, rnd]:
            all_dates.update(data.keys())
        results = []
        for date_str in sorted(all_dates, reverse=True):
            results.append(
                FinancialStatement(
                    date=date_str,
                    total_revenue=revenue.get(date_str),
                    cost_of_revenue=cost_of_revenue.get(date_str),
                    operating_expense=operating_expense.get(date_str),
                    operating_income=operating_income.get(date_str),
                    net_income=net_income.get(date_str),
                    research_and_development=rnd.get(date_str),
                )
            )

        return results

    def get_balance_sheets(self, ticker: str) -> list[BalanceSheet]:
        facts = self._get_company_facts(ticker)
        total_assets = self._extract_annual_values(facts, "us-gaap", "Assets")
        total_liabilities = self._merge_annual_values(
            self._extract_annual_values(facts, "us-gaap", "Liabilities"),
            self._extract_annual_values(facts, "us-gaap", "LiabilitiesAndStockholdersEquity"),
        )

        current_assets = self._merge_annual_values(
            self._extract_annual_values(facts, "us-gaap", "AssetsCurrent"),
        )
        current_liabilities = self._merge_annual_values(
            self._extract_annual_values(facts, "us-gaap", "LiabilitiesCurrent"),
        )

        non_current_assets = self._extract_annual_values(facts, "us-gaap", "AssetsNoncurrent")
        non_current_liabilities = self._extract_annual_values(facts, "us-gaap", "LiabilitiesNoncurrent")

        inventory = self._merge_annual_values(
            self._extract_annual_values(facts, "us-gaap", "InventoryNet"),
            self._extract_annual_values(facts, "us-gaap", "Inventory"),
        )
        receivables = self._merge_annual_values(
            self._extract_annual_values(facts, "us-gaap", "AccountsReceivableNetCurrent"),
            self._extract_annual_values(facts, "us-gaap", "ReceivablesNetCurrent"),
            self._extract_annual_values(facts, "us-gaap", "AccountsReceivableNet"),
        )
        cash = self._merge_annual_values(
            self._extract_annual_values(facts, "us-gaap", "CashAndCashEquivalentsAtCarryingValue"),
            self._extract_annual_values(facts, "us-gaap", "Cash"),
            self._extract_annual_values(facts, "us-gaap", "CashCashEquivalentsAndShortTermInvestments"),
        )
        short_term_inv = self._merge_annual_values(
            self._extract_annual_values(facts, "us-gaap", "ShortTermInvestments"),
            self._extract_annual_values(facts, "us-gaap", "MarketableSecuritiesCurrent"),
        )
        ppe = self._merge_annual_values(
            self._extract_annual_values(facts, "us-gaap", "PropertyPlantAndEquipmentNet"),
            self._extract_annual_values(facts, "us-gaap", "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization"),
        )
        goodwill = self._extract_annual_values(facts, "us-gaap", "Goodwill")
        intangibles = self._extract_annual_values(facts, "us-gaap", "IntangibleAssetsNetExcludingGoodwill")
        payables = self._merge_annual_values(
            self._extract_annual_values(facts, "us-gaap", "AccountsPayableCurrent"),
            self._extract_annual_values(facts, "us-gaap", "AccountsPayableAndAccruedLiabilitiesCurrent"),
        )
        long_term_debt = self._extract_annual_values(facts, "us-gaap", "LongTermDebtNoncurrent")

        all_dates = set(total_assets.keys())

        results = []
        for date_str in sorted(all_dates, reverse=True):
            ta = total_assets.get(date_str, 0)
            tl = total_liabilities.get(date_str, 0)
            ca = current_assets.get(date_str)
            cl = current_liabilities.get(date_str)
            nca = non_current_assets.get(date_str)
            ncl = non_current_liabilities.get(date_str)

            # Derive non-current from total - current when not reported directly
            if nca is None and ta and ca is not None:
                nca = ta - ca
            if ncl is None and tl and cl is not None:
                ncl = tl - cl

            # Combine into single sunburst node
            gw = goodwill.get(date_str)
            intg = intangibles.get(date_str)
            gw_intg = None
            if gw is not None or intg is not None:
                gw_intg = (gw or 0) + (intg or 0)

            results.append(
                BalanceSheet(
                    date=date_str,
                    total_assets=ta,
                    total_liabilities=tl,
                    current_assets=ca,
                    current_liabilities=cl,
                    non_current_assets=nca,
                    non_current_liabilities=ncl,
                    inventory=inventory.get(date_str),
                    receivables=receivables.get(date_str),
                    cash_and_equivalents=cash.get(date_str),
                    short_term_investments=short_term_inv.get(date_str),
                    net_ppe=ppe.get(date_str),
                    goodwill_and_intangibles=gw_intg,
                    payables=payables.get(date_str),
                    long_term_debt=long_term_debt.get(date_str),
                )
            )

        return results
