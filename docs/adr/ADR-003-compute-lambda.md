# ADR-003: Compute Layer — Lambda Configuration

## Status
Proposed

## Context
Backend logic must fetch stock data from multiple sources (yfinance for prices, SEC EDGAR for financials), transform it, and return JSON to the frontend. The compute layer must handle Python dependencies including `yfinance`, `pandas`, and SEC EDGAR parsing libraries.

Key constraints:
- yfinance + pandas + dependencies = ~100MB+ uncompressed
- Lambda deployment package limit: 50MB zipped, 250MB unzipped
- Lambda container image limit: 10GB
- Cold start latency matters for sporadic usage

## Options Considered

| Option | Pros | Cons | Est. Monthly Cost |
|--------|------|------|-------------------|
| **Lambda + Lambda Layer** | Standard approach, shared layer across functions | 250MB limit may be tight, layer management | $0 (free tier: 1M requests, 400K GB-sec) |
| **Lambda Container Image** | 10GB limit, Docker-based, full control | Larger cold starts (1-3s), ECR storage cost | ~$0.10/mo (ECR) |
| **Fargate** | No package limits, persistent containers | Minimum cost ~$10/mo even idle | $10+/mo |

## Decision
**Lambda with Container Image**

Rationale:
1. **Package size freedom** — 10GB limit vs 250MB, no stress about dependency bloat
2. **Reproducible builds** — Dockerfile defines exact environment
3. **Local testing** — Run same container locally with `docker run`
4. **Future-proof** — Easy to add more dependencies (SEC EDGAR parsers, ML libraries)
5. **Acceptable cold starts** — 1-3s is fine for sporadic usage; user expects data fetch latency anyway
6. **ECR cost negligible** — ~$0.10/mo for a single image

Container structure:
```dockerfile
FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/lambda/ ${LAMBDA_TASK_ROOT}/

CMD ["handler.main"]
```

Lambda configuration:
- **Memory**: 512MB (pandas needs headroom)
- **Timeout**: 30 seconds (external API calls can be slow)
- **Architecture**: arm64 (20% cheaper, Graviton2)

## Consequences

**Positive:**
- No dependency size constraints
- Consistent local and deployed environment
- Easy to add heavy libraries later (lxml, beautifulsoup for SEC parsing)
- arm64 is cheaper and often faster for Python

**Negative:**
- Requires Docker for local development
- ECR adds small monthly cost (~$0.10)
- Cold starts slightly longer than zip deployment (1-3s vs <1s)

**Mitigations:**
- Keep container image lean — only include required dependencies
- Use multi-stage Docker builds to minimize image size
