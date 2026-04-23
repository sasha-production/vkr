from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
import logging
import pandas as pd
from io import StringIO

DAG_ID = "dag_load_raw_from_csv"
DEFAULT_ARGS = {
    "owner": "ignatov",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

# Пути внутри контейнера (настройте под ваш volume)
RAW_SALES_CSV = "/opt/airflow/data/raw_sales.csv"
RAW_CLIENTS_CSV = "/opt/airflow/data/raw_clients_crm.csv"
RAW_WAREHOUSES_CSV = "/opt/airflow/data/raw_warehouses_excel.csv"
RAW_PRODUCTS_CSV = "/opt/airflow/data/raw_products.csv"
RAW_SUPPLIERS_CSV = "/opt/airflow/data/raw_suppliers.csv"
RAW_PURCHASES_CSV = "/opt/airflow/data/raw_purchases.csv"

POSTGRES_CONN_ID = "postgres_dwh"

# --- SQL создания raw‑таблиц ---
CREATE_RAW_TABLES_SQL = """
TRUNCATE TABLE dwh.raw_sales;

CREATE TABLE IF NOT EXISTS dwh.raw_sales (
    raw_id          BIGSERIAL PRIMARY KEY,
    doc_id          VARCHAR(100),
    doc_date        DATE,
    client_code     VARCHAR(100),
    client_name     TEXT,
    product_code    VARCHAR(100),
    product_name    TEXT,
    warehouse_code  VARCHAR(100),
    quantity        NUMERIC(15, 4),
    price           NUMERIC(15, 4),
    amount          NUMERIC(18, 4),
    source_system   VARCHAR(20),
    load_dttm       TIMESTAMP NOT NULL DEFAULT NOW()
);

TRUNCATE TABLE dwh.raw_clients_crm;

CREATE TABLE IF NOT EXISTS dwh.raw_clients_crm (
    raw_id          BIGSERIAL PRIMARY KEY,
    client_code     VARCHAR(100),
    client_name     TEXT,
    region          TEXT,
    segment         TEXT,
    email           TEXT,
    source_system   VARCHAR(20),
    load_dttm       TIMESTAMP NOT NULL DEFAULT NOW()
);

TRUNCATE TABLE dwh.raw_warehouses_excel;

CREATE TABLE IF NOT EXISTS dwh.raw_warehouses_excel (
    raw_id          BIGSERIAL PRIMARY KEY,
    warehouse_code  VARCHAR(100),
    warehouse_name  TEXT,
    city            TEXT,
    country         TEXT,
    warehouse_type  TEXT,
    source_system   VARCHAR(20),
    load_dttm       TIMESTAMP NOT NULL DEFAULT NOW()
);

TRUNCATE TABLE dwh.raw_products;

CREATE TABLE IF NOT EXISTS dwh.raw_products (
    raw_id           BIGSERIAL PRIMARY KEY,
    product_code     VARCHAR(100) NOT NULL,
    product_name     TEXT,
    category         TEXT,
    brand            TEXT,
    analog_eu_brand  TEXT,
    technical_params TEXT,
    country_of_prod TEXT,
    source_system    VARCHAR(20) NOT NULL,
    load_dttm        TIMESTAMP NOT NULL DEFAULT NOW()
);

TRUNCATE TABLE dwh.raw_suppliers;

CREATE TABLE IF NOT EXISTS dwh.raw_suppliers (
    raw_id           BIGSERIAL PRIMARY KEY,
    supplier_code    TEXT NOT NULL,
    supplier_name    TEXT,
    country          TEXT,
    city             TEXT,
    source_system    TEXT NOT NULL,
    load_dttm        TIMESTAMP NOT NULL DEFAULT NOW()
);

TRUNCATE TABLE dwh.raw_purchases;

CREATE TABLE IF NOT EXISTS dwh.raw_purchases (
    raw_id           BIGSERIAL PRIMARY KEY,
    purchase_doc     TEXT,
    doc_date         DATE,
    supplier_code    TEXT,
    product_code     TEXT,
    warehouse_code   TEXT,
    quantity         NUMERIC(15, 4),
    price            NUMERIC(15, 4),
    amount           NUMERIC(22, 4),
    source_system    TEXT NOT NULL,
    load_dttm        TIMESTAMP NOT NULL DEFAULT NOW()
);

"""

def load_csv_to_postgres(table_name: str, file_path: str, source_system: str, **kwargs):
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = hook.get_conn()

    df = pd.read_csv(file_path)
    df["source_system"] = source_system

    buffer = StringIO()
    df.to_csv(buffer, index=False, header=False)
    buffer.seek(0)

    columns = ", ".join([f'"{c}"' for c in df.columns])
    copy_sql = f"COPY dwh.{table_name} ({columns}) FROM STDIN WITH (FORMAT csv, HEADER false);"

    with conn.cursor() as cur:
        cur.copy_expert(copy_sql, buffer)
        conn.commit()

    logging.info(f"Loaded {len(df)} rows into dwh.{table_name}")

def create_raw_tables(**kwargs):
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    hook.run(CREATE_RAW_TABLES_SQL)

with DAG(
    DAG_ID,
    default_args=DEFAULT_ARGS,
    description="Load CSV files into raw tables (raw_sales, raw_clients_crm, raw_warehouses_excel)",
    # start_date=days_ago(1),
    catchup=False,
) as dag:

    create_raw_tables_task = PythonOperator(
        task_id="create_raw_tables",
        python_callable=create_raw_tables,
    )
    start = EmptyOperator(
        task_id="start",
    )

    load_raw_sales = PythonOperator(
        task_id="load_raw_sales",
        python_callable=load_csv_to_postgres,
        op_kwargs={
            "table_name": "raw_sales",
            "file_path": RAW_SALES_CSV,
            "source_system": "1C",
        },
    )

    load_raw_clients = PythonOperator(
        task_id="load_raw_clients",
        python_callable=load_csv_to_postgres,
        op_kwargs={
            "table_name": "raw_clients_crm",
            "file_path": RAW_CLIENTS_CSV,
            "source_system": "CRM",
        },
    )

    load_raw_warehouses = PythonOperator(
        task_id="load_raw_warehouses",
        python_callable=load_csv_to_postgres,
        op_kwargs={
            "table_name": "raw_warehouses_excel",
            "file_path": RAW_WAREHOUSES_CSV,
            "source_system": "EXCEL",
        },
    )

    load_raw_products = PythonOperator(
        task_id="load_raw_products",
        python_callable=load_csv_to_postgres,
        op_kwargs={
            "table_name": "raw_products",
            "file_path": RAW_PRODUCTS_CSV,
            "source_system": "NOMENCLATURE",  # или "EXCEL", "ERP"
        },
    )

    load_raw_suppliers = PythonOperator(
        task_id="load_raw_suppliers",
        python_callable=load_csv_to_postgres,
        op_kwargs={
            "table_name": "raw_suppliers",
            "file_path": RAW_SUPPLIERS_CSV,
            "source_system": "SUPPLIERS",
        },
    )

    load_raw_purchases = PythonOperator(
        task_id="load_raw_purchases",
        python_callable=load_csv_to_postgres,
        op_kwargs={
            "table_name": "raw_purchases",
            "file_path": RAW_PURCHASES_CSV,
            "source_system": "PURCHASES",
        },
    )

    end = EmptyOperator(
        task_id="end",
    )

    start >> create_raw_tables_task >> [load_raw_sales, load_raw_clients, load_raw_warehouses,
                                        load_raw_products, load_raw_suppliers, load_raw_purchases] >> end
