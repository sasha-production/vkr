from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime
####
with DAG(
    'test_worker',
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag:
    task = BashOperator(
        task_id='test_task',
        bash_command='echo "Worker is working! Hostname: $(hostname)"'
    )
