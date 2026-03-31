import logging
from airflow.decorators import dag, task

"""
Максимально простой DAG для проверки подключения
"""
from airflow_clickhouse_plugin.hooks.clickhouse import ClickHouseHook
from airflow.operators.python import PythonOperator
from datetime import datetime

def check_clickhouse():
    """Простая проверка подключения"""
    ch_hook = ClickHouseHook(clickhouse_conn_id='clickhouse_sqlite')
    result = ch_hook.execute('DESCRIBE nomenclature;')
    # result = hook.execute("SELECT 'ClickHouse connection OK' as message")
    # result = hook.execute("SELECT 1")
    logging.info(f"res is {result}")
    return "Подключение работает"



@dag("ch_check", start_date=datetime(2023, 1, 1), schedule=None, catchup=False)
def taskflow_etl():
    @task
    def extract():
        return "Process start"


    @task
    def load():
        return "process complited"

  # Задаем порядок выполнения как вызов функций
    raw_data = extract()

    check_task = PythonOperator(
        task_id='clickhouse_check',
        python_callable=check_clickhouse,

    )
    load()
# Инициализируем DAG
my_dag = taskflow_etl()
