{{config(
    alias='users',
    table_type='delta'
)}}

SELECT DISTINCT name, value
FROM {{ source('silver', 'users') }}
