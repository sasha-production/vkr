from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.operators.empty import EmptyOperator

DAG_ID = "fct_sales_brand_mart"
DEFAULT_ARGS = {
    "owner": "ignatov",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

POSTGRES_CONN_ID = "postgres_dwh"

# --- SQL: создание / обновление витрины sales_brand_mart ---
CREATE_SALES_BRAND_MART_SQL = """
-- Очищаем витрину за весь период (или можно фильтровать по дате)
TRUNCATE TABLE dm.sales_brand_mart;

-- Собираем агрегаты по продажам по брендам
INSERT INTO dm.sales_brand_mart (
    date_id,
    year,
    month,
    brand,
    category,
    country_of_prod,
    analog_eu_brand,
    region,
    segment,
    total_quantity,
    total_amount,
    avg_price,
    load_dttm
)
SELECT
    fs.date_id,
    d.year,
    d.month,
    p.brand,
    p.category,
    p.country_of_prod,
    p.analog_eu_brand,
    c.region,
    c.segment,
    SUM(fs.quantity) AS total_quantity,
    SUM(fs.amount) AS total_amount,
    ROUND(AVG(fs.price), 2) AS avg_price,
    NOW() AS load_dttm
FROM dwh.fact_sales fs
JOIN dwh.dim_date d
    ON fs.date_id = d.date_id
JOIN dwh.ods_products p
    ON fs.product_id = p.product_id
JOIN dwh.ods_clients c
    ON fs.client_id = c.client_id
WHERE fs.date_id IS NOT NULL
GROUP BY
    fs.date_id,
    d.year,
    d.month,
    p.brand,
    p.category,
    p.country_of_prod,
    p.analog_eu_brand,
    c.region,
    c.segment;

"""

with DAG(
    DAG_ID,
    default_args=DEFAULT_ARGS,
    description="ETL for sales brand data mart (ELMI vs EU brands, by region/segment)",
    catchup=False,
) as dag:

    start = EmptyOperator(
        task_id="start",
    )

    create_sales_brand_mart = SQLExecuteQueryOperator(
        task_id="create_sales_brand_mart",
        conn_id=POSTGRES_CONN_ID,
        sql=CREATE_SALES_BRAND_MART_SQL,
    )

    end = EmptyOperator(
        task_id="end",
    )

    start >> create_sales_brand_mart >> end

