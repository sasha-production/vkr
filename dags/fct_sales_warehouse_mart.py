from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.operators.empty import EmptyOperator

DAG_ID = "fct_sales_warehouse_mart"
DEFAULT_ARGS = {
    "owner": "sasha",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

POSTGRES_CONN_ID = "postgres_dwh"

# --- SQL‑запрос создания/обновления витрины sales_warehouse_mart ---
CREATE_SALES_WAREHOUSE_MART_SQL = """
TRUNCATE TABLE dm.sales_warehouse_mart;

INSERT INTO dm.sales_warehouse_mart (
    date_id,
    year,
    month,
    warehouse_code,
    warehouse_name,
    city,
    country,
    total_quantity,
    total_amount,
    total_orders,
    load_dttm
)
SELECT
    fs.date_id,
    d.year,
    d.month,
    w.warehouse_code,
    w.warehouse_name,
    w.city,
    w.country,
    SUM(fs.quantity) AS total_quantity,
    SUM(fs.amount) AS total_amount,
    COUNT(fs.sale_id) AS total_orders,
    NOW() AS load_dttm
FROM dwh.fact_sales fs
JOIN dwh.dim_date d
    ON fs.date_id = d.date_id
JOIN dwh.ods_warehouses w
    ON fs.warehouse_id = w.warehouse_id
WHERE fs.date_id IS NOT NULL
GROUP BY
    fs.date_id,
    d.year,
    d.month,
    w.warehouse_code,
    w.warehouse_name,
    w.city,
    w.country;
"""

with DAG(
    DAG_ID,
    default_args=DEFAULT_ARGS,
    description="ETL for sales warehouse mart (sales by warehouse and region)",
    catchup=False,
) as dag:

    start = EmptyOperator(
        task_id="start",
    )

    create_sales_warehouse_mart = SQLExecuteQueryOperator(
        task_id="create_sales_warehouse_mart",
        conn_id=POSTGRES_CONN_ID,
        sql=CREATE_SALES_WAREHOUSE_MART_SQL,
    )

    end = EmptyOperator(
        task_id="end",
    )

    start >> create_sales_warehouse_mart >> end
