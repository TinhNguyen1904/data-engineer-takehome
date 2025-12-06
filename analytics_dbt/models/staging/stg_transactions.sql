with raw as (
  select
    cast(txn_id as string) as txn_id,
    cast(user_id as string) as user_id,
    upper(trim(status)) as status,
    upper(trim(source_currency)) as source_currency,
    upper(trim(destination_currency)) as destination_currency,
    cast(created_at as timestamp) as created_at,
    cast(source_amount as double) as source_amount,
    cast(destination_amount as double) as destination_amount
  from {{ source('raw', 'transactions') }}
)

select
  txn_id,
  user_id,
  status,
  source_currency,
  destination_currency,
  created_at,
  source_amount,
  destination_amount,
  current_timestamp() as loaded_at
from raw
