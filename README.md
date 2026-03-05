# MBTA Data Warehouse

A production-grade data warehouse designed to collect, transform, and analyze transit data from the Massachusetts Bay Transportation Authority (MBTA). Built with PostgreSQL, Apache Airflow, SQLMesh, and Apache Superset to demonstrate modern data engineering architecture and best practices.

## Project Overview

This project builds a complete data platform that ingests real-time transit data from the [MBTA API v3](https://api-v3.mbta.com/docs/swagger/index.html#/), applies dimensional modeling principles, and exposes business intelligence dashboards for transit analytics.

**Data Source**: MBTA API v3 (real-time public transit data for Boston/Massachusetts)

**Use Cases**:
- Service reliability analysis (on-time performance by route and time-of-day)
- Ridership demand estimation (inferred from schedule density)
- Transit coverage analysis (neighborhood accessibility)
- Service disruption monitoring and alerting
- Historical trend analysis of route and schedule changes

## Architecture

```
┌─────────────┐
│  MBTA API   │
└──────┬──────┘
       │ Extract (Airflow Task)
       ↓
┌──────────────────────┐
│ PostgreSQL (Staging) │  ← Raw, unmodified API responses
└──────────┬───────────┘
           │ Load (Airflow Task)
           ↓
┌──────────────────────────┐
│  SQLMesh Transforms      │  ← Medallion Architecture
│  - Bronze (raw)          │    Staging → Cleansed → Mart
│  - Silver (cleansed)     │
│  - Gold (mart)           │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│ PostgreSQL (Warehouse)   │  ← Star schema with dimensions
│ - Fact Tables            │    and slowly changing dimensions
│ - Dimension Tables       │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│  Apache Superset         │  ← Interactive BI dashboards
│  - Service KPIs          │
│  - Trend analysis        │
│  - Drill-through views   │
└──────────────────────────┘
```

## Directory Structure

```
.
├── README.md                      # This file
├── index.md                       # Quick reference & project index
├── data/                          # Fixtures and reference data
│   └── CESReport.csv
├── lib/                           # Documentation & design decisions
│   ├── 1. foundation & env/
│   │   └── Postgres.md           # PostgreSQL setup & schema documentation
│   ├── 2. orchestration/         # Airflow DAGs, scheduling
│   ├── 3. transformation/        # SQLMesh models, data quality tests
│   ├── 4. data warehouse design/ # Star schema design, dimensional models
│   ├── 5. bi and visualization/  # Dashboard specs, metric definitions
│   └── 6. e2e/                   # Integration guide, deployment docs
├── dw/                            # Infrastructure-as-Code
│   └── docker-compose.yml         # Local stack (PostgreSQL, Airflow, Superset)
└── in/                            # Notebooks for exploration & validation
    ├── mbta_api_test.ipynb        # API exploration & schema discovery
    └── moodys.ipynb               # Sample analysis notebook
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Ingestion** | Python + Requests | API client with rate limiting & error handling |
| **Orchestration** | Apache Airflow | DAG-based scheduling, retry logic, SLAs |
| **Transformation** | SQLMesh | DataFrame-free SQL layer, CI/CD for data |
| **Storage** | PostgreSQL + TimescaleDB | OLAP warehouse with time-series extensions |
| **BI** | Apache Superset | Self-hosted dashboards with no cloud dependency |
| **Infrastructure** | Docker Compose | Reproducible local environment, no cloud required |

## Data Model

### Star Schema (Warehouse Layer)

The warehouse uses Kimball dimensional modeling with the following structure:

**Fact Tables**:
- `fct_schedule_events` — Route schedules with actual vs. expected times (SCD Type 2)
- `fct_service_alerts` — Disruptions and service warnings
- `fct_route_stops` — Route-stop relationships

**Dimension Tables**:
- `dim_routes` — Route metadata (agency, direction, URL, color)
- `dim_stops` — Stop locations (lat/lon, accessibility info, parent stations)
- `dim_dates` — Conformed date dimension for time-based joins
- `dim_services` — Service patterns (weekday/weekend/holiday schedules)

**SCD Type 2 Implementation**: Route and stop changes are tracked with valid_from/valid_to timestamps, enabling historical analysis.

## Key Features Demonstrated

### Data Engineering Fundamentals

- **Idempotent Ingestion**: All Airflow tasks are replayable—no duplicates on reruns
- **Data Quality**: SQLMesh tests enforce not-null, unique, and referential integrity constraints
- **Slowly Changing Dimensions**: Tracks route/stop metadata changes with effective dates
- **Incremental Loading**: Fact tables use incremental models to avoid full reprocessing
- **Error Handling**: Airflow retries, dead-letter queues, alerting on failures

### Production Readiness

- **Schema Versioning**: All schema changes tracked in `lib/4. data warehouse design/`
- **Secrets Management**: API keys and DB credentials via environment variables only
- **Monitoring**: Row count reconciliation between staging and warehouse layers
- **Documentation**: Column lineage, model logic, and business context embedded in SQLMesh
- **Reproducibility**: One `docker-compose up` command stands up the entire platform

### Portfolio-Quality Practices

- Git history shows iterative design (schema evolution, model refactoring)
- Clear commit messages linking analytics decisions to code changes
- Architecture diagrams (Mermaid) in design docs
- Trade-off discussions (why Kimball, why medallion, why PostgreSQL)
- Separate documentation for each phase of the data pipeline

## Current Status

**Phase 1 — Foundation & Environment ✅**
- PostgreSQL + Docker Compose setup
- Initial schema design (staging layer)
- Sample data loaded and validated

**Phase 2 — Orchestration 🔄 (In Progress)**
- Airflow DAG for MBTA data ingestion
- Task dependencies and error handling
- Schedule: daily full refresh + hourly incremental updates

**Phase 3 — Transformation**
- SQLMesh models (Bronze/Silver/Gold layers)
- Data quality tests
- Incremental load logic for fact tables

**Phase 4 — Data Warehouse Design**
- Star schema finalization
- SCD Type 2 dimension tracking
- Performance indexing and partitioning

**Phase 5 — BI & Visualization**
- Superset dashboard: Service Overview
- Route performance trending
- Accessibility drill-through

**Phase 6 — Capstone**
- End-to-end testing and validation
- Performance benchmarking
- Final documentation and GitHub release

## Design Decisions

### Why PostgreSQL?
- Self-hosted on local machine (no cloud costs)
- Strong SQL & window function support (needed for transit analytics)
- Easy to scale horizontally with replication if needed
- Rich ecosystem (PostGIS for location queries, TimescaleDB for time-series)

### Why Medallion Architecture?
- Clear separation of concerns (raw → trusted → refined)
- Easy to backfill or replay transformations
- Aligns with modern dbt/SQLMesh best practices
- Natural place to add data quality checks

### Why Kimball Dimensional Modeling?
- Optimized for BI queries (fast joins, intuitive for analysts)
- Slowly Changing Dimensions handle route/stop metadata changes elegantly
- Conformed dimensions (dates, services) enable cross-fact analysis
- Well-understood by BI tools (Superset, Tableau, etc.)

### Why Airflow (not cron)?
- Visual DAG monitoring and debugging
- Idempotent retries and backfilling
- Data lineage and SLA monitoring
- Community-standard for data engineering workflows

## Learning Resources Applied

- **Dimensional Modeling**: Kimball Group essays + "The Data Warehouse Toolkit"
- **SQL Optimization**: PostgreSQL EXPLAIN ANALYZE, query planning
- **Airflow Best Practices**: Idempotent operators, XCom passing, dynamic DAGs
- **Data Quality**: Elementary OS, dbt tests, custom SQL validators
- **BI Design**: Superset documentation, dashboard best practices

## Contact

Portfolio project built to demonstrate data engineering capabilities. Questions or feedback? Check the architecture docs in `/lib/` or review the Git commit history for design evolution.
