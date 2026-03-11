# Сеть
output "network_id" {
  value       = yandex_vpc_network.network.id
  description = "Идентификатор созданной сети"
}

output "network_name" {
  value       = yandex_vpc_network.network.name
  description = "Имя созданной сети"
}

# Первая подсеть
output "subnet_a_id" {
  value       = yandex_vpc_subnet.subnet-a.id
  description = "Идентификатор первой подсети"
}

output "subnet_a_name" {
  value       = yandex_vpc_subnet.subnet-a.name
  description = "Имя первой подсети"
}

output "subnet_a_cidr" {
  value       = yandex_vpc_subnet.subnet-a.v4_cidr_blocks
  description = "CIDR блок первой подсети"
}

output "subnet_a_zone" {
  value       = yandex_vpc_subnet.subnet-a.zone
  description = "Зона доступности первой подсети"
}

# Вторая подсеть
output "subnet_b_id" {
  value       = yandex_vpc_subnet.subnet-b.id
  description = "Идентификатор второй подсети"
}

output "subnet_b_name" {
  value       = yandex_vpc_subnet.subnet-b.name
  description = "Имя второй подсети"
}

output "subnet_b_cidr" {
  value       = yandex_vpc_subnet.subnet-b.v4_cidr_blocks
  description = "CIDR блок второй подсети"
}

output "subnet_b_zone" {
  value       = yandex_vpc_subnet.subnet-b.zone
  description = "Зона доступности второй подсети"
}

# Внешний IP-адрес
output "external_ip_id" {
  value       = var.create_external_ip ? yandex_vpc_address.addr[0].id : null
  description = "Идентификатор внешнего IP-адреса"
}

output "external_ip_address" {
  value       = var.create_external_ip ? yandex_vpc_address.addr[0].external_ipv4_address[0].address : null
  description = "Значение внешнего IP-адреса"
}

# Сводная информация
output "all_subnets" {
  value = {
    subnet_a = {
      id   = yandex_vpc_subnet.subnet-a.id
      name = yandex_vpc_subnet.subnet-a.name
      cidr = yandex_vpc_subnet.subnet-a.v4_cidr_blocks[0]
      zone = yandex_vpc_subnet.subnet-a.zone
    }
    subnet_b = {
      id   = yandex_vpc_subnet.subnet-b.id
      name = yandex_vpc_subnet.subnet-b.name
      cidr = yandex_vpc_subnet.subnet-b.v4_cidr_blocks[0]
      zone = yandex_vpc_subnet.subnet-b.zone
    }
  }
  description = "Информация обо всех созданных подсетях"
}
