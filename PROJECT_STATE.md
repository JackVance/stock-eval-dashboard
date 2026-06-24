# Project State — Stock Evaluation Dashboard

**As of:** 2026-06-24
**Commit:** 6a784be (`docs: refresh README and add screenshot and guides`)
**Live URL:** https://stocks.jhviv.com

## What's Done

- Full serverless deployment on AWS (3 CDK stacks: Storage, Api, Frontend)
- Lambda backend (Python 3.11, ARM64) with yfinance + SEC EDGAR providers
- Static frontend with 5 interactive Plotly chart types
- DynamoDB ticker persistence with add/remove API
- CloudFront + Route 53 + ACM for HTTPS on custom domain
- 20 default tickers seeded
- Weekly top-N market-cap ticker refresh (`refresh_top_tickers.py` Lambda)
- Standalone "about" page describing the dashboard
- Unit tests (handler, models, composite provider) + integration tests (DynamoDB via moto)
- Linting pipeline: ruff + mypy
- Local dev server (`make local-api`) with in-memory ticker storage
- Architecture documentation (ARCHITECTURE.md, 6 ADRs, PROJECT_STRUCTURE.md)
- Deployment log documenting all issues encountered during first deploy

## In Progress

Nothing currently in progress.

## Not Started

- CI/CD pipeline (GitHub Actions)
- API response caching (Lambda or CloudFront level)
- Restrict CORS to CloudFront domain (currently wildcard `*`)
- Authentication / API key protection
- Error monitoring / alerting (CloudWatch alarms)
- End-to-end tests
- Frontend build pipeline (minification, bundling)
- Multi-environment support (dev stack)

## Known Issues

1. **CORS wildcard** — `allow_origins=["*"]` in API Gateway. Functional but should be locked down before adding any authentication.
2. **No API caching** — Every request hits yfinance + SEC EDGAR live. SEC EDGAR data rarely changes; price data changes daily. Lambda cold starts add 1-3s.
3. **No CI/CD pipeline** — Deploys are manual via `cdk deploy`. No automated testing on push.
4. **yfinance dependency risk** — Unofficial library that scrapes Yahoo Finance. Can break without warning if Yahoo changes their API.
5. **SEC EDGAR CIK mapping** — Some tickers (especially those with special characters like BRK-B) may not resolve correctly in the SEC EDGAR CIK lookup.

## Next Steps (Priority Order)

1. Restrict CORS origins to the CloudFront domain
2. Add CloudFront-level caching for API responses (TTL: 5 min for prices, 24h for financials)
3. Set up GitHub Actions for lint + test on PR, deploy on merge to main
4. Add CloudWatch alarms for Lambda errors and API Gateway 5xx rates
