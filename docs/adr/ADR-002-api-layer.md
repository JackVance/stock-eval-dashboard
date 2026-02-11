# ADR-002: API Layer Selection

## Status
Proposed

## Context
The static frontend needs to communicate with backend Lambda functions to fetch stock data. We need an API layer that routes requests, handles CORS, and stays within free tier for low usage.

Expected traffic: <100 requests/month during typical usage, potentially 500+ during active research sessions.

## Options Considered

| Option | Pros | Cons | Est. Monthly Cost |
|--------|------|------|-------------------|
| **API Gateway HTTP API** | 70% cheaper than REST, lower latency, simpler, 1M free requests/mo | Fewer features (no usage plans, caching, request validation) | $0 (free tier) |
| **API Gateway REST API** | More features, built-in caching, request/response transformation | More expensive ($3.50/M requests), more complex setup | $0 (free tier covers 1M) |
| **Lambda Function URLs** | Simplest, no API Gateway needed, free | No custom domain without CloudFront, limited routing | $0 |
| **AppSync (GraphQL)** | Flexible queries, real-time subscriptions | Overkill for this use case, learning curve | $0 (free tier) |

## Decision
**API Gateway HTTP API**

Rationale:
1. **Cost efficiency** — 70% cheaper than REST API if we exceed free tier
2. **Sufficient features** — We don't need REST API's caching (fetching live data), usage plans (single user), or request validation (simple inputs)
3. **Lower latency** — HTTP APIs have less overhead
4. **Free tier** — 1M requests/month for first 12 months, then $1.00/M requests
5. **CORS support** — Built-in, easy to configure
6. **JWT/Lambda authorizers** — Available if we add auth later (stretch goal)

API Structure:
```
GET /api/stock/{ticker}
    Query params: ?start_year=2020&end_year=2024
    Returns: { prices, financials, info, balance_sheet }

GET /api/tickers
    Returns: { tickers: ["AAPL", "MSFT", ...] }

POST /api/tickers
    Body: { ticker: "NVDA" }
    Returns: { success: true }

DELETE /api/tickers/{ticker}
    Returns: { success: true }
```

## Consequences

**Positive:**
- Minimal cost even beyond free tier
- Simple configuration via CDK
- Fast response times
- Easy CORS setup

**Negative:**
- No built-in response caching (but we're fetching live data anyway for MVP)
- No API key management (acceptable for public API)
- No request validation (will validate in Lambda)

**Future considerations:**
- If caching is added later, could use CloudFront in front of API Gateway
- Could add Lambda authorizer if authentication becomes needed
