"""
Тестовый DAG для отладки одного файла
Обновление 20.03
Работает, загружает из s3 в ch,
При повторном запуске ошибка (так и должно быть)
ch plugin
"""
from airflow.decorators import dag, task
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow_clickhouse_plugin.hooks.clickhouse import ClickHouseHook
from airflow.models import Variable
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os
import tempfile
import logging
import json
import re
from typing import Dict, List, Optional, Tuple
from collections import Counter
import hashlib

# Настройка логирования
logger = logging.getLogger(__name__)

# Конфигурация
S3_BUCKET = "prod"
S3_RAW_PREFIX = "raw"
S3_PROCESSED_PREFIX = "processed"
CLICKHOUSE_CONN_ID = "clickhouse_sqlite"
AWS_CONN_ID = "minio_s3"
KEY_NAME = "users_export_{{ ds }}.csv"

# Маппинг источников и их конфигурации
SOURCE_CONFIGS = {
    "turkish_factory": {
        "s3_prefix": "raw/turkish_factory", # raw в бакете, а не suppliers
        "source_system": "turkish_factory",
        "encoding": "utf-8",
        "delimiter": ",",
        "skip_rows": 0,
        "column_mapping": {
            "URUN_KODU": "sku",
            "URUN_ADI": "name",
            "KATEGORI": "category",
            "ALT_KATEGORI": "subcategory",
            "MALZEME": "material",
            "MENŞEİ": "country"
        },
        "static_fields": {
            "manufacturer": "ELM Turkey"
        }
    },
    "chinese_factory": {
        "s3_prefix": "raw/chinese_factory",
        "source_system": "chinese_factory",
        "encoding": "utf-8-sig",
        "delimiter": ",",
        "skip_rows": 0,
        "column_mapping": {
            "Product ID": "sku",
            "产品名称 (Product Name)": "name",
            "Category/类别": "category",
            "Subcategory/子类别": "subcategory",
            "Material/材料": "material",
            "Manufacturer/制造商": "manufacturer"
        },
        "static_fields": {
            "country": "China"
        }
    },
    "russian_factory": {
        "s3_prefix": "raw/russian_factory",
        "source_system": "russian_factory",
        "encoding": "utf-8",
        "delimiter": ",",
        "skip_rows": 0,
        "column_mapping": {
            "Артикул": "sku",
            "Наименование": "name",
            "Категория": "category",
            "Подкатегория": "subcategory",
            "Материал": "material",
            "Производитель": "manufacturer"
        },
        "static_fields": {
            "country": "Russia"
        }
    },
    "german_catalog": {
        "s3_prefix": "raw/german_catalog",
        "source_system": "german_catalog",
        "encoding": "utf-8",
        "delimiter": ",",
        "skip_rows": 0,
        "column_mapping": {
            "Artikelnummer": "sku",
            "Bezeichnung": "name",
            "Kategorie": "category",
            "Unterkategorie": "subcategory",
            "Material": "material",
            "Hersteller": "manufacturer",
            "Land": "country"
        }
    },
    "commercial_price_list": {
        "s3_prefix": "price_lists/commercial",
        "source_system": "commercial_price_list",
        "encoding": "utf-8",
        "delimiter": ",",
        "skip_rows": 0,
        "column_mapping": {
            "Код товара": "sku",
            "Наименование": "name",
            "Категория": "category",
            "Подкатегория": "subcategory",
            "Материал": "material",
            "Производитель": "manufacturer",
            "Страна": "country"
        }
    },
    "warehouse_movements": {
        "s3_prefix": "erp/warehouse",
        "source_system": "warehouse_movements",
        "encoding": "cp1251",
        "delimiter": ",",
        "skip_rows": 0,
        "column_mapping": {
            "Артикул": "sku",
            "Наименование": "name",
            "Категория": "category",
            "Склад": "warehouse",
            "Количество": "quantity",
            "ТипОперации": "operation_type"
        },
        "is_fact_table": True  # Это не справочник, а факты движения
    }
}


# Функции для нормализации данных
def normalize_sku(sku: str) -> str:
    """Приводит артикул к единому формату"""
    if pd.isna(sku) or not sku:
        return None

    sku = str(sku).strip()

    # Удаляем лишние префиксы (1С_, ERP- и т.д.)
    sku = re.sub(r'^(1С_|ERP-|ART-|OLD-)', '', sku, flags=re.IGNORECASE)

    # Приводим к верхнему регистру
    sku = sku.upper()

    # Заменяем подчеркивания на дефисы (ELM_CON_123 -> ELM-CON-123)
    sku = sku.replace('_', '-')

    # Удаляем множественные дефисы
    sku = re.sub(r'-+', '-', sku)

    return sku if sku else None


