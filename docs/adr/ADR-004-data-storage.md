# ADR-004: Data Storage — Ticker Persistence

## Status
Proposed

## Context
The application needs to remember previously searched tickers across sessions. This is the only persistent state required for MVP (no caching). The data is simple: a list of ticker symbols that the user has searched.

Requirements:
- Persist ticker list across browser sessions
- Single user, no multi-tenancy
- Very low write volume (new ticker added occasionally)
- Very low read volume (load ticker list on page load)

## Options Considered

| Option | Pros | Cons | Est. Monthly Cost |
|--------|------|------|-------------------|
| **DynamoDB (on-demand)** | Serverless, free tier (25GB, 25 WCU/RCU), pay-per-request | Slight overkill for simple list | $0 (free tier) |
| **S3 (JSON file)** | Simplest, just read/write a file | No atomic updates, potential race conditions | $0 (free tier) |
| **Parameter Store** | Free, good for config | 4KB limit per parameter, not designed for this | $0 |
| **Browser localStorage** | Zero infrastructure | Doesn't persist across devices/browsers | $0 |

## Decision
**DynamoDB with on-demand capacity**

Rationale:
1. **Free tier generous** — 25GB storage, 25 RCU/WCU perpetually free (not just 12 months)
2. **Atomic operations** — Can safely add/remove tickers without race conditions
3. **Future-ready** — If caching is added later, same table can store cached data
4. **CDK native** — Easy to define in infrastructure code
5. **On-demand pricing** — No capacity planning, pay only for actual requests

Table design:
```
Table: StockDashboard
├── PK: "TICKERS"           # Partition key (singleton for ticker list)
│   └── tickers: ["AAPL", "MSFT", ...]  # String set attribute
│
└── (Future: cached stock data)
    PK: "STOCK#AAPL"
    SK: "2024-01-15"
    data: { ... }
```

For MVP, we only need the ticker list. Single item, updated via SET operations.

## Consequences

**Positive:**
- Zero cost at expected usage
- Atomic set operations (add/remove ticker)
- Scales automatically if usage grows
- Same table can hold cache data later

**Negative:**
- Slightly more complex than S3 JSON file
- Requires IAM permissions for Lambda

**Access patterns:**
| Operation | DynamoDB Call |
|-----------|---------------|
| Get all tickers | `GetItem(PK="TICKERS")` |
| Add ticker | `UpdateItem` with `ADD tickers :ticker` |
| Remove ticker | `UpdateItem` with `DELETE tickers :ticker` |
