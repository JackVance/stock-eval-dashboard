"""Prices, company info, and ~4 years of financials via yfinance."""
from datetime import date, timedelta
from typing import Any

import yfinance as yf

from config import config
from models import BalanceSheet, CompanyInfo, FinancialStatement, PriceData

from .base import StockDataProvider


class YFinanceProvider(StockDataProvider):

    def get_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> PriceData:
        # Fetch extra history so MAs are populated at start_date
        extended_start = start_date - timedelta(days=config.PRICE_LOOKBACK_DAYS)

        df = yf.download(
            ticker,
            start=extended_start.isoformat(),
            end=end_date.isoformat(),
            progress=False,
        )

        if df.empty:
            raise ValueError(f"No price data found for {ticker}")

        # yfinance returns multi-index columns for single ticker; flatten
        if df.columns.nlevels > 1:
            df.columns = df.columns.droplevel(1)

        # MAs computed on full range, then trimmed to display window
        df["MA50"] = df["Close"].rolling(50).mean()
        df["MA200"] = df["Close"].rolling(200).mean()

        display_df = df[start_date.isoformat() : end_date.isoformat()]

        def safe_list(series: Any) -> list[float]:
            return [None if v != v else float(v) for v in series.tolist()]

        def safe_int_list(series: Any) -> list[int]:
            return [int(v) if v == v else 0 for v in series.tolist()]

        return PriceData(
            dates=[d.strftime("%Y-%m-%d") for d in display_df.index],
            open=safe_list(display_df["Open"]),
            high=safe_list(display_df["High"]),
            low=safe_list(display_df["Low"]),
            close=safe_list(display_df["Close"]),
            volume=safe_int_list(display_df["Volume"]),
            ma50=safe_list(display_df["MA50"]),
            ma200=safe_list(display_df["MA200"]),
        )

    def get_company_info(self, ticker: str) -> CompanyInfo:
        tick = yf.Ticker(ticker)
        info = tick.info

        if not info or info.get("symbol") is None:
            raise ValueError(f"No company info found for {ticker}")

        return CompanyInfo(
            symbol=info.get("symbol", ticker),
            name=info.get("longName", ""),
            short_name=info.get("shortName", ""),
            website=info.get("website", ""),
            sector=info.get("sector", ""),
            industry=info.get("industry", ""),
            summary=info.get("longBusinessSummary", ""),
            current_price=float(info.get("currentPrice", 0)),
            market_cap=int(info.get("marketCap", 0)),
            trailing_pe=info.get("trailingPE"),
            forward_pe=info.get("forwardPE"),
            ebitda=info.get("ebitda"),
            total_debt=info.get("totalDebt"),
        )

    def get_financials(self, ticker: str) -> list[FinancialStatement]:
        """~4 years only. Use SEC EDGAR for 10+ year history."""
        tick = yf.Ticker(ticker)
        financials = tick.financials

        if financials is None or financials.empty:
            return []

        df = financials.transpose()  # columns=metrics -> rows=dates

        results = []
        for idx in df.index:
            date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)

            results.append(
                FinancialStatement(
                    date=date_str,
                    total_revenue=self._safe_int(df.loc[idx].get("Total Revenue")),
                    cost_of_revenue=self._safe_int(df.loc[idx].get("Cost Of Revenue")),
                    operating_expense=self._safe_int(df.loc[idx].get("Operating Expense")),
                    operating_income=self._safe_int(df.loc[idx].get("Operating Income")),
                    net_income=self._safe_int(df.loc[idx].get("Net Income")),
                    research_and_development=self._safe_int(
                        df.loc[idx].get("Research And Development")
                    ),
                )
            )

        return results

    def get_balance_sheets(self, ticker: str) -> list[BalanceSheet]:
        tick = yf.Ticker(ticker)
        balance_sheet = tick.balance_sheet

        if balance_sheet is None or balance_sheet.empty:
            return []

        df = balance_sheet.transpose()

        results = []
        for idx in df.index:
            date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
            row = df.loc[idx]

            results.append(
                BalanceSheet(
                    date=date_str,
                    total_assets=self._safe_int(row.get("Total Assets")) or 0,
                    total_liabilities=self._safe_int(
                        row.get("Total Liabilities Net Minority Interest")
                    )
                    or 0,
                    current_assets=self._safe_int(row.get("Current Assets")),
                    current_liabilities=self._safe_int(row.get("Current Liabilities")),
                    non_current_assets=self._safe_int(row.get("Total Non Current Assets")),
                    non_current_liabilities=self._safe_int(
                        row.get("Total Non Current Liabilities Net Minority Interest")
                    ),
                    inventory=self._safe_int(row.get("Inventory")),
                    receivables=self._safe_int(row.get("Receivables")),
                    cash_and_equivalents=self._safe_int(row.get("Cash And Cash Equivalents")),
                    short_term_investments=self._safe_int(row.get("Other Short Term Investments")),
                    other_current_assets=self._safe_int(row.get("Other Current Assets")),
                    net_ppe=self._safe_int(row.get("Net PPE")),
                    investments_and_advances=self._safe_int(row.get("Investments And Advances")),
                    goodwill_and_intangibles=self._safe_int(
                        row.get("Goodwill And Other Intangible Assets")
                    ),
                    other_non_current_assets=self._safe_int(row.get("Other Non Current Assets")),
                    payables=self._safe_int(row.get("Payables And Accrued Expenses")),
                    current_deferred_liabilities=self._safe_int(
                        row.get("Current Deferred Liabilities")
                    ),
                    current_debt=self._safe_int(
                        row.get("Current Debt And Capital Lease Obligation")
                    ),
                    other_current_liabilities=self._safe_int(row.get("Other Current Liabilities")),
                    long_term_debt=self._safe_int(
                        row.get("Long Term Debt And Capital Lease Obligation")
                    ),
                    other_non_current_liabilities=self._safe_int(
                        row.get("Other Non Current Liabilities")
                    ),
                )
            )

        return results

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        """NaN/None -> None, else int."""
        if value is None:
            return None
        try:
            if value != value:  # NaN check
                return None
            return int(value)
        except (ValueError, TypeError):
            return None
