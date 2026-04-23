from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.operators.empty import EmptyOperator

DAG_ID = "fct_margin_by_client_brand_mart"
DEFAULT_ARGS = {
    "owner": "sasha",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

POSTGRES_CONN_ID = "postgres_dwh"

# --- Запрос заполнения витрины ---
CREATE_MARGIN_BY_CLIENT_BRAND_MART_SQL = """
TRUNCATE TABLE dm.margin_by_client_brand_mart;

INSERT INTO dm.margin_by_client_brand_mart (
    client_id,
    client_code,
    client_name,
    region,
    segment,
    brand,
    total_sales_amount,
    total_purchase_amount,
    total_margin,
    avg_margin_per_sale,
    load_dttm
)
SELECT
    c.client_id,
    c.client_code,
    c.client_name,
    c.region,
    c.segment,
    p.brand,
    COALESCE(SUM(fs.amount), 0) AS total_sales_amount,
    COALESCE(SUM(fp.amount), 0) AS total_purchase_amount,
    COALESCE(SUM(fs.amount - fp.amount), 0) AS total_margin,
    CASE
        WHEN SUM(fs.amount) > 0
        THEN (SUM(fs.amount) - SUM(fp.amount)) / NULLIF(SUM(fs.amount), 0)
        ELSE 0
    END AS avg_margin_per_sale,
    NOW() AS load_dttm
FROM dwh.ods_clients c
JOIN dwh.fact_sales fs
    ON c.client_id = fs.client_id
JOIN dwh.fact_purchases fp
    ON fs.product_id = fp.product_id
JOIN dwh.ods_products p
    ON fs.product_id = p.product_id
GROUP BY
    c.client_id,
    c.client_code,
    c.client_name,
    c.region,
    c.segment,
    p.brand;
"""

with DAG(
    DAG_ID,
    default_args=DEFAULT_ARGS,
    description="ETL for margin by client & brand mart (client performance by brand margin)",
    catchup=False,
) as dag:

    start = EmptyOperator(
        task_id="start",
    )

    create_margin_by_client_brand_mart = SQLExecuteQueryOperator(
        task_id="create_margin_by_client_brand_mart",
        conn_id=POSTGRES_CONN_ID,
        sql=CREATE_MARGIN_BY_CLIENT_BRAND_MART_SQL,
    )

    end = EmptyOperator(
        task_id="end",
    )

    start >> create_margin_by_client_brand_mart >> end
