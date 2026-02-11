# Project Structure: Stock Evaluation Dashboard

## Directory Layout

```
stock-eval-dashboard/
│
├── docs/                          # Architecture documentation
│   ├── PROBLEM_STATEMENT.md       # Problem definition and requirements
│   ├── ARCHITECTURE.md            # System design and decisions
│   ├── PROJECT_STRUCTURE.md       # This file
│   └── adr/                       # Architecture Decision Records
│       ├── ADR-001-frontend-framework.md
│       ├── ADR-002-api-layer.md
│       ├── ADR-003-compute-lambda.md
│       ├── ADR-004-data-storage.md
│       ├── ADR-005-data-providers.md
│       └── ADR-006-static-hosting.md
│
├── src/
│   ├── legacy_dashboard.py        # Original Dash app (reference only)
│   ├── assets/
│   │   └── style.css              # Original CSS (reference only)
│   │
│   ├── frontend/                  # Static frontend application
│   │   ├── index.html             # Main HTML page
│   │   ├── css/
│   │   │   └── style.css          # buffalo_stone theme + layout
│   │   └── js/
│   │       ├── main.js            # Entry point, event handlers
│   │       ├── api.js             # API client (fetch wrapper)
│   │       ├── charts.js          # Plotly chart builders
│   │       └── state.js           # Ticker list, UI state
│   │
│   └── lambda/                    # Lambda function code
│       ├── handler.py             # Request routing, Lambda entry point
│       ├── models.py              # Data classes (PriceData, etc.)
│       ├── config.py              # Environment config, constants
│       │
│       └── providers/             # Data provider abstraction
│           ├── __init__.py
│           ├── base.py            # Protocol/interface definition
│           ├── yfinance_provider.py   # Prices, company info
│           ├── sec_edgar_provider.py  # Historical financials
│           └── composite.py       # Combines multiple providers
│
├── infra/                         # Infrastructure as Code
│   └── cdk/
│       ├── app.py                 # CDK app entry point
│       ├── cdk.json               # CDK configuration
│       ├── requirements.txt       # CDK Python dependencies
│       └── stacks/
│           ├── __init__.py
│           ├── storage_stack.py   # DynamoDB, ECR
│           ├── api_stack.py       # Lambda, API Gateway
│           └── frontend_stack.py  # S3, CloudFront
│
├── tests/
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_yfinance_provider.py
│   │   ├── test_sec_edgar_provider.py
│   │   └── test_handler.py
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   └── test_data_providers.py
│   └── fixtures/
│       ├── sample_yfinance_response.json
│       └── sample_sec_edgar_response.json
│
├── scripts/
│   ├── seed_tickers.py            # Populate default tickers in DynamoDB
│   ├── local_lambda.py            # Run Lambda locally for testing
│   └── build_frontend.py          # Bundle frontend for deployment
│
├── docker/
│   ├── Dockerfile                 # Lambda container image
│   └── requirements.txt           # Lambda Python dependencies
│
├── .github/
│   └── workflows/
│       └── deploy.yml             # CI/CD pipeline (future)
│
├── .gitignore
├── pyproject.toml                 # Python project config
├── Makefile                       # Common commands
└── README.md                      # Quick start guide
```

## Component Details

### Frontend (`src/frontend/`)

