# Agent-callable app research — case study

This is a self-contained case-study deliverable for the Product Ops Intern take-home.

## View it

Open `index.html` in any modern browser. No build step, server, or credentials are needed.

## Run the research pipeline

```powershell
python research_agent.py --input apps.js --output research-run.json --sample 12
```

Add `--check-sources` to HTTP-check every first-party starting point before a review run.

The script is deliberately dependency-free. It parses the 100-app corpus, validates the required evidence fields, calculates the dashboard metrics, draws a stratified verification sample, optionally checks source availability, and emits a machine-readable run report. It is designed to sit behind a browsing/MCP research worker: source URLs and structured claims are stored separately so a worker can refresh a source without changing the presentation layer.

### What the agent does

1. Normalizes each app into a strict evidence record.
2. Applies deterministic readiness rules (credentials + public docs + usable API).
3. Flags ambiguous access language for reviewer attention.
4. Stratifies a verification queue across category, access, and verdict.
5. Produces the metrics consumed by the page.

### Where a person remains in the loop

The agent cannot infer a commercial contract from a pricing page or safely guess whether an OAuth app can be approved by an enterprise tenant. The `verify` records capture those decisions and corrections. In a production run, a browser/MCP worker would fetch official docs, attach excerpts/timestamps, and route ambiguous rows to a reviewer.

## Evidence standard

Every row links to first-party developer documentation. “Self-serve” means a developer can create credentials without a sales or partner approval step; it does not promise that every production use is free.

## Deploy

Deploy the `composio-case-study` directory on GitHub Pages, Netlify, or Vercel as a static site. The file is intentionally standalone for easy review.
