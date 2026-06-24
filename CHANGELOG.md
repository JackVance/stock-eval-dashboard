# Changelog

All notable changes to the Stock Evaluation Dashboard are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-02-16

Initial release.

### Added

- Interactive stock dashboard with 5 chart types: price (with 50/200-day MA), volume, financial timeline, company info, and balance sheet (bar + sunburst)
- Lambda backend (Python 3.11, ARM64) fetching live data from Yahoo Finance and SEC EDGAR
- DynamoDB-backed ticker list with add/remove support via API
- Static frontend served from S3 via CloudFront with custom domain and HTTPS
- AWS CDK infrastructure (3 stacks: Storage, Api, Frontend)
- Local development server (`make local-api`) with in-memory ticker storage
- Seed script for 20 default tickers
- Unit and integration test suite with moto-based DynamoDB tests
- Architecture documentation, ADRs, and deployment log
