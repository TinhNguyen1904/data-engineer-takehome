{{ config(materialized='table') }}

with enriched as (
  select * from {{ ref('int_transactions_enriched') }}
)

select
  date_trunc('day', created_at) as day,
  sum(destination_amount_usd) as total_volume_usd,
  count(*) as transactions_count
from enriched
group by 1
order by 1
