from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.operators.empty import EmptyOperator

DAG_ID = "fct_margin_by_product_mart"
DEFAULT_ARGS = {
    "owner": "ignatov",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

POSTGRES_CONN_ID = "postgres_dwh"
# Соединяем fact_sales и fact_purchases по product_id и считаем среднюю себестоимость (purchase_price) и маржу = sales_price − purchase_price
# --- SQL: создание / обновление витрины margin_by_product_mart  витрина маржи по товарам---
CREATE_MARGIN_BY_PRODUCT_SQL = """
-- Очищаем витрину за весь период
TRUNCATE TABLE dm.margin_by_product_mart;

-- Собираем агрегаты по продажам по брендам
INSERT INTO dm.margin_by_product_mart (
    product_id,
    product_code,
    product_name,
    brand,
    category,
    country_of_prod,
    avg_sales_price,
    avg_purchase_price,
    avg_margin_per_unit,
    total_sales_amount,
    total_purchase_amount,
    total_sales_quantity,
    total_purchase_quantity,
    load_dttm
)
SELECT
    p.product_id,
    p.product_code,
    p.product_name,
    p.brand,
    p.category,
    p.country_of_prod,
    COALESCE(AVG(fs.price), 0) AS avg_sales_price,
    COALESCE(mpp.avg_purchase_price, 0) AS avg_purchase_price,
    COALESCE(AVG(fs.price), 0) - COALESCE(mpp.avg_purchase_price, 0) AS avg_margin_per_unit,
    COALESCE(SUM(fs.amount), 0) AS total_sales_amount,
    COALESCE(mpp.total_purchase_amount, 0) AS total_purchase_amount,
    COALESCE(SUM(fs.quantity), 0) AS total_sales_quantity,
    COALESCE(mpp.total_purchase_quantity, 0) AS total_purchase_quantity,
    NOW() AS load_dttm
FROM dwh.ods_products p
LEFT JOIN dwh.fact_sales fs
    ON p.product_id = fs.product_id
LEFT JOIN (
    SELECT
        fp.product_id,
        AVG(fp.price) AS avg_purchase_price,
        SUM(fp.amount) AS total_purchase_amount,
        SUM(fp.quantity) AS total_purchase_quantity
    FROM dwh.fact_purchases fp
    GROUP BY fp.product_id
) mpp ON p.product_id = mpp.product_id
GROUP BY
    p.product_id,
    p.product_code,
    p.product_name,
    p.brand,
    p.category,
    p.country_of_prod,
    mpp.avg_purchase_price,
    mpp.total_purchase_amount,
    mpp.total_purchase_quantity;

"""

with DAG(
    DAG_ID,
    default_args=DEFAULT_ARGS,
    description="ETL margin by product category and product country prod",
    catchup=False,
) as dag:

    start = EmptyOperator(
        task_id="start",
    )

    create_margin_by_product_mart = SQLExecuteQueryOperator(
        task_id="create_margin_by_product_mart",
        conn_id=POSTGRES_CONN_ID,
        sql=CREATE_MARGIN_BY_PRODUCT_SQL,
    )

    end = EmptyOperator(
        task_id="end",
    )

    start >> create_margin_by_product_mart >> end

