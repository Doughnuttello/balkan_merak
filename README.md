# Balkan Trends — Architecture

## 1. Purpose

Balkan Trends is a small data platform that retrieves public statistical data from the **Eurostat API**, stores it in **DuckDB**, and transforms it into analytical datasets using a simple medallion-style structure.

The project is designed to be:

* Open source
* Low-cost / free to operate
* Fully automated through GitHub Actions
* Reproducible
* Simple enough to maintain as a personal project

## 2. Architecture

```text
                    ┌──────────────────┐
                    │    Eurostat API  │
                    └────────┬─────────┘
                             │
                        API ingestion
                             │
                             ▼
                    ┌──────────────────┐
                    │      DuckDB      │
                    │                  │
                    │       SRC        │
                    │ (raw-ish source) │
                    └────────┬─────────┘
                             │
                         transform
                             │
                             ▼
                    ┌──────────────────┐
                    │      STG         │
                    │    cleaned/      │
                    │    standardized  │
                    └────────┬─────────┘
                             │
                         transform
                             │
                             ▼
                    ┌──────────────────┐
                    │      MART        │
                    │    analytical    │
                    │    datasets      │
                    └──────────────────┘


             ┌───────────────────────────────┐
             │       GitHub Actions          │
             │                               │
             │  1. Scheduled ingestion       │
             │  2. Scheduled transformation  │
             └───────────────────────────────┘
```

## 3. Components

### Eurostat API

The source system.

Eurostat provides public statistical datasets through an API. The project will retrieve only the datasets required for the Balkan Trends models.

### GitHub Actions

GitHub Actions provides execution and scheduling.

Two workflows will initially be used:

1. **Ingestion workflow**

   * Triggered on a schedule
   * Calls the Eurostat API
   * Loads data into DuckDB `src` tables

2. **Transformation workflow**

   * Triggered on a schedule
   * Reads `src` tables
   * Builds `stg` tables (DW method to be added later)
   * Builds `mart` tables (probably Dimensional Model)

### DuckDB

DuckDB is the analytical database and transformation engine.

It will contain three logical layers:

```text
src
 └── minimally transformed source data

stg
 └── cleaned and standardized data

mart
 └── analytical datasets ready for consumption
```

The DuckDB database is the persistent data store for the project.

## 4. Data Flow

### Ingestion

```text
Eurostat API
     │
     ▼
Python ingestion code
     │
     ▼
DuckDB
     │
     ▼
src tables
```

The `src` layer remains close to the structure returned by Eurostat, adding only the metadata necessary for ingestion and traceability.

### Transformation

```text
src
 │
 ▼
stg
 │
 ▼
mart
```

The staging layer handles cleaning, type conversion, naming conventions and normalization.

The mart layer contains business-oriented datasets designed for analysis.

## 5. Initial Data Domains

The first version will focus on several EU Balkan contries and their trends (Bulgaria, Romania, Greece). With time progressing, more will be added.

Potential domains include:

* Population
* Employment/Unemployment
* GDP
* Inflation
* Migration
* Wages vs Living standards

The exact Eurostat datasets will be selected separately.

## 6. Scheduling

The initial scheduling model is:

```text
Daily
  │
  ├── Ingestion
  │
  └── Transformation
```

The ingestion workflow should complete successfully before transformation begins.
The transformation workflow should be dependent on successful ingestion rather than simply running at a fixed time.

## 7. Design Principles

### Keep the stack small

The initial implementation intentionally uses only:

* Eurostat
* Python
* DuckDB
* GitHub Actions

No separate data warehouse, object store, Spark cluster, orchestration platform or cloud database is required initially.

### Keep source data reproducible

Each ingestion should record enough metadata to determine:

* when the data was retrieved
* which Eurostat dataset was used
* which parameters/filters were used
* when the source data was last updated

### Separate ingestion from transformation

API interaction belongs to the ingestion layer.

SQL/data modelling belongs to the transformation layer.

This makes the transformation logic independently testable and reproducible.

### Prefer incremental processing where practical

The project should avoid unnecessarily rebuilding/overwriting.

Where Eurostat metadata allows it, ingestion and transformations should process only the required datasets and dimensions.

## 8. Target State

The desired end state is:

```text
                   Eurostat
                      │
                      ▼
                GitHub Actions
                      │
                  ingestion
                      │
                      ▼
                   DuckDB
                      │
              ┌───────┼───────┐
              ▼       ▼       ▼
             SRC     STG     MART
                              │
                              ▼
                          BI/Analysis
```

The architecture should remain simple enough that the entire pipeline can be understood and reproduced from the GitHub repository.
