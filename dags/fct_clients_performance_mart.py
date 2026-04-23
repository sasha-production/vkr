from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.operators.empty import EmptyOperator

DAG_ID = "fct_clients_performance_mart"
DEFAULT_ARGS = {
    "owner": "sasha",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

POSTGRES_CONN_ID = "postgres_dwh"

# --- SQL‑запрос создания/обновления витрины ---
CREATE_CLIENTS_PERFORMANCE_MART_SQL = """
TRUNCATE TABLE dm.clients_performance_mart;

INSERT INTO dm.clients_performance_mart (
    client_id,
    client_code,
    client_name,
    region,
    segment,
    total_orders,
    first_order_date,
    last_order_date,
    lifetime_value,
    elmi_amount,
    non_elmi_amount,
    days_between_first_last,
    load_dttm
)
SELECT
    c.client_id,
    c.client_code,
    c.client_name,
    c.region,
    c.segment,
    COALESCE(cnt.total_orders, 0) AS total_orders,
    cnt.first_order_date,
    cnt.last_order_date,
    COALESCE(cnt.lifetime_value, 0) AS lifetime_value,
    COALESCE(cnt.elmi_amount, 0) AS elmi_amount,
    COALESCE(cnt.non_elmi_amount, 0) AS non_elmi_amount,
    COALESCE(
        CASE
            WHEN cnt.first_order_date IS NULL THEN NULL
            WHEN cnt.last_order_date IS NULL THEN NULL
            ELSE (cnt.last_order_date - cnt.first_order_date)::INT
        END,
        NULL
    ) AS days_between_first_last,
    NOW() AS load_dttm
FROM dwh.ods_clients c
LEFT JOIN (
    SELECT
        fs.client_id,
        COUNT(fs.sale_id) AS total_orders,
        MIN(fs.date_id) AS first_order_date,
        MAX(fs.date_id) AS last_order_date,
        SUM(fs.amount) AS lifetime_value,
        SUM(
            CASE WHEN p.brand = 'ELMI' THEN fs.amount ELSE 0 END
        ) AS elmi_amount,
        SUM(
            CASE WHEN p.brand != 'ELMI' THEN fs.amount ELSE 0 END
        ) AS non_elmi_amount
    FROM dwh.fact_sales fs
    JOIN dwh.ods_products p
        ON fs.product_id = p.product_id
    GROUP BY fs.client_id
) AS cnt ON c.client_id = cnt.client_id;
"""

with DAG(
    DAG_ID,
    default_args=DEFAULT_ARGS,
    description="ETL for clients performance mart (loyalty, ELMI share, lifetime value)",
    catchup=False,
) as dag:
    start = EmptyOperator(
        task_id="start",
    )

    create_clients_performance_mart = SQLExecuteQueryOperator(
        task_id="create_clients_performance_mart",
        conn_id=POSTGRES_CONN_ID,
        sql=CREATE_CLIENTS_PERFORMANCE_MART_SQL,
    )

    end = EmptyOperator(
        task_id="end",
    )

    start >> create_clients_performance_mart >> end
