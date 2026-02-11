# ADR-006: Static Frontend Hosting

## Status
Proposed

## Context
The frontend is a static single-page application (HTML, CSS, JS, Plotly.js) that needs to be served to browsers. It must communicate with the API Gateway backend and load quickly despite the large Plotly.js library (~3MB).

Requirements:
- Low latency globally (or at least in primary region)
- HTTPS required for modern browser APIs
- Custom domain optional but nice
- Minimal cost

## Options Considered

| Option | Pros | Cons | Est. Monthly Cost |
|--------|------|------|-------------------|
| **S3 + CloudFront** | CDN caching, HTTPS, custom domain, free tier | Slight setup complexity | $0 (free tier: 1TB/mo) |
| **S3 static hosting only** | Simplest | HTTP only (no HTTPS), no CDN caching, no custom domain | $0 |
| **Amplify Hosting** | Managed, CI/CD built-in, HTTPS | Less control, potential cost surprises | $0 (free tier) |
| **GitHub Pages** | Free, easy | No direct AWS integration, limited customization | $0 |

## Decision
**S3 + CloudFront**

Rationale:
1. **HTTPS included** — Required for modern web APIs, no extra cost
2. **CDN caching** — Plotly.js (3MB) cached at edge, fast repeat loads
3. **Free tier generous** — 1TB data transfer/month, 10M requests
4. **Custom domain ready** — Can add later with Route 53 or external DNS
5. **Native CDK support** — `BucketDeployment` + `Distribution` patterns well-documented
6. **Cache invalidation** — Can invalidate on deploy for instant updates

Configuration:
```
S3 Bucket (private, not public website hosting)
├── index.html
├── css/style.css
├── js/*.js
└── error.html

CloudFront Distribution
├── Origin: S3 bucket (OAC access)
├── Default root object: index.html
├── Cache policy: CachingOptimized for static assets
├── Error pages: 404 → /index.html (SPA routing)
└── Price class: PriceClass_100 (US, Canada, Europe only — cheapest)
```

## Consequences

**Positive:**
- Fast global delivery via CDN edge caching
- HTTPS with AWS-managed certificate
- Plotly.js cached at edge after first load
- Easy custom domain addition later
- Integrates cleanly with API Gateway (same-origin or CORS)

**Negative:**
- CloudFront propagation takes ~15 min for new distributions
- Cache invalidation required on each deploy (or use versioned filenames)
- Slight complexity vs raw S3

**Cost breakdown at expected usage:**
| Component | Free Tier | Expected Usage | Cost |
|-----------|-----------|----------------|------|
| S3 storage | 5GB | <1MB | $0 |
| S3 requests | 20K GET | <1K/mo | $0 |
| CloudFront transfer | 1TB | <1GB/mo | $0 |
| CloudFront requests | 10M | <10K/mo | $0 |

**Total: $0/month**
