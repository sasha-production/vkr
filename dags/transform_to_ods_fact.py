from datetime import datetime, timedelta

from airflow import DAG
# from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.operators.empty import EmptyOperator


DAG_ID = "dag_transform_to_ods_fact"
DEFAULT_ARGS = {
    "owner": "sasha",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

POSTGRES_CONN_ID = "postgres_dwh"

# --- Шаг 1: заполнение ODS‑таблиц ---
CREATE_ODS_DATA_SQL = """
-- ОБНОВЛЕНИЕ КЛИЕНТОВ
TRUNCATE TABLE dwh.ods_clients CASCADE;

INSERT INTO dwh.ods_clients (
    client_code,
    client_name,
    region,
    segment,
    email,
    valid_from,
    valid_to,
    is_current,
    load_dttm
)
SELECT
    client_code,
    client_name,
    region,
    segment,
    email,
    CURRENT_DATE,
    '9999-12-31',
    TRUE,
    NOW()
FROM (
    SELECT DISTINCT
        client_code,
        client_name,
        region,
        segment,
        email
    FROM dwh.raw_clients_crm
) t;

-- ОБНОВЛЕНИЕ ТОВАРОВ (упрощённо)
TRUNCATE TABLE dwh.ods_products CASCADE;

INSERT INTO dwh.ods_products (
    product_code,
    product_name,
    category,
    brand,
    analog_eu_brand,
    technical_params,
    country_of_prod,
    valid_from,
    valid_to,
    is_current,
    load_dttm
)
SELECT
    product_code,
    product_name,
    NULL AS category,
    'ELMI' AS brand,
    NULL AS analog_eu_brand,
    NULL AS technical_params,
    NULL AS country_of_prod,
    CURRENT_DATE,
    '9999-12-31',
    TRUE,
    NOW()
FROM (
    SELECT DISTINCT
        product_code,
        product_name
    FROM dwh.raw_sales
    ORDER BY product_code,product_name
) t;

-- ОБНОВЛЕНИЕ СКЛАДОВ
TRUNCATE TABLE dwh.ods_warehouses CASCADE;

INSERT INTO dwh.ods_warehouses (
    warehouse_code,
    warehouse_name,
    city,
    country,
    warehouse_type,
    valid_from,
    valid_to,
    is_current,
    load_dttm
)
SELECT
    warehouse_code,
    warehouse_name,
    city,
    country,
    warehouse_type,
    CURRENT_DATE,
    '9999-12-31',
    TRUE,
    NOW()
FROM (
    SELECT DISTINCT
        warehouse_code,
        warehouse_name,
        city,
        country,
        warehouse_type
    FROM dwh.raw_warehouses_excel
) t;
"""

# --- Шаг 2: заполнение fact_sales ---
CREATE_FACT_SALES_SQL = """
-- Очистка за сегодня (если делаем full refresh daily)
DELETE FROM dwh.fact_sales
WHERE date_id = CURRENT_DATE;

INSERT INTO dwh.fact_sales (
    date_id,
    client_id,
    product_id,
    warehouse_id,
    quantity,
    price,
    amount,
    doc_type,
    doc_id,
    load_dttm
)
SELECT
    COALESCE(d.date_id, '9999-12-31'::DATE),
    c.client_id,
    p.product_id,
    w.warehouse_id,
    s.quantity,
    s.price,
    s.amount,
    'sale' AS doc_type,
    s.doc_id,
    NOW()
FROM dwh.raw_sales s
LEFT JOIN dwh.ods_clients c
    ON s.client_code = c.client_code
LEFT JOIN dwh.ods_products p
    ON s.product_code = p.product_code
LEFT JOIN dwh.ods_warehouses w
    ON s.warehouse_code = w.warehouse_code
LEFT JOIN dwh.dim_date d
    ON s.doc_date = d.date_id
ORDER BY d.date_id;
"""

with DAG(
    DAG_ID,
    default_args=DEFAULT_ARGS,
    description="Transform raw data into ODS and fact_sales in DWH",
    catchup=False,
) as dag:
    start = EmptyOperator(
        task_id="start",
    )

    create_ods_data = SQLExecuteQueryOperator(
        task_id="create_ods_data",
        conn_id=POSTGRES_CONN_ID,
        sql=CREATE_ODS_DATA_SQL,
    )

    create_fact_sales = SQLExecuteQueryOperator(
        task_id="create_fact_sales",
        conn_id=POSTGRES_CONN_ID,
        sql=CREATE_FACT_SALES_SQL,
    )

    end = EmptyOperator(
        task_id="end",
    )

    start >> create_ods_data >> create_fact_sales >> end