| File | Responsibility |
|------|----------------|
| `index.html` | Page structure with Plotly divs, form inputs, topnav |
| `css/style.css` | buffalo_stone theme (#696969 bg, white text), topnav, layout |
| `js/main.js` | DOM event handlers, orchestrates API calls and chart updates |
| `js/api.js` | `fetchStock(ticker, startYear, endYear)`, `getTickers()`, `saveTicker(ticker)` |
| `js/charts.js` | `renderPriceChart(data)`, `renderFinancialsTimeline(data)`, etc. |
| `js/state.js` | Current ticker, year range, saved tickers list |

**Plotly.js Loading:** Load from CDN in `index.html`:
```html
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
```

### Lambda (`src/lambda/`)

| File | Responsibility |
|------|----------------|
| `handler.py` | Lambda entry point, routes requests, returns JSON responses |
| `models.py` | `@dataclass` definitions matching API contract |
| `config.py` | DynamoDB table name, provider settings, timeouts |
| `providers/base.py` | `StockDataProvider` protocol definition |
| `providers/yfinance_provider.py` | Wraps yfinance for prices/info |
| `providers/sec_edgar_provider.py` | Fetches/parses SEC EDGAR filings |
| `providers/composite.py` | Combines providers (yfinance for prices, SEC for financials) |

**Handler Structure:**
```python
def main(event, context):
    path = event["requestContext"]["http"]["path"]
    method = event["requestContext"]["http"]["method"]

    if path.startswith("/api/stock/") and method == "GET":
        return handle_get_stock(event)
    elif path == "/api/tickers" and method == "GET":
        return handle_get_tickers(event)
    elif path == "/api/tickers" and method == "POST":
        return handle_add_ticker(event)
    elif path.startswith("/api/tickers/") and method == "DELETE":
        return handle_delete_ticker(event)
    else:
        return {"statusCode": 404, "body": "Not found"}
```

### Infrastructure (`infra/cdk/`)

| Stack | Resources |
|-------|-----------|
| `StorageStack` | DynamoDB table, ECR repository |
| `ApiStack` | Lambda function, API Gateway HTTP API |
| `FrontendStack` | S3 bucket, CloudFront distribution, bucket deployment |

**Stack Outputs:**
- `ApiStack.ApiUrl` → Used by frontend to make API calls
- `FrontendStack.DistributionUrl` → Public URL of the dashboard

### Tests (`tests/`)

| Directory | Purpose |
|-----------|---------|
| `unit/` | Test individual functions in isolation (mocked dependencies) |
| `integration/` | Test full request flows with real/mocked AWS services |
| `fixtures/` | Sample API responses for reproducible tests |

### Scripts (`scripts/`)

| Script | Usage |
|--------|-------|
| `seed_tickers.py` | `python scripts/seed_tickers.py` — adds default tickers |
| `local_lambda.py` | `python scripts/local_lambda.py` — test Lambda locally |
| `build_frontend.py` | `python scripts/build_frontend.py` — prep frontend for deploy |

## Makefile Commands

```makefile
.PHONY: install test lint deploy clean

install:                           ## Install all dependencies
	pip install -r docker/requirements.txt
	pip install -r infra/cdk/requirements.txt
	pip install pytest pytest-cov ruff

test:                              ## Run all tests
	pytest tests/ -v --cov=src/lambda

lint:                              ## Lint Python code
	ruff check src/ tests/

deploy:                            ## Deploy to AWS (prod)
	cd infra/cdk && cdk deploy --all

deploy-dev:                        ## Deploy to AWS (dev)
	cd infra/cdk && cdk deploy --all -c env=dev

local-api:                         ## Run Lambda locally
	python scripts/local_lambda.py

seed:                              ## Seed default tickers
	python scripts/seed_tickers.py

clean:                             ## Remove build artifacts
	rm -rf .pytest_cache __pycache__ .ruff_cache cdk.out

destroy:                           ## Tear down AWS resources
	cd infra/cdk && cdk destroy --all
```

## File Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Python modules | snake_case | `yfinance_provider.py` |
| Python classes | PascalCase | `class YFinanceProvider` |
| JavaScript files | camelCase | `main.js`, `apiClient.js` |
| CSS classes | kebab-case | `.price-chart`, `.topnav` |
| CDK stacks | PascalCase | `ApiStack`, `FrontendStack` |
| Test files | `test_*.py` | `test_handler.py` |

## Migration Notes

### From Legacy Dashboard

| Legacy | New Location | Changes |
|--------|--------------|---------|
| `src/legacy_dashboard.py` | `src/lambda/` + `src/frontend/` | Split into API + static frontend |
| `src/assets/style.css` | `src/frontend/css/style.css` | Add buffalo_stone theme, preserve topnav |
| `getData()` | `src/lambda/providers/` | Split by data source |
| `priceChart()` | `src/frontend/js/charts.js` | Convert Python Plotly → Plotly.js |
| `financialsTimeline()` | `src/frontend/js/charts.js` | Convert Python Plotly → Plotly.js |
| `printInfo()` | `src/frontend/js/charts.js` | Render as HTML instead of Markdown |
| `balanceSheetPlots()` | `src/frontend/js/charts.js` | Convert Python Plotly → Plotly.js |
| Dash callbacks | `src/frontend/js/main.js` | Convert to DOM event listeners |
| Dash dropdown | HTML `<select>` + `<datalist>` | Custom ticker input with autocomplete |

### Chart Function Mapping

| Legacy Function | Plotly.js Equivalent |
|-----------------|---------------------|
| `make_subplots(rows=2)` | `Plotly.newPlot(div, traces, {grid: {rows: 2}})` |
| `go.Scatter()` | `{type: 'scatter', x: [...], y: [...]}` |
| `go.Bar()` | `{type: 'bar', x: [...], y: [...]}` |
| `go.Sunburst()` | `{type: 'sunburst', labels: [...]}` |
| `px.line()` | `{type: 'scatter', mode: 'lines'}` |

---

*Document Status: COMPLETE — Ready for implementation*
