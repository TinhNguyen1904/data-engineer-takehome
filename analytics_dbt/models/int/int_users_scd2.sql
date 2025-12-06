{{ config(materialized='incremental', unique_key='user_scd_id') }}

with source_users as (
  select
    user_id,
    kyc_level,
    created_at,
    updated_at
  from {{ ref('stg_users') }}
),

changes as (
  select
    user_id,
    kyc_level,
    created_at as effective_from,
    timestamp('9999-12-31') as effective_to,
    md5(concat(user_id, '-', kyc_level, '-', cast(updated_at as string))) as user_scd_id,
    updated_at
  from source_users
)

select * from changes

{% if is_incremental() %}
  where user_scd_id not in (select user_scd_id from {{ this }})
{% endif %}
