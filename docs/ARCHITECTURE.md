# System Architecture: Stock Evaluation Dashboard

## 1. System Overview

A serverless stock evaluation dashboard that fetches market data on-demand and renders interactive Plotly charts in the browser.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                  FRONTEND                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      Route 53 DNS (stocks.jhviv.com)                   │  │
│  │                         A record → CloudFront                          │  │
│  └───────────────────────────────┬───────────────────────────────────────┘  │
│                                  │                                           │
│  ┌───────────────────────────────▼───────────────────────────────────────┐  │
│  │                         CloudFront (CDN)                               │  │
│  │            HTTPS (ACM certificate), edge caching, gzip                 │  │
│  └───────────────────────────────┬───────────────────────────────────────┘  │
│                                  │                                           │
│  ┌───────────────────────────────▼───────────────────────────────────────┐  │
│  │                          S3 Bucket                                     │  │
│  │              index.html, style.css, *.js, plotly.min.js               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTPS API calls
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                   API                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      API Gateway (HTTP API)                            │  │
│  │                /api/stock/{ticker}  /api/tickers                       │  │
│  └───────────────────────────────┬───────────────────────────────────────┘  │
│                                  │                                           │
│  ┌───────────────────────────────▼───────────────────────────────────────┐  │
│  │                     Lambda (Container Image)                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐   │  │
│  │  │   Handler   │  │  Providers  │  │      Data Models            │   │  │
│  │  │  (routing)  │──│  - yfinance │  │  - PriceData                │   │  │
│  │  └─────────────┘  │  - SEC EDGAR│  │  - CompanyInfo              │   │  │
│  │                   └─────────────┘  │  - Financials               │   │  │
│  │                                    └─────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
┌─────────────────────────────┐   ┌─────────────────────────────────────────┐
│        DynamoDB             │   │           External APIs                  │
│  ┌───────────────────────┐  │   │  ┌─────────────┐  ┌─────────────────┐   │
│  │ PK: "TICKERS"         │  │   │  │  Yahoo      │  │   SEC EDGAR     │   │
│  │ tickers: [AAPL, ...]  │  │   │  │  Finance    │  │   (data.sec.gov)│   │
│  └───────────────────────┘  │   │  │  (yfinance) │  │                 │   │
└─────────────────────────────┘   │  └─────────────┘  └─────────────────┘   │
                                  └─────────────────────────────────────────┘
```

## 2. Component Inventory

### 2.1 Frontend Components

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **Route 53 DNS** | AWS Route 53 | Custom domain (stocks.jhviv.com) |
| **ACM Certificate** | AWS ACM (us-east-1) | SSL/TLS certificate for HTTPS |
| **CloudFront Distribution** | AWS CloudFront | CDN, HTTPS termination, caching |
| **S3 Bucket** | AWS S3 | Static file storage (HTML, CSS, JS) |
| **index.html** | HTML5 | Page structure, Plotly containers |
| **style.css** | CSS3 | buffalo_stone theme, topnav, layout |
| **main.js** | Vanilla JS | Event handlers, orchestration |
| **api.js** | Vanilla JS | API client, fetch wrapper |
| **charts.js** | Vanilla JS + Plotly.js | Chart rendering functions |
| **state.js** | Vanilla JS | Ticker list, current selection |

### 2.2 Backend Components

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **API Gateway** | AWS HTTP API | Request routing, CORS, throttling |
| **Lambda Function** | Python 3.11 (container) | Business logic, data aggregation |
| **handler.py** | Python | Request routing, response formatting |
| **providers/yfinance.py** | Python | Price data, company info |
| **providers/sec_edgar.py** | Python | Historical financials (10+ years) |
| **providers/base.py** | Python | Provider protocol/interface |
| **models.py** | Python (dataclasses) | Data structures |

### 2.3 Data Components

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **DynamoDB Table** | AWS DynamoDB (on-demand) | Ticker list persistence |
| **ECR Repository** | AWS ECR | Lambda container image storage |

## 3. Data Model

### 3.1 DynamoDB Schema

**Table: StockDashboard**

| Attribute | Type | Description |
|-----------|------|-------------|
| `PK` | String (Partition Key) | Record identifier |
| `tickers` | String Set | List of saved ticker symbols |

**Access Patterns:**

| Operation | Key | Action |
|-----------|-----|--------|
| Get ticker list | `PK = "TICKERS"` | `GetItem` |
| Add ticker | `PK = "TICKERS"` | `UpdateItem ADD tickers :t` |
| Remove ticker | `PK = "TICKERS"` | `UpdateItem DELETE tickers :t` |

### 3.2 API Response Models

```python
@dataclass
class PriceData:
    dates: list[str]           # ISO date strings
    open: list[float]
    high: list[float]
    low: list[float]
    close: list[float]
    volume: list[int]
    ma50: list[float | None]   # 50-day moving average
    ma200: list[float | None]  # 200-day moving average

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