def normalize_name(name: str) -> str:
    """Приводит названия к единому формату"""
    if pd.isna(name) or not name:
        return None

    name = str(name).strip()

    # Убираем лишние пробелы
    name = re.sub(r'\s+', ' ', name)

    # Первая буква заглавная, остальные строчные (для кириллицы и латиницы)
    words = name.split()
    normalized_words = []
    for word in words:
        if len(word) > 1:
            # Если слово в верхнем регистре, делаем нормальный
            if word.isupper():
                word = word.capitalize()
        normalized_words.append(word)

    return ' '.join(normalized_words)


def normalize_category(category: str) -> str:
    """Приводит категории к единому формату"""
    if pd.isna(category) or not category:
        return 'other'

    category = str(category).strip().lower()

    # Маппинг различных вариантов написания
    category_mapping = {
        'fan': 'вентиляторы',
        'вентилятор': 'вентиляторы',
        'ventilator': 'вентиляторы',
        'grille': 'решетки для вентиляторов',
        'решетка': 'решетки для вентиляторов',
        'ızgarası': 'решетки для вентиляторов',
        'lock': 'промышленная фурнитура',
        'замок': 'промышленная фурнитура',
        'hinge': 'промышленная фурнитура',
        'петля': 'промышленная фурнитура',
        'connector': 'промышленные разъемы',
        'разъем': 'промышленные разъемы',
        'konnektör': 'промышленные разъемы',
        'seal': 'уплотнители',
        'уплотнитель': 'уплотнители',
        'conta': 'уплотнители',
        'gland': 'кабельные вводы',
        'ввод': 'кабельные вводы',
    }

    for key, value in category_mapping.items():
        if key in category:
            return value

    return category


def extract_specifications(row: pd.Series) -> str:
    """Извлекает специфичные характеристики в JSON"""
    specs = {}

    # Общие поля, которые не должны попасть в specifications
    base_fields = ['sku', 'name', 'category', 'subcategory', 'material',
                   'manufacturer', 'country', 'source_file', 'source_system']

    for col in row.index:
        if col not in base_fields and pd.notna(row[col]) and row[col] != '':
            specs[col] = str(row[col])

    return json.dumps(specs, ensure_ascii=False)


def detect_duplicates(df: pd.DataFrame, sku_col: str = 'sku') -> Tuple[pd.DataFrame, Dict]:
    """
    Обнаруживает и обрабатывает дубликаты
    Возвращает: (уникальные записи, статистика)
    """
    total_rows = len(df)

    # Проверяем на null в SKU
    null_skus = df[sku_col].isna().sum()
    df = df.dropna(subset=[sku_col])

    # Находим дубликаты по SKU
    duplicates = df[df.duplicated(subset=[sku_col], keep=False)]
    unique_skus = df[sku_col].nunique()

    # Статистика
    stats = {
        'total_rows': total_rows,
        'null_skus': null_skus,
        'unique_skus': unique_skus,
        'duplicates_found': len(duplicates),
        'duplicate_skus': df[sku_col].value_counts()[df[sku_col].value_counts() > 1].to_dict()
    }

    # Оставляем только уникальные записи (берем первую)
    df_unique = df.drop_duplicates(subset=[sku_col], keep='first')

    return df_unique, stats


# @task
# def list_s3_files(source_name: str, execution_date: str) -> List[Dict]:
#     """
#     Получает список файлов из S3 для конкретного источника за дату
#     """
#     logging.info(f"start conn s3 HOOK")
#     s3_hook = S3Hook(aws_conn_id=AWS_CONN_ID)
#     logging.info(f"conn to s3 success")
#     source_config = SOURCE_CONFIGS[source_name]
#
#     year, month, day = execution_date.split('-')
#     prefix = f"{source_config['s3_prefix']}/year={year}/month={month}/day={day}/"
#     logging.info(f"Prefix if {prefix}")
#
#     logger.info(f"Поиск файлов в S3 по префиксу: {prefix}")
#
#     files = []
#     for key in s3_hook.list_keys(bucket_name=S3_BUCKET, prefix=prefix):
#         logging.info(f"Key - {key}, prefix - {prefix}")
#         if key.endswith('.csv'):
#             file_info = {
#                 'source_name': source_name,
#                 's3_key': key,
#                 'local_path': None,
#                 'source_config': source_config
#             }
#             files.append(file_info)
#
#     logger.info(f"Найдено {len(files)} CSV файлов для {source_name}")
#     return files


