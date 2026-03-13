Отличный выбор! NFS - правильное решение для multi-node кластера. Давайте настроим NFS для общего хранилища файлов Airflow.

## Настройка NFS сервера

### На менеджер-ноде (или выделенном сервере хранения):

```bash
# Установка NFS сервера
sudo apt-get update
sudo apt-get install -y nfs-kernel-server

# Создание директорий для Airflow
sudo mkdir -p /srv/nfs/airflow/{dags,logs,plugins,config}
sudo chown -R nobody:nogroup /srv/nfs/airflow
sudo chmod -R 755 /srv/nfs/airflow

# Настройка экспорта NFS
sudo nano /etc/exports
```

Добавьте в `/etc/exports`:
```
/srv/nfs/airflow *(rw,sync,no_subtree_check,no_root_squash,insecure)
# Или для конкретной подсети:
# /srv/nfs/airflow 192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash,insecure)
```

Примените настройки:
```bash
sudo exportfs -a
sudo systemctl restart nfs-kernel-server

# Проверка
sudo showmount -e localhost
```

## На всех нодах кластера (менеджер и воркеры):

```bash
# Установка NFS клиента
sudo apt-get update
sudo apt-get install -y nfs-common

# Создание точек монтирования
sudo mkdir -p /mnt/nfs/airflow/{dags,logs,plugins,config}
```

## Обновленный docker-compose.yaml с NFS

```yaml
version: '3.8'

services:
  redis:
    image: redis:latest
    deploy:
      placement:
        constraints:
          - node.role == manager
    networks:
      - airflow-network

  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres-data:/var/lib/postgresql/data
    deploy:
      placement:
        constraints:
          - node.role == manager
    networks:
      - airflow-network

  airflow-webserver:
    image: apache/airflow:2.7.1
    depends_on:
      - postgres
      - redis
    environment:
      - AIRFLOW__CORE__EXECUTOR=CeleryExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
      - AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres/airflow
      - AIRFLOW__CELERY__BROKER_URL=redis://redis:6379/0
      - AIRFLOW__CORE__FERNET_KEY=${FERNET_KEY}
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
      - AIRFLOW__WEBSERVER__SECRET_KEY=${WEBSERVER_SECRET_KEY}
    volumes:
      - airflow-dags:/opt/airflow/dags
      - airflow-logs:/opt/airflow/logs
      - airflow-plugins:/opt/airflow/plugins
      - airflow-config:/opt/airflow/config
    command: webserver
    deploy:
      placement:
        constraints:
          - node.role == manager
      replicas: 1
    networks:
      - airflow-network
    ports:
      - "8080:8080"

  airflow-scheduler:
    image: apache/airflow:2.7.1
    depends_on:
      - postgres
      - redis
    environment:
      - AIRFLOW__CORE__EXECUTOR=CeleryExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
      - AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres/airflow
      - AIRFLOW__CELERY__BROKER_URL=redis://redis:6379/0
      - AIRFLOW__CORE__FERNET_KEY=${FERNET_KEY}
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
    volumes:
      - airflow-dags:/opt/airflow/dags
      - airflow-logs:/opt/airflow/logs
      - airflow-plugins:/opt/airflow/plugins
      - airflow-config:/opt/airflow/config
    command: scheduler
    deploy:
      placement:
        constraints:
          - node.role == manager
      replicas: 1
    networks:
      - airflow-network

  airflow-worker:
    image: apache/airflow:2.7.1
    depends_on:
      - postgres
      - redis
    environment:
      - AIRFLOW__CORE__EXECUTOR=CeleryExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
      - AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres/airflow
      - AIRFLOW__CELERY__BROKER_URL=redis://redis:6379/0
      - AIRFLOW__CORE__FERNET_KEY=${FERNET_KEY}
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
    volumes:
      - airflow-dags:/opt/airflow/dags
      - airflow-logs:/opt/airflow/logs
      - airflow-plugins:/opt/airflow/plugins
      - airflow-config:/opt/airflow/config
    command: celery worker
    deploy:
      mode: global
      placement:
        constraints:
          - node.role == worker
    networks:
      - airflow-network

  airflow-flower:
    image: apache/airflow:2.7.1
    depends_on:
      - postgres
      - redis
    environment:
      - AIRFLOW__CORE__EXECUTOR=CeleryExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
      - AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres/airflow
      - AIRFLOW__CELERY__BROKER_URL=redis://redis:6379/0
      - AIRFLOW__CORE__FERNET_KEY=${FERNET_KEY}
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
    command: celery flower
    volumes:
      - airflow-config:/opt/airflow/config
    deploy:
      placement:
        constraints:
          - node.role == manager
      replicas: 1
    networks:
      - airflow-network
    ports:
      - "5555:5555"

networks:
  airflow-network:
    driver: overlay

volumes:
  postgres-data:
    driver: local
    
  airflow-dags:
    driver: local
    driver_opts:
      type: nfs
      o: addr=<NFS_SERVER_IP>,rw,nfsvers=4,soft,timeo=30,retrans=3
      device: :/srv/nfs/airflow/dags
      
  airflow-logs:
    driver: local
    driver_opts:
      type: nfs
      o: addr=<NFS_SERVER_IP>,rw,nfsvers=4,soft,timeo=30,retrans=3
      device: :/srv/nfs/airflow/logs
      
  airflow-plugins:
    driver: local
    driver_opts:
      type: nfs
      o: addr=<NFS_SERVER_IP>,rw,nfsvers=4,soft,timeo=30,retrans=3
      device: :/srv/nfs/airflow/plugins
      
  airflow-config:
    driver: local
    driver_opts:
      type: nfs
      o: addr=<NFS_SERVER_IP>,ro,nfsvers=4,soft,timeo=30,retrans=3
      device: :/srv/nfs/airflow/config
```

