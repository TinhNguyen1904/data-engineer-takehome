with tx as (
  select * from {{ ref('stg_transactions') }}
),

rates as (
  select
    symbol,
    open_time,
    close_price
  from {{ ref('stg_rates') }}
),

tx_pairs as (
  select
    t.*,
    upper(concat(destination_currency, 'USDT')) as pair
  from tx t
)


select
  t.txn_id,
  t.user_id,
  t.status,
  t.source_currency,
  t.destination_currency,
  t.created_at,
  t.destination_amount,
  r.close_price as rate_to_usdt,
  safe_cast(t.destination_amount as numeric) * safe_cast(r.close_price as numeric) as destination_amount_usd
from tx_pairs t
left join lateral (
  select close_price
  from rates r
  where r.symbol = t.pair
    and r.open_time <= t.created_at
  order by r.open_time desc
  limit 1
) r on true
