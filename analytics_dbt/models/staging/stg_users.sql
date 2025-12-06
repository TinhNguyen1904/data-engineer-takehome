with raw as (
  select
    cast(user_id as string) as user_id,
    upper(trim(kyc_level)) as kyc_level,
    cast(created_at as timestamp) as created_at,
    cast(updated_at as timestamp) as updated_at
  from {{ source('raw', 'users') }}
)

select
  user_id,
  kyc_level,
  created_at,
  updated_at,
  current_timestamp() as loaded_at
from raw
