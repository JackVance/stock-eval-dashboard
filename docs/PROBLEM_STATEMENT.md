# Problem Statement: Stock Evaluation Dashboard Migration

## 1. What Problem Are We Solving?

A functional stock evaluation dashboard currently runs on EC2, incurring fixed monthly costs (~$8-15/mo for a t3.micro) regardless of usage. The application is used sporadically, making pay-per-use serverless architecture more cost-effective. Additionally, the current data source (yfinance) limits historical financials to ~4 years, while SEC EDGAR provides 10+ years of audited data. The Dash server-rendered approach adds latency compared to a static frontend with API backend.

## 2. Who/What Are the Users or Consumers?

| User/Consumer | Description |
|---------------|-------------|
| **Primary User** | Solo developer/investor viewing stock analysis dashboards |
| **Usage Pattern** | Sporadic — possibly days or weeks between sessions |
| **Concurrent Users** | 1 (no multi-tenancy required) |
| **Access Method** | Web browser on desktop/laptop |
| **Authentication** | None — public dashboard |

## 3. What Are the Inputs and Outputs?

### Inputs
| Input | Source | Description |
|-------|--------|-------------|
| Stock ticker symbol | User input (dropdown or custom entry) | e.g., "AAPL", "MSFT" |
| Year range | User slider input | Historical price data window (up to 20 years back) |
| Stock price data | Yahoo Finance (yfinance) | OHLCV for price charts and moving averages |
| Company financials | SEC EDGAR (10-K/10-Q filings) | 10+ years of income statement, balance sheet, cash flow |
| Company info | Yahoo Finance | Sector, industry, description, key stats, P/E ratios |

### Outputs (from `src/legacy_dashboard.py`)
| Output | Current Implementation | Description |
|--------|----------------------|-------------|
| Price chart | `priceChart()` — Plotly subplots | Close price with 50/200-day MAs (top), volume bars colored by daily change (bottom) |
| Financials timeline | `financialsTimeline()` — Plotly line | Revenue, Operating Expense, Cost of Revenue, Operating Income, Net Income, R&D over time |
| Company summary | `printInfo()` — Markdown text | Name, website, sector/industry, price, market cap, trailing/forward P/E, debt-to-EBITDA, business summary |
| Balance sheet bar | `balanceSheetPlots()` — Plotly grouped bar | Current vs Non-Current for Assets and Liabilities |
| Balance sheet sunburst | `balanceSheetPlots()` — Plotly sunburst | Hierarchical breakdown of assets and liabilities |

### Existing Data Transformations to Preserve
- 50-day and 200-day moving averages (requires fetching 400 extra days before display window)
- Volume bar coloring: green for up days, red for down days
- Reduced financials filtering (only specific keys from full financials)
- Balance sheet hierarchy mapping for sunburst chart
- Custom "buffalo_stone" dark theme (gray background #696969, white text)

### Static Assets to Migrate
- `src/assets/style.css` — Topnav styling (dark bar #333, hover effects)

## 4. What Are the Constraints?

| Constraint | Details |
|------------|---------|
| **Budget** | Near-zero at low usage; must stay within AWS free tier for MVP |
| **Timeline** | No hard deadline; quality over speed |
| **Data Freshness** | Always fetch live data (no caching in MVP) |
| **Historical Depth** | 10+ years of financials required (SEC EDGAR) |
| **Data Range** | Maximum available data for selected time window |
| **Data Sensitivity** | None — all data is publicly available market data |
| **Regulatory** | None — personal use, no PII, no financial advice |
| **Technology** | Python primary, AWS CDK for IaC |
| **Migration** | Must preserve all existing chart types and visual styling |
| **State** | Remember previously searched tickers across sessions |

## 5. What Does "Done" Look Like? (MVP)

- [ ] EC2 instance can be terminated — zero fixed compute costs
- [ ] Static frontend loads from S3/CloudFront
- [ ] User can enter a ticker via dropdown or custom input field
- [ ] All existing visualizations work identically:
  - [ ] Price chart with 50/200-day moving averages and volume subplot
  - [ ] Financials timeline (line chart of key metrics)
  - [ ] Company info summary (markdown text block)
  - [ ] Balance sheet bar chart (assets vs liabilities, current vs non-current)
  - [ ] Balance sheet sunburst (hierarchical breakdown)
- [ ] Year range slider controls price chart date window
- [ ] Custom "buffalo_stone" dark theme preserved
- [ ] Previously searched tickers persist and appear in dropdown
- [ ] Data fetched on-demand via API Gateway + Lambda
- [ ] Monthly cost at typical usage (< 100 requests/month): **~$0**
- [ ] Infrastructure defined in AWS CDK (Python)
- [ ] Single-command deployment

## 6. What Does "Done Well" Look Like? (Stretch Goals)

| Goal | Benefit |
|------|---------|
| **SEC EDGAR integration** | 10+ years of audited financials |
| **Data provider abstraction** | Swap/combine sources without frontend changes |
| **Response caching** | Faster repeat lookups, reduced API calls |
| **Alpha Vantage integration** | Redundant data source, different metrics |
| **Additional analytics** | DCF calculator, peer comparison, custom ratios |
| **Multi-ticker comparison** | Side-by-side stock analysis |
| **Watchlist management** | Organize and categorize saved tickers |

## 7. Current Architecture (As-Is)

```
┌─────────────────────────────────────────────────────────┐
│                      EC2 Instance                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │           Python Dash Application                │    │
│  │  ┌──────────────┐    ┌──────────────────────┐   │    │
│  │  │ Dash Server  │───▶│  Plotly Rendering    │   │    │
│  │  │ (Flask)      │    │  (Server-side)       │   │    │
│  │  └──────────────┘    └──────────────────────┘   │    │
│  │         │                                        │    │
│  │         ▼                                        │    │
│  │  ┌──────────────┐                               │    │
│  │  │   yfinance   │──────▶ Yahoo Finance API      │    │
│  │  └──────────────┘                               │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                    ┌──────────┐
                    │  Browser │
                    └──────────┘
```

**Current Pain Points:**
- Fixed EC2 cost regardless of usage (~$8-15/mo)
- Server-rendered HTML adds latency on each interaction
- yfinance provides only ~4 years of financials
- No data persistence — every page load re-fetches
- Single point of failure (EC2 instance)

---

*Document Status: APPROVED — Ready for Phase 2 (Architecture Decision Records)*
