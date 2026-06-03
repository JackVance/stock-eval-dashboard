# CLAUDE.md — Stock Evaluation Dashboard

Serverless stock analysis dashboard: CloudFront + S3 frontend, Lambda + API Gateway backend, DynamoDB storage. Live at https://stocks.jhviv.com.

## Stack

- **Frontend:** Vanilla HTML/CSS/JS + Plotly.js, served from S3 via CloudFront
- **Backend:** Python 3.11 Lambda (ARM64), HTTP API Gateway
- **Data:** DynamoDB (ticker list), yfinance (prices/info), SEC EDGAR (10+ yr financials)
- **Infra:** AWS CDK (Python), 3 stacks: Storage, Api, Frontend
- **Domain:** Route 53 + ACM certificate (us-east-1)

## Project Structure

```
src/frontend/           # Static files: index.html, css/, js/ (main, api, charts, state, config)
src/lambda/             # Lambda code: handler.py, config.py, models.py
src/lambda/providers/   # Data providers: base.py, yfinance_provider.py, sec_edgar_provider.py, composite.py
infra/cdk/              # CDK app: app.py + stacks/ (storage, api, frontend)
infra/cdk/stacks/       # StorageStack, ApiStack, FrontendStack
tests/unit/             # test_handler.py, test_models.py, test_composite_provider.py
tests/integration/      # test_handler_dynamodb.py (moto-based)
scripts/                # seed_tickers.py, local_lambda.py
docs/                   # ARCHITECTURE.md, PROJECT_STRUCTURE.md, adr/, DEPLOYMENT_LOG.md
```

## Commands

```bash
# Install
pip install -e ".[dev,cdk]"

# Lint
make lint                    # ruff check + ruff format --check + mypy

# Test
make test                    # pytest with coverage

# Run locally
make local-api               # http://localhost:3000 — serves frontend + proxies API

# Deploy (all 3 stacks)
cd infra/cdk && cdk deploy --all --require-approval never

# Seed tickers
python scripts/seed_tickers.py

# Destroy
make destroy
```

## Architecture Summary

```
Route 53 → CloudFront → S3 (static frontend)
                           ↓ fetch /api/*
                     API Gateway HTTP API
                           ↓
                     Lambda (Python 3.11, ARM64)
                           ↓
              ┌────────────┼────────────┐
              ↓            ↓            ↓
          yfinance    SEC EDGAR     DynamoDB
       (prices/info) (financials) (ticker list)
```

API routes: `GET /api/stock/{ticker}`, `GET /api/tickers`, `POST /api/tickers`, `DELETE /api/tickers/{ticker}`

## Gotchas

- **config.js deploy ordering:** FrontendStack's `DeployConfig` overwrites the dev `localhost:3000` `config.js` that `DeployFrontend` uploads. `add_dependency` only enforces order *if both run* — CDK skips `DeployConfig` when its source content is unchanged (the `api_url` alone is stable across deploys), leaving the localhost URL live on S3 and breaking the dashboard. Fix: hash the entire `src/frontend/` folder into `DeployConfig`'s source content (a `// build {hash}` comment), so any frontend change forces both deployments to re-run together.
- **ARM64 bundling on Windows:** pip in the SAM Docker image can't compile numpy from source. Bundling uses `--platform manylinux2014_aarch64 --only-binary=:all:` and `platform="linux/arm64"` on BundlingOptions.
- **`cp -r` not `cp -au`:** Archive copy fails on Docker volume mounts from Windows. The bundling command uses `cp -r`.
- **SEC EDGAR rate limits:** 10 req/sec. The provider respects this, but bulk testing can trigger 429s.
- **yfinance silent failures:** Returns empty DataFrames instead of raising exceptions for invalid tickers. The composite provider checks for empty data.
- **CORS wildcard:** API Gateway `allow_origins=["*"]` — works but should be restricted to the CloudFront domain before adding auth.
- **CDK bootstrap required:** First deploy to any account/region needs `cdk bootstrap` first.

## Current State

- **Deployed and working** at https://stocks.jhviv.com (commit 84c7d5a)
- 20 tickers seeded in DynamoDB
- All 5 chart types functional: price, volume, financial timeline, company info, balance sheet
- Tests passing (unit + integration with moto)
- Estimated cost: $0/month (free tier)

## Do Not

- **Do not run `cdk deploy` without explicit user confirmation** — costs real money and takes minutes
- **Do not change the DynamoDB schema** without updating both `models.py` and `storage_stack.py`
- **Do not push to main without tests passing** — `make lint && make test`
- **Do not remove the frontend-folder hash in `DeployConfig`'s source** in `frontend_stack.py` — without it CDK skips `DeployConfig` and the dev localhost `config.js` stays live on S3. The `add_dependency` line still matters for ordering but isn't enough on its own.
- **Do not change Lambda architecture** from ARM64 without updating bundling options