@dataclass
class FinancialStatement:
    date: str                  # Fiscal year end
    total_revenue: int | None
    cost_of_revenue: int | None
    operating_expense: int | None
    operating_income: int | None
    net_income: int | None
    research_and_development: int | None

@dataclass
class BalanceSheet:
    date: str
    total_assets: int
    total_liabilities: int
    current_assets: int | None
    current_liabilities: int | None
    non_current_assets: int | None
    non_current_liabilities: int | None
    # Detailed breakdown for sunburst
    inventory: int | None
    receivables: int | None
    cash_and_equivalents: int | None
    short_term_investments: int | None
    net_ppe: int | None
    goodwill_and_intangibles: int | None
    payables: int | None
    current_debt: int | None
    long_term_debt: int | None
    # ... additional line items

@dataclass
class StockData:
    prices: PriceData
    info: CompanyInfo
    financials: list[FinancialStatement]  # 10+ years
    balance_sheets: list[BalanceSheet]    # Most recent available
```

## 4. API Contract

**Base URL:** `https://{api-id}.execute-api.{region}.amazonaws.com`

### 4.1 Get Stock Data

```
GET /api/stock/{ticker}?start_year={YYYY}&end_year={YYYY}
```

**Path Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Stock symbol (e.g., "AAPL") |

**Query Parameters:**
| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `start_year` | int | No | current - 3 | Start of price data range |
| `end_year` | int | No | current | End of price data range |

**Response: 200 OK**
```json
{
  "prices": {
    "dates": ["2024-01-02", "2024-01-03", ...],
    "open": [185.50, 186.20, ...],
    "high": [186.80, 187.10, ...],
    "low": [184.90, 185.50, ...],
    "close": [186.10, 186.80, ...],
    "volume": [50123000, 48234000, ...],
    "ma50": [182.30, 182.45, ...],
    "ma200": [178.50, 178.62, ...]
  },
  "info": {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "short_name": "Apple",
    "website": "https://www.apple.com",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "summary": "Apple Inc. designs, manufactures...",
    "current_price": 186.10,
    "market_cap": 2890000000000,
    "trailing_pe": 28.5,
    "forward_pe": 26.2,
    "ebitda": 130000000000,
    "total_debt": 110000000000
  },
  "financials": [
    {
      "date": "2023-09-30",
      "total_revenue": 383285000000,
      "cost_of_revenue": 214137000000,
      "operating_expense": 54847000000,
      "operating_income": 114301000000,
      "net_income": 96995000000,
      "research_and_development": 29915000000
    },
    // ... 10+ years of data from SEC EDGAR
  ],
  "balance_sheets": [
    {
      "date": "2023-09-30",
      "total_assets": 352583000000,
      "total_liabilities": 290437000000,
      "current_assets": 143566000000,
      "current_liabilities": 145308000000,
      // ... detailed breakdown
    }
  ]
}
```

**Response: 404 Not Found**
```json
{
  "error": "Ticker not found",
  "ticker": "INVALID"
}
```

**Response: 500 Internal Server Error**
```json
{
  "error": "Failed to fetch data from provider",
  "details": "yfinance connection timeout"
}
```

### 4.2 Get Saved Tickers

```
GET /api/tickers
```

**Response: 200 OK**
```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL", "NVDA"]
}
```

### 4.3 Add Ticker

```
POST /api/tickers
Content-Type: application/json

{
  "ticker": "NVDA"
}
```

**Response: 201 Created**
```json
{
  "success": true,
  "ticker": "NVDA"
}
```

### 4.4 Remove Ticker

```
DELETE /api/tickers/{ticker}
```

**Response: 200 OK**
```json
{
  "success": true,
  "ticker": "NVDA"
}
```

## 5. Security Design

### 5.1 IAM Roles

**Lambda Execution Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/StockDashboard"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### 5.2 Network Security

| Layer | Configuration |
|-------|---------------|
| **CloudFront** | HTTPS only (redirect HTTP), TLSv1.2 minimum |
| **API Gateway** | HTTPS only, no VPC (public internet) |
| **Lambda** | No VPC needed (external API access only) |
| **DynamoDB** | IAM auth, no public access |
| **S3** | Private bucket, CloudFront OAC access only |

### 5.3 Data Security

| Data Type | At Rest | In Transit |
|-----------|---------|------------|
| Static files | S3 SSE-S3 (default) | HTTPS via CloudFront |
| Ticker list | DynamoDB encryption (default) | HTTPS via API Gateway |
| Stock data | Not stored (fetched live) | HTTPS from providers |

