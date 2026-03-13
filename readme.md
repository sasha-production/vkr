Создайте временный сервис для инициализации базы данных:

bash
# Убедитесь, что postgres и redis запущены
docker stack deploy --with-registry-auth -c docker-compose.yaml stage2

# Подождите 10-15 секунд, чтобы postgres полностью запустился
sleep 15

# Запустите временный контейнер для инициализации БД
docker service create --name stage2_db_init \
  --network stage2_airflow-network \
  --env AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow \
  --env AIRFLOW__CORE__FERNET_KEY=${FERNET_KEY} \
  apache/airflow:2.7.1 \
  airflow db init

# После успешного выполнения удалите временный сервис
docker service rm stage2_db_init

# Теперь перезапустите остальные сервисы
docker stack deploy --with-registry-auth -c docker-compose.yaml stage2


---------------

Способ 2: Создание пользователя через запущенный контейнер
Если вы хотите создать пользователя через уже запущенный контейнер веб-сервера:

bash
# Найдите имя контейнера веб-сервера
docker ps | grep airflow-webserver

# Выполните команду внутри контейнера
docker exec -it <container_id> airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
----

Получилось включить воркер через # Зайдите в контейнер веб-сервера
docker exec -it $(docker ps | grep stage2_airflow-webserver | awk '{print $1}') bash и # Проверьте статус Celery воркеров
airflow celery worker