@task
def download_from_s3(file_info: Dict, ds, **kwargs) -> Dict:
    """
    Скачивает файл из S3 во временную директорию
    """
    logging.info(f"fun download_from_s3")
    s3_hook = S3Hook(aws_conn_id=AWS_CONN_ID)

    # Создаём временный файл
    # with tempfile.NamedTemporaryFile(
    #         prefix=f"{file_info['source_name']}_{ds}",
    #         suffix='.csv',
    #         delete=False
    # ) as tmp_file:
    #     local_path = tmp_file.name


    local_path = "/tmp"
    logger.info(f"Скачивание {file_info['s3_key']} в {local_path}")
    # Скачиваем файл
    s3_hook.download_file(
        key=file_info['s3_key'],
        bucket_name=S3_BUCKET,
        local_path=local_path,
        preserve_file_name=True,
        use_autogenerated_subdir=False
    )
    logging.info(f"Local path is {local_path}")
    file_info['local_path'] = local_path + '/' + file_info['s3_key'].split('/')[-1]
    logger.info(f"local path is - {file_info['local_path']}")
    file_info['download_time'] = datetime.now().isoformat()

    return file_info


@task
def normalize_file(file_info: Dict) -> Dict:
    """
    Нормализует CSV файл: чистит, приводит к единому формату
    """
    source_config = file_info['source_config']
    local_path = file_info['local_path']

    logger.info(f"Нормализация файла: {local_path}")

    try:
        # Читаем CSV с правильной кодировкой
        df = pd.read_csv(
            local_path,
            encoding=source_config.get('encoding', 'utf-8'),
            delimiter=source_config.get('delimiter', ','),
            skiprows=source_config.get('skip_rows', 0),
            dtype=str,
            keep_default_na=False
        )

        logger.info(f"Прочитано {len(df)} строк из исходного файла")

        # Переименовываем колонки согласно маппингу
        column_mapping = source_config['column_mapping']
        df = df.rename(columns=column_mapping)

        # Оставляем только нужные колонки (которые есть в маппинге)
        target_columns = list(column_mapping.values())
        df = df[[col for col in target_columns if col in df.columns]]

        # Добавляем статические поля
        for field, value in source_config.get('static_fields', {}).items():
            df[field] = value

        # Нормализуем основные поля
        if 'sku' in df.columns:
            df['sku'] = df['sku'].apply(normalize_sku)

        if 'name' in df.columns:
            df['name'] = df['name'].apply(normalize_name)

        if 'category' in df.columns:
            df['category'] = df['category'].apply(normalize_category)

        # Добавляем метаданные источника
        df['source_file'] = file_info['s3_key']
        df['source_system'] = source_config['source_system']
        df['load_date'] = pd.Timestamp.now().date()

        # Создаём JSON со спецификациями
        df['specifications'] = df.apply(extract_specifications, axis=1)

        # Удаляем временные колонки, которые могли попасть в specifications
        for col in df.columns:
            if col not in ['sku', 'name', 'category', 'subcategory', 'material',
                           'manufacturer', 'country', 'source_file', 'source_system',
                           'load_date', 'specifications']:
                df = df.drop(columns=[col])

        # Обрабатываем дубликаты
        df_unique, stats = detect_duplicates(df)

        logger.info(f"После нормализации: {len(df_unique)} уникальных записей")

        # Сохраняем нормализованный файл
        normalized_path = local_path.replace('.csv', '_normalized.csv')
        df_unique.to_csv(normalized_path, index=False, encoding='utf-8')

        file_info['normalized_path'] = normalized_path
        file_info['row_count'] = len(df_unique)
        file_info['stats'] = stats
        file_info['normalization_status'] = 'success'

    except Exception as e:
        logger.error(f"Ошибка при нормализации {local_path}: {e}")
        file_info['normalization_status'] = 'failed'
        file_info['error'] = str(e)
        raise

    return file_info


