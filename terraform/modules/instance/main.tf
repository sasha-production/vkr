# Создание загрузочных дисков для каждой ВМ
resource "yandex_compute_disk" "boot_disk" {
  for_each = var.instances

  name     = "${each.key}-boot-disk"
  type     = try(each.value.boot_disk.type, var.default_boot_disk_type)
  zone     = each.value.zone
  size     = try(each.value.boot_disk.size_gb, var.default_boot_disk_size_gb)
  image_id = try(each.value.image_id, var.default_image_id)

}

# Создание виртуальных машин
resource "yandex_compute_instance" "vm" {
  for_each = var.instances

  name        = each.key
  description = try(each.value.description, "Виртуальная машина ${each.key}")
  platform_id = try(each.value.platform_id, var.default_platform_id)
  zone        = each.value.zone

  resources {
    cores         = each.value.resources.cores
    memory        = each.value.resources.memory
  }

  boot_disk {
    auto_delete = try(each.value.boot_disk.auto_delete, var.default_boot_disk_auto_delete)
    disk_id     = yandex_compute_disk.boot_disk[each.key].id
  }

  network_interface {
    subnet_id      = try(each.value.network.subnet_id, var.default_subnet_id)
    nat            = try(each.value.network.nat, var.default_nat)
    nat_ip_address = try(each.value.network.nat_ip_address, null)
    ip_address     = try(each.value.network.ip_address, null)
  }

  metadata = {
    ssh-keys           = "${try(each.value.ssh.user, var.default_ssh_user)}:${file(try(each.value.ssh.public_key_path, var.default_ssh_public_key_path))}"
    user-data          = try(each.value.user_data, var.default_user_data)
  }

  scheduling_policy {
    preemptible = try(each.value.preemptible, var.default_preemptible)
  }

  allow_stopping_for_update = true

  depends_on = [
    yandex_compute_disk.boot_disk
  ]
}
