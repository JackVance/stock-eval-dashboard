# ADR-005: Data Provider Strategy

## Status
Proposed

## Context
The dashboard requires multiple types of stock data:
1. **Price history** — OHLCV for charts and moving averages
2. **Volume data** — For volume subplot
3. **Company info** — Sector, industry, P/E ratios, business summary
4. **Financials** — Income statement, balance sheet, cash flow (10+ years required)

No single free data source provides all of this well. We need a strategy that combines sources and allows future flexibility.

## Options Considered

| Source | Price Data | Company Info | Financials | Limits | Cost |
|--------|-----------|--------------|------------|--------|------|
| **yfinance** | ✅ Excellent | ✅ Good | ⚠️ ~4 years | Unofficial, may break | Free |
| **SEC EDGAR** | ❌ None | ⚠️ From filings | ✅ 10+ years | Official, reliable | Free |
| **Alpha Vantage** | ✅ Good | ⚠️ Limited | ✅ Good depth | 25 req/day free | Free (limited) |
| **Polygon.io** | ✅ Excellent | ✅ Good | ❌ Limited | 5 req/min free | $29+/mo |
| **Financial Modeling Prep** | ✅ Good | ✅ Good | ✅ Good | 250 req/day free | Free (limited) |

## Decision
**Dual-source approach: yfinance + SEC EDGAR**

With a **provider abstraction layer** allowing future source additions.

### Source Responsibilities

| Data Type | Primary Source | Fallback | Rationale |
|-----------|---------------|----------|-----------|
| Price/Volume | yfinance | (none for MVP) | Best free source, decades of data |
| Company info | yfinance | SEC filings | Real-time P/E, current metrics |
| Financials | SEC EDGAR | yfinance | 10+ years of audited data |

### SEC EDGAR Integration

SEC EDGAR provides structured data via:
- **XBRL filings** — Machine-readable financial statements
- **Company Facts API** — `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`
- **Submissions API** — Filing history and metadata

Approach:
1. Map ticker → CIK (SEC identifier) via SEC's company tickers JSON
2. Fetch company facts JSON (all historical XBRL data in one call)
3. Extract income statement, balance sheet, cash flow line items
4. Normalize to match existing dashboard format

### Provider Abstraction Layer

```python
# Abstract interface
class StockDataProvider(Protocol):
    def get_prices(self, ticker: str, start: date, end: date) -> PriceData: ...
    def get_company_info(self, ticker: str) -> CompanyInfo: ...
    def get_financials(self, ticker: str) -> Financials: ...

# Concrete implementations
class YFinanceProvider(StockDataProvider): ...
class SECEdgarProvider(StockDataProvider): ...
class AlphaVantageProvider(StockDataProvider): ...  # Future

# Composite provider
class CompositeProvider:
    def __init__(self,
                 price_provider: StockDataProvider,
                 info_provider: StockDataProvider,
                 financials_provider: StockDataProvider): ...
```

## Consequences

**Positive:**
- 10+ years of audited financials (SEC EDGAR)
- Real-time price data (yfinance)
- Current company metrics (yfinance)
- Abstraction allows swapping sources without frontend changes
- All free, no API keys required

**Negative:**
- yfinance is unofficial and may break with Yahoo changes
- SEC EDGAR requires CIK lookup (minor latency)
- Two different data formats to normalize
- SEC data is US-listed companies only

**Risks & Mitigations:**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| yfinance breaks | Medium | Abstraction layer allows swap to Alpha Vantage |
| SEC API rate limits | Low | 10 req/sec limit is generous for single user |
| Data format changes | Low | Versioned parsers, good error handling |

**Future enhancements:**
- Add Alpha Vantage as redundant price source
- Add Financial Modeling Prep for international stocks
- Cache SEC data (doesn't change after filing)
