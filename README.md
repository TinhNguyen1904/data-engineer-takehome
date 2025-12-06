# Data Engineer Takehome

Quickstart
1. Create a virtual environment and install dependencies

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Prepare the data

   * Place your `transactions.csv` and `users.csv` in the `examples/` folder (or upload to S3/GCS).
   * Update script arguments if using a custom path.

3. Ingest exchange rates

   ```bash
   python scripts/ingest_rates.py --transactions examples/transactions.csv --output output/raw_rates
   ```

   Output: `output/raw_rates/<PAIR>.jsonl`

4. Load raw files into your DWH

   * Example: load JSONL files into BigQuery table `raw.rates`.
   * You may use `gsutil` + `bq load` or Snowflake external stage depending on the warehouse.

5. Set up dbt and run pipelines

   ```bash
   cd analytics_dbt
   dbt deps
   dbt seed      # if seeds exist
   dbt run --models staging+
   dbt run --models int+
   dbt run --models marts+
   dbt test
   ```



