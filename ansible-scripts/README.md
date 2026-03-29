# Docker Swarm Ansible Deployment

## Структура проекта

ansible-scripts/
├── ansible.cfg # Конфигурация Ansible
├── inventory.ini # Инвентори файл с хостами
├── group_vars/ # Переменные для групп
│ ├── all.yml # Общие переменные
│ ├── manager.yml # Переменные для менеджеров
│ └── nodes.yml # Переменные для нод
├── requirements.yml # Зависимости Ansible Galaxy
├── playbooks/
│ ├── docker-swarm-setup.yml # Главный плейбук
│ ├── tasks/ # Отдельные таски
│ │ ├── docker_setup.yml
│ │ ├── swarm_manager.yml
│ │ ├── swarm_worker.yml
│ │ └── node_labels.yml
│ └── handlers/
│ └── main.yml

## Использование

### 1. Установка зависимостей
```bash
ansible-galaxy collection install -r requirements.yml

### 2. Настройка inventory.ini
Отредактировать файл inventory.ini, указав IP адреса серверов

### 3. Проверка подключения
```bash
ansible all -m ping

### 4. Запуск плейбука
```bash
# Полная установка
ansible-playbook playbooks/docker-swarm-setup.yml

# Только установка Docker
ansible-playbook playbooks/docker-swarm-setup.yml --tags docker

# Только настройка Swarm
ansible-playbook playbooks/docker-swarm-setup.yml --tags swarm

# Только добавление меток
ansible-playbook playbooks/docker-swarm-setup.yml --tags labels

### Переменные
Основные переменные (group_vars/all.yml)
docker_user: Пользователь для добавления в группу docker (по умолчанию: sasha)

docker_packages: Список пакетов Docker для установки

mnt_path: Путь для изменения прав доступа (по умолчанию: /mnt)

Метки узлов (group_vars/manager.yml и nodes.yml)
node_labels: Список меток для узлов кластера


