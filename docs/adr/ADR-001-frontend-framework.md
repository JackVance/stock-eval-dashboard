# ADR-001: Frontend Framework Selection

## Status
Proposed

## Context
The current Dash application renders HTML server-side on each interaction. We need a static frontend that can be hosted on S3/CloudFront and communicate with a backend API. The frontend must render Plotly charts (5 chart types) and handle user interactions (dropdown, slider, custom ticker input).

Key requirements:
- Render Plotly.js charts (the JavaScript library underlying Plotly Python)
- Handle form inputs and API calls
- Minimal bundle size (faster CDN delivery)
- Solo developer maintainability
- Preserve existing visual design

## Options Considered

| Option | Pros | Cons | Bundle Size |
|--------|------|------|-------------|
| **Vanilla JS + Plotly.js** | Zero framework overhead, smallest bundle, no build step needed, direct Plotly.js usage | More boilerplate for state management, manual DOM manipulation | ~3MB (Plotly.js only) |
| **React + react-plotly.js** | Component model, large ecosystem, good Plotly wrapper | Adds ~45KB (gzipped), requires build tooling, overkill for 1-page app | ~3.1MB |
| **Vue 3 + vue-plotly** | Lighter than React, good reactivity model | Smaller ecosystem, vue-plotly less maintained | ~3.05MB |
| **Preact + preact-plotly** | React API at 3KB, minimal overhead | Less ecosystem support, may need adapters | ~3.02MB |

## Decision
**Vanilla JS + Plotly.js** with a simple module structure.

Rationale:
1. **Plotly.js is the heavy dependency** (~3MB) — framework choice is noise in comparison
2. **Single-page application** with 5 charts and 3 inputs doesn't justify framework complexity
3. **No build step required** — can develop and deploy without webpack/vite configuration
4. **Direct Plotly.js API** — no wrapper translation, matches Plotly Python concepts 1:1
5. **Easier debugging** — no virtual DOM layer between code and browser
6. **Future-proof** — vanilla JS won't have breaking version upgrades

Structure:
```
frontend/
├── index.html          # Single HTML file
├── css/
│   └── style.css       # Migrated from assets/style.css + buffalo_stone theme
├── js/
│   ├── main.js         # Entry point, event handlers
│   ├── api.js          # API client module
│   ├── charts.js       # Plotly chart rendering functions
│   └── state.js        # Simple state management (ticker list, current selection)
└── lib/
    └── plotly.min.js   # Or load from CDN
```

## Consequences

**Positive:**
- Smallest possible bundle beyond Plotly itself
- No build tooling to maintain
- No framework version upgrades to track
- Direct browser debugging

**Negative:**
- More verbose DOM manipulation code
- No component reusability (acceptable for 1-page app)
- Manual state synchronization (mitigated by simple state needs)

**Risks:**
- If app grows significantly, may want to reconsider (but that's a stretch goal problem)

**Mitigation:**
- Structure JS into clear modules from the start
- Keep chart functions pure (data in, Plotly config out)
