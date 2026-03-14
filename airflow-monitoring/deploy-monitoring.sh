#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying Monitoring Stack for Airflow${NC}"
echo -e "${GREEN}========================================${NC}"

# Проверка наличия необходимых директорий
echo -e "${YELLOW}Checking directories...${NC}"
for dir in prometheus grafana alertmanager promtail; do
    if [ ! -d "$dir" ]; then
        mkdir -p $dir
        echo -e "  Created $dir directory"
    fi
done

# Установка пароля для Grafana
if [ -z "$GRAFANA_PASSWORD" ]; then
    export GRAFANA_PASSWORD=$(openssl rand -base64 12)
    echo -e "${YELLOW}Generated Grafana password: $GRAFANA_PASSWORD${NC}"
    echo "export GRAFANA_PASSWORD=$GRAFANA_PASSWORD" >> ~/.bashrc
fi

# Проверка наличия конфигурационных файлов
echo -e "${YELLOW}Checking configuration files...${NC}"
if [ ! -f "prometheus/prometheus.yml" ]; then
    echo -e "${RED}Error: prometheus/prometheus.yml not found!${NC}"
    exit 1
fi

# Создание сети если не существует
echo -e "${YELLOW}Creating overlay network...${NC}"
docker network create --driver overlay --attachable monitoring-network 2>/dev/null || true

# Деплой стека
echo -e "${YELLOW}Deploying monitoring stack...${NC}"
docker stack deploy --with-registry-auth -c docker-compose.monitoring.yml monitoring

# Ожидание запуска
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Проверка статуса
echo -e "${YELLOW}Checking service status...${NC}"
docker service ls | grep monitoring

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Monitoring stack deployed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Access points:"
echo -e "  ${YELLOW}Prometheus:${NC} http://localhost:9090"
echo -e "  ${YELLOW}Grafana:${NC} http://localhost:3000 (admin/$GRAFANA_PASSWORD)"
echo -e "  ${YELLOW}Alertmanager:${NC} http://localhost:9093"
echo -e "  ${YELLOW}cAdvisor:${NC} http://localhost:8080 (on each node)"
echo ""
echo -e "To check logs:"
echo -e "  ${YELLOW}docker service logs monitoring_prometheus${NC}"
echo -e "  ${YELLOW}docker service logs monitoring_grafana${NC}"
