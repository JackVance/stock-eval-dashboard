# Stock Evaluation Dashboard

A serverless stock evaluation dashboard that displays interactive Plotly charts for stock analysis. Migrated from a Dash/EC2 architecture to static frontend + Lambda backend on AWS.

## Features

- **Price Charts**: Historical close prices with 50/200-day moving averages
- **Volume Analysis**: Daily trading volume with up/down day coloring
- **Financial Timeline**: 10+ years of key financial metrics (via SEC EDGAR)
- **Company Info**: Sector, industry, P/E ratios, business summary
- **Balance Sheet**: Bar chart and sunburst visualization of assets/liabilities

## Architecture

```
CloudFront → S3 (static frontend)
                ↓
         API Gateway HTTP API
                ↓
         Lambda (Python container)
                ↓
    ┌───────────┴───────────┐
    ↓                       ↓
 yfinance              SEC EDGAR
(prices, info)      (10+ yr financials)
```

**Estimated cost**: ~$0/month (AWS free tier)

## Prerequisites

- Python 3.11+
- AWS CLI configured with credentials
- Docker (for Lambda container builds)
- Node.js (for AWS CDK)

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd stock-eval-dashboard

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,cdk]"

# Deploy to AWS
cd infra/cdk
cdk bootstrap  # First time only
cdk deploy --all

# Seed default tickers
python scripts/seed_tickers.py
```

## Development

```bash
# Run linting
make lint

# Run tests
make test

# Test Lambda locally
make local-api

# Build Lambda container
make build-lambda
```

## Project Structure

```
├── src/
│   ├── frontend/          # Static HTML/CSS/JS
│   └── lambda/            # Python Lambda functions
├── infra/cdk/             # AWS CDK infrastructure
├── tests/                 # Unit and integration tests
├── scripts/               # Development utilities
└── docs/                  # Architecture documentation
```

## Documentation

- [Problem Statement](docs/PROBLEM_STATEMENT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Project Structure](docs/PROJECT_STRUCTURE.md)
- [Architecture Decision Records](docs/adr/)

## License

MIT
