{{ config(materialized='table') }}

with tx as (
  select txn_id, user_id, status, created_at, destination_amount_usd
  from {{ ref('int_transactions_enriched') }}
  where status = 'COMPLETED' 
),

users_scd as (
  select user_id, kyc_level, effective_from, effective_to
  from {{ ref('int_users_scd2') }}
)

select
  t.txn_id,
  t.user_id,
  u.kyc_level,
  t.created_at,
  t.destination_amount_usd
from tx t
left join users_scd u
  on t.user_id = u.user_id
  and t.created_at >= u.effective_from
  and t.created_at < u.effective_to
