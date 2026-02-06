resource "yandex_vpc_network" "network" {
  name        = var.network_name
  description = var.network_description
}

resource "yandex_vpc_subnet" "subnet-a" {
  name           = var.subnet-1-name
  description    = var.subnet_description
  v4_cidr_blocks = [var.subnet-1-cidr]
  zone           = var.zone1
  network_id     = "$yandex_vpc_network.default.id"
}

resource "yandex_vpc_subnet" "subnet-b" {
  name           = var.subnet-2-name
  description    = var.subnet_description
  v4_cidr_blocks = [var.subnet-2-cidr]
  zone           = var.zone2           
  network_id     = "$yandex_vpc_network.default.id"
}

resource "yandex_vpc_address" "addr" {
  name = var.addr_name
  deletion_protection = false
  external_ipv4_address {
    zone_id = var.zone1
  }
}
