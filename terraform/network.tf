# network resource
resource "yandex_vpc_network" "network" {
  name        = var.network_name
  description = "Network name for vkr"
}

# subnet resource 
resource "yandex_vpc_subnet" "subnet-a" {
  name           = var.subnet_a_name
  v4_cidr_blocks = var.subnet_a_cidr
  zone           = var.zone1
  network_id     = yandex_vpc_network.network.id
}

resource "yandex_vpc_subnet" "subnet-b" {
  name           = var.subnet_b_name
  v4_cidr_blocks = var.subnet_b_cidr
  zone           = var.zone2          
  network_id     = yandex_vpc_network.network.id
}

resource "yandex_vpc_address" "addr" {
  count = var.create_external_ip ? 1 : 0
  name = var.external_ip_name
  deletion_protection = false
  external_ipv4_address {
    zone_id = var.zone1
  }
}
