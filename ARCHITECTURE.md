
Objective

Build a data pipeline from raw CSV → bronze (raw_rates) → silver (enriched, SCD2 users) → gold (marts) to answer:

1. Total trading volume (USD) by day/month/quarter.
2. Completed transactions grouped by `kyc_level`.
3. `kyc_level` must reflect the user status at the time the transaction occurred, not the current one (time-travel requirement → historized KYC with SCD Type 2).


1. Data Warehouse Choice

Recommendation: BigQuery (Google Cloud) or Snowflake.

Reasons (3–5 bullets):

* Excellent performance for analytical workloads over large time-based data (partition/cluster-friendly).
* Supports MERGE/UPSERT operations, suitable for incremental pipelines.
* Strong integration with dbt, Airflow, and BI tools (Looker / PowerBI).
* Scales automatically with separated storage/compute, suitable for fast-growing datasets.


2. Strategy for tracking `kyc_level` changes over time (Requirement 3)

Two possible approaches:

A. SCD Type 2 (recommended)

* When a user snapshot or update event occurs, insert a new record with `effective_from = updated_at` and `effective_to = '9999-12-31'`.
* On new change, update the previous record so `effective_to = new_effective_from`.
* Query using temporal join:

  sql
  tx.created_at BETWEEN effective_from AND effective_to
  
* Implemented via dbt incremental model + post-hook MERGE, or an Airflow job updating effective ranges.

B. Event-sourcing / audit log

* If the system provides user change streams (CDC), ingest change events and build SCD2 logic deterministically.

If only a current snapshot exists (`users.csv` latest state):

* Store snapshots daily/weekly.
* Compare snapshots (diff) → insert new SCD rows, update previous ones' `effective_to`.


3. dbt Materialization Strategy

| Layer                                       | Materialization                            | Reason                                       |
| ------------------------------------------- | ------------------------------------------ | -------------------------------------------- |
| `stg_*`                                     | view (dev) / table (prod optional) | simple transformations; views help debugging |
| `int_*` (users_scd2, transactions_enriched) | incremental table                      | growing data, allows MERGE-based upserts     |
| `marts/*`                                   | table (or incremental by partition)    | BI-heavy consumption; pre-aggregated results |
| `ephemeral`                                 | optional                                   | for small reusable logic                     |


4. Orchestration (Scheduling & Dependencies)

Tool Options: Apache Airflow or dbt Cloud.
Airflow recommended if full ingestion orchestration & notifications are needed.
dbt Cloud suitable for dbt-only scheduling.

Daily Workflow:

| Step | Task                       | Description                                                                                               |
| ---- | -------------------------- | --------------------------------------------------------------------------------------------------------- |
| A    | `ingest_rates` (Python)    | read `transactions.csv`, detect date range, fetch klines, store into `/output/raw_rates/` or cloud bucket |
| B    | `load_raw_to_dwh`          | load raw CSV/JSONL to bronze tables                                                                       |
| C    | `dbt run --models +stg_*`  | staging cleanup + typing                                                                                  |
| D    | `dbt run --models +int_*`  | build SCD2 users + enrich transactions                                                                    |
| E    | `dbt run --models marts.*` | build final marts for BI                                                                                  |
| F    | `dbt test`                 | fail → alerts                                                                                             |

Schedule: daily `0 1 * * *` (or hourly if intraday reporting needed).
Dependencies: A → B → C → D → E → F.


5. Notes on Rates & USD Conversion

* Assume USDT ≈ USD, so `<CURRENCY>USDT` price represents USD rate.
* If `destination_currency == USDT`, conversion rate = 1.
* If no `<CUR>USDT` exists:

  * try cross-rate via BTC or ETH, otherwise skip and log.
* Missing/unsupported coins must be flagged.


6. Data Quality & Tests

* PK uniqueness: `txn_id` unique, `user_id` unique in staging.
* `not_null`: `txn_id`, `user_id`, `created_at`.
* Validation rules: detect missing rates, failed USD conversions → export to error table/report.




