from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import socket
import logging


def check_worker():
    """Функция для проверки, на каком воркере выполняется задача"""
    hostname = socket.gethostname()
    logging.info(f"Task executed on worker: {hostname}")
    return f"Worker hostname: {hostname}"


def check_celery_config():
    """Проверка конфигурации Celery"""
    from airflow.configuration import conf
    executor = conf.get('core', 'executor')
    broker = conf.get('celery', 'broker_url')
    backend = conf.get('celery', 'result_backend')

    logging.info(f"Executor: {executor}")
    logging.info(f"Broker: {broker}")
    logging.info(f"Backend: {backend}")
    return f"Executor: {executor}"


with DAG(
    'test_celery_workers',
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['test']
) as dag:

    check_executor = PythonOperator(
        task_id='check_executor_config',
        python_callable=check_celery_config
    )

    check_worker_task = PythonOperator(
        task_id='check_worker_hostname',
        python_callable=check_worker
    )

    check_executor >> check_worker_task