### 5.4 Input Validation

| Input | Validation |
|-------|------------|
| `ticker` | Uppercase, 1-5 alphanumeric chars, sanitized |
| `start_year` | Integer, 1900-current year |
| `end_year` | Integer, >= start_year, <= current year |

### 5.5 Authentication

**MVP:** None — public dashboard as specified.

**Future option:** Add Cognito User Pool or API key if needed.

## 6. Cost Estimate

### 6.1 Monthly Cost at Expected Usage

| Service | Free Tier | Expected Usage | Monthly Cost |
|---------|-----------|----------------|--------------|
| **Lambda** | 1M requests, 400K GB-sec | ~100 requests, ~50 GB-sec | $0.00 |
| **API Gateway** | 1M requests (12 mo) | ~100 requests | $0.00 |
| **DynamoDB** | 25 RCU/WCU, 25GB | <1 RCU/WCU, <1KB | $0.00 |
| **S3** | 5GB, 20K requests | <1MB, <1K requests | $0.00 |
| **CloudFront** | 1TB transfer, 10M requests | <1GB, <10K requests | $0.00 |
| **ECR** | 500MB (private) | ~200MB image | $0.00 |
| **ECR (after free tier)** | — | ~200MB image | ~$0.02 |
| **CloudWatch Logs** | 5GB ingest | <100MB | $0.00 |

**Total: ~$0.00 - $0.02/month**

### 6.2 Cost at Higher Usage (1000 requests/month)

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| Lambda | 1000 req × 5s × 512MB | $0.00 (within free tier) |
| API Gateway | 1000 requests | $0.00 (within free tier) |
| DynamoDB | ~2000 RCU | $0.00 (within free tier) |
| Data Transfer | ~50MB | $0.00 |

**Total: ~$0.00/month** (still within free tier)

### 6.3 Cost Risks

| Risk | Trigger | Mitigation |
|------|---------|------------|
| Lambda timeout loops | Bug causing retries | Set concurrency limit (10) |
| DynamoDB hot partition | N/A (single item) | N/A |
| CloudFront overage | Viral traffic | Set spend alert at $1 |

## 7. Deployment Strategy

### 7.1 CDK Stack Structure

```
infra/cdk/
├── app.py                 # CDK app entry point
├── cdk.json              # CDK configuration
└── stacks/
    ├── __init__.py
    ├── frontend_stack.py  # S3 + CloudFront
    ├── api_stack.py       # API Gateway + Lambda
    └── storage_stack.py   # DynamoDB + ECR
```

**Stack Dependencies:**
```
StorageStack (DynamoDB, ECR)
      │
      ▼
   ApiStack (Lambda, API Gateway)
      │
      ▼
 FrontendStack (S3, CloudFront)
      │
      └── Outputs API URL to frontend config
```

### 7.2 Environments

| Environment | Purpose | Differences |
|-------------|---------|-------------|
| **dev** | Development/testing | Separate stack, relaxed throttling |
| **prod** | Production | Primary stack, monitoring enabled |

Stack naming: `StockDashboard-{env}-{component}`

### 7.3 Deployment Commands

```bash
# First-time setup
cd infra/cdk
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cdk bootstrap

# Deploy all stacks
cdk deploy --all

# Deploy specific stack
cdk deploy StockDashboard-prod-Api

# Destroy (cleanup)
cdk destroy --all
```

### 7.4 CI/CD Pipeline (Future)

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: npm install -g aws-cdk
      - run: cdk deploy --all --require-approval never
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

---

## 8. Risks & Open Questions

### 8.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| yfinance API breaks | Medium | High | Provider abstraction allows swap to Alpha Vantage |
| SEC EDGAR rate limiting | Low | Medium | 10 req/sec is generous; add exponential backoff |
| Lambda cold starts | Certain | Low | 1-3s acceptable; user expects data fetch latency |
| Plotly.js bundle size | Certain | Low | CDN caching after first load |

### 8.2 Open Questions

| Question | Impact | Resolution Path |
|----------|--------|-----------------|
| SEC EDGAR CIK mapping reliability? | Data availability | Test with edge cases (BRK-B, etc.) |
| yfinance rate limits? | Reliability | Monitor and add backoff if needed |
| Should we pre-populate default tickers? | UX | Seed DynamoDB in deployment |

### 8.3 Assumptions

- Single user, sporadic usage pattern
- US-listed stocks only (SEC EDGAR limitation)
- Browser supports ES6+ JavaScript
- No real-time data requirements (live fetch on interaction is sufficient)

---

*Document Status: DRAFT — Ready for Phase 4 (Project Structure)*