## Скрипт для инициализации NFS структуры

Создайте `setup-nfs-airflow.sh`:

```bash
#!/bin/bash

NFS_SERVER="<NFS_SERVER_IP>"
AIRFLOW_HOME="/srv/nfs/airflow"

# Создание структуры директорий на NFS сервере
ssh user@$NFS_SERVER "
sudo mkdir -p $AIRFLOW_HOME/{dags,logs,plugins,config}
sudo chown -R 50000:50000 $AIRFLOW_HOME  # UID/GID airflow пользователя
sudo chmod -R 755 $AIRFLOW_HOME

# Создание тестового DAG
cat > $AIRFLOW_HOME/dags/test_nfs.py << 'EOF'
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    'test_nfs_mount',
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag:
    test_task = BashOperator(
        task_id='test_nfs_task',
        bash_command='echo \"NFS is working on $(hostname)\"'
    )
EOF

sudo chown 50000:50000 $AIRFLOW_HOME/dags/test_nfs.py
"
```

## Проверка NFS монтирования

### Тест на каждой ноде:
```bash
# Проверка доступности NFS
showmount -e <NFS_SERVER_IP>

# Ручное монтирование для теста
sudo mount -t nfs <NFS_SERVER_IP>:/srv/nfs/airflow/dags /mnt/test
ls -la /mnt/test
sudo umount /mnt/test
```

### Проверка через Docker:
```bash
# Создайте тестовый сервис для проверки NFS
docker service create \
  --name test-nfs \
  --mount type=volume,source=airflow-dags,target=/test \
  --network stage2_airflow-network \
  alpine:latest \
  ls -la /test/

# Проверьте логи
docker service logs test-nfs

# Удалите тестовый сервис
docker service rm test-nfs
```

## Применение конфигурации

```bash
# Экспортируйте переменные
export NFS_SERVER_IP=<ваш-nfs-сервер-ip>
export FERNET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export WEBSERVER_SECRET_KEY=$(openssl rand -hex 16)

# Разверните стек
docker stack deploy --with-registry-auth -c docker-compose.yaml stage2

# Проверьте статус
docker service ls
docker service ps stage2_airflow-worker
```

## Мониторинг NFS

Для отладки проблем с NFS:

```bash
# На любой ноде проверьте статус монтирования
docker run --rm --privileged --pid=host debian nsenter -t 1 -m -u -n -i mount | grep nfs

# Проверьте логи NFS на сервере
sudo tail -f /var/log/syslog | grep nfs

# На клиенте проверьте статистику NFS
cat /proc/self/mountstats | grep nfs
```

## Важные замечания:

1. **UID/GID**: Airflow контейнер использует пользователя с UID 50000. Убедитесь, что права на NFS шаре установлены корректно:
   ```bash
   sudo chown -R 50000:50000 /srv/nfs/airflow
   ```

2. **Безопасность**: Для production используйте ограничение доступа по IP:
   ```
   /srv/nfs/airflow 192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash,insecure)
   ```

3. **Производительность**: Настройте параметры NFS для лучшей производительности:
   ```yaml
   o: addr=<NFS_SERVER_IP>,rw,nfsvers=4,rsize=1048576,wsize=1048576,hard,intr,noatime,timeo=600
   ```

4. **Отказоустойчивость**: Рассмотрите использование NFS с репликацией или DRBD для критичных данных.
