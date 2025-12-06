with raw as (
  select
    symbol,
    to_timestamp(open_time/1000) as open_time,
    to_timestamp(close_time/1000) as close_time,
    safe_cast(close as float) as close_price,
    current_timestamp() as loaded_at
  from {{ source('raw', 'rates') }}
)

select
  symbol,
  open_time,
  close_time,
  close_price,
  loaded_at
from raw
