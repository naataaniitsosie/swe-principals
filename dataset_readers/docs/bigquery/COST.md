# BigQuery Cost Analysis

## Free Tier

| Resource | Free allowance |
|---|---|
| Query processing | **1 TB / month** (resets monthly) |
| Storage | 10 GB / month |
| BigQuery Sandbox | Available; tables auto-expire after 60 days |

The 1 TB free tier is generous — a typical filtered query for this project (specific repos + specific event types) costs 1–5 GB of scan, meaning hundreds of queries per month before charges kick in.

## On-Demand Pricing (US regions)

**$6.25 per TB scanned** (10 MB minimum per table touched).

## Estimated Query Costs — 2023–2025

Each `githubarchive.day` table is roughly **7–10 GB**. A three-year range spans ~1 095 daily tables, totalling ~8–11 TB unfiltered.

| Query scope | Bytes scanned | Estimated cost |
|---|---|---|
| Single day, unfiltered | ~8 GB | < $0.01 (within free tier) |
| Single month, unfiltered | ~230 GB | ~$1.40 |
| Full 2023–2025, unfiltered | ~10 TB | ~$60 |
| Full 2023–2025, **filtered** (repo list + event types, projected columns) | ~0.5–2 TB | **$0–$12.50** |
| Full 2023–2025, filtered, within monthly free tier | ≤ 1 TB | **$0** |

The key levers are **column projection** (avoid `SELECT *`) and **row filtering** (`repo.name IN (...)` + `type IN (...)`), which together cut scan volume by 60–80 %.

## Recommendations

- Use the BigQuery console's **dry-run** (query validator) to see bytes-to-be-scanned before running.
- Materialize results into a project-owned table once — avoid re-scanning the archive for the same date range.
- For sustained high-volume use, evaluate BigQuery **Editions** pricing or a **flat-rate slot reservation**.