@task
def load_to_clickhouse(file_info: Dict) -> Dict:
    """
    Загружает нормализованные данные в ClickHouse
    """
    if file_info.get('normalization_status') != 'success':
        logger.warning(f"Файл {file_info.get('s3_key')} не прошел нормализацию, пропускаем загрузку")
        file_info['clickhouse_status'] = 'skipped'
        return file_info

    normalized_path = file_info['normalized_path']

    logger.info(f"Загрузка {normalized_path} в ClickHouse")

    try:
        # Читаем нормализованные данные
        df = pd.read_csv(normalized_path)

        # Подключаемся к ClickHouse
        clickhouse_hook = ClickHouseHook(clickhouse_conn_id=CLICKHOUSE_CONN_ID)

        # Вставляем данные батчами
        batch_size = 1000
        total_inserted = 0

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i + batch_size]

            # Формируем запрос на вставку
            insert_query = """
            INSERT INTO elm.nomenclature 
            (sku, name, category, subcategory, material, manufacturer, 
             country, specifications, source_file, source_system, load_date)
            VALUES
            """

            values = []
            for _, row in batch.iterrows():
                value = f"('{row['sku']}', '{row['name']}', '{row['category']}', " \
                        f"'{row.get('subcategory', '')}', '{row.get('material', '')}', " \
                        f"'{row.get('manufacturer', '')}', '{row.get('country', '')}', " \
                        f"'{row['specifications']}', '{row['source_file']}', " \
                        f"'{row['source_system']}', '{row['load_date']}')"
                values.append(value)

            if values:
                full_query = insert_query + ','.join(values)
                clickhouse_hook.execute(full_query)
                total_inserted += len(batch)

        logger.info(f"Успешно загружено {total_inserted} записей в ClickHouse")

        file_info['clickhouse_status'] = 'success'
        file_info['rows_inserted'] = total_inserted

    except Exception as e:
        logger.error(f"Ошибка при загрузке в ClickHouse: {e}")
        file_info['clickhouse_status'] = 'failed'
        file_info['clickhouse_error'] = str(e)
        raise

    return file_info


@task
def save_quality_metrics(file_infos: List[Dict], execution_date: str) -> Dict:
    """
    Сохраняет метрики качества загрузки
    """
    clickhouse_hook = ClickHouseHook(clickhouse_conn_id=CLICKHOUSE_CONN_ID)

    load_id = f"load_{execution_date.replace('-', '')}_{datetime.now().strftime('%H%M%S')}"

    for file_info in file_infos:
        if file_info.get('stats'):
            stats = file_info['stats']

            query = f"""
            INSERT INTO elm.load_quality 
            (load_id, source_file, total_rows, unique_skus, duplicates_found, 
             null_skus, invalid_rows, load_date)
            VALUES (
                '{load_id}',
                '{file_info.get('s3_key', 'unknown')}',
                {stats.get('total_rows', 0)},
                {stats.get('unique_skus', 0)},
                {stats.get('duplicates_found', 0)},
                {stats.get('null_skus', 0)},
                0,
                '{execution_date}'
            )
            """
            clickhouse_hook.run(query)

    logger.info(f"Метрики качества сохранены для загрузки {load_id}")

    return {
        'load_id': load_id,
        'execution_date': execution_date,
        'files_processed': len(file_infos)
    }


@task
def cleanup_temp_files(file_infos: List[Dict]):
    """
    Удаляет временные файлы
    """
    cleaned = 0
    for file_info in file_infos:
        for path_key in ['local_path', 'normalized_path']:
            path = file_info.get(path_key)
            if path and os.path.exists(path):
                os.unlink(path)
                cleaned += 1
                logger.info(f"Удалён временный файл: {path}")

    return {'cleaned': cleaned}


@task
def send_completion_notification(file_infos: List[Dict], quality_metrics: Dict):
    """
    Отправляет уведомление о завершении обработки
    """
    successful = [f for f in file_infos if f.get('clickhouse_status') == 'success']
    failed = [f for f in file_infos if f.get('clickhouse_status') == 'failed']
    skipped = [f for f in file_infos if f.get('clickhouse_status') == 'skipped']

    total_rows = sum(f.get('rows_inserted', 0) for f in successful)

    message = f"""
    ✅ ETL процесс завершен

    Статистика:
    - Всего файлов: {len(file_infos)}
    - Успешно загружено: {len(successful)}
    - Ошибок: {len(failed)}
    - Пропущено: {len(skipped)}
    - Всего записей: {total_rows}
    - ID загрузки: {quality_metrics.get('load_id')}

    Детали по файлам:
    """

    for f in successful:
        message += f"\n  ✅ {f['source_name']}: {f.get('rows_inserted', 0)} записей"

    for f in failed:
        message += f"\n  ❌ {f['source_name']}: {f.get('error', 'Unknown error')}"

    logger.info(message)
    return message


@dag("test_ch_8",schedule=None,start_date=datetime(2024, 1, 1),catchup=False,tags=['elm', 'test'],)
def test_normalization():

    # Тестируем на одном файле
    test_file = {
            'source_name': 'russian_factory_export', # chinese_factory, russian_factory, german_catalog, turkish_factory
            's3_key': 'raw/russian_factory_export.csv',
            'source_config': SOURCE_CONFIGS['russian_factory']
        }

    downloaded = download_from_s3(test_file)
    normalized = normalize_file(downloaded)
    loaded = load_to_clickhouse(normalized)


dag = test_normalization()
