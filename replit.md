# Workspace

## Overview

pnpm workspace monorepo using TypeScript. Each package manages its own dependencies.
Also includes a standalone Streamlit Python data visualization dashboard.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)

## Streamlit Dashboard

Location: `artifacts/data-viz-dashboard/`
Run: `cd artifacts/data-viz-dashboard && streamlit run app.py --server.port 5000`
Workflow: "Data Viz Dashboard" (port 5000)

### Files
- `app.py` — Main entry point, navigation, sidebar, 6-page tab layout
- `data_processing.py` — File loading (CSV/Excel), cleaning, filtering, validation
- `visualizations.py` — 9 Plotly chart factory functions + CHART_REGISTRY
- `insights.py` — KPIs, trend analysis, category comparison, NL insights, outlier detection
- `utils.py` — Export helpers (CSV/Excel/PNG), session state, UI components
- `sample_data.csv` — 1,200-row generic demo dataset
- `.streamlit/config.toml` — Server and theme config
- `report/PROJECT_REPORT.md` — Full academic project report
- `README.md` — Installation and usage guide

### Python Dependencies
- streamlit, pandas, plotly, numpy, openpyxl, xlrd, kaleido

## Key Commands

- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- `pnpm --filter @workspace/api-server run dev` — run API server locally

See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details.
