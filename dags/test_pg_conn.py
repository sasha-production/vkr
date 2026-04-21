from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.empty import EmptyOperator

POSTGRES_CONN_ID = 'postgres_dwh'

# Аргументы по умолчанию
default_args = {
    'owner': 'ignatov',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}


def test_postgres_connection():
    """Функция для проверки подключения к PostgreSQL"""
    try:
        # Создаем хук с указанием connection_id (ваше имя соединения)
        hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

        # Простой запрос для проверки соединения
        result = hook.get_first("SELECT 1 as test, NOW() as current_time, version() as pg_version")

        # Логируем результат
        print(f"✅ Соединение успешно!")
        print(f"Результат запроса: {result}")
        print(f"Версия PostgreSQL: {result[2]}")
        print(f"Текущее время на БД: {result[1]}")

        return True

    except Exception as e:
        print(f"❌ Ошибка подключения: {str(e)}")
        raise


def test_simple_query():
    """Функция с простым запросом"""
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

    # Получаем список таблиц (пример)
    tables = hook.get_records("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        LIMIT 5
    """)

    print(f"Найдено таблиц в public схеме: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")


# Создаем DAG
with DAG(
        'test_postgres_connection',
        default_args=default_args,
        description='Простой DAG для проверки соединения с PostgreSQL',
        catchup=False,
        tags=['test', 'postgres'],
) as dag:
    # Стартовая задача (опционально)
    start = EmptyOperator(task_id='start')

    # Задача проверки соединения
    test_connection = PythonOperator(
        task_id='test_postgres_connection',
        python_callable=test_postgres_connection,
    )

    # Задача с простым запросом
    test_query = PythonOperator(
        task_id='test_simple_query',
        python_callable=test_simple_query,
    )

    # Финальная задача
    end = EmptyOperator(task_id='end')

    # Порядок выполнения задач
    start >> test_connection >> test_query >> end
