# Создание загрузочных дисков для каждой VM
resource "yandex_compute_disk" "boot_disk" {
  for_each = var.instances
  
  name     = "boot-disk-${each.key}"
  type     = each.value.disk_type
  zone     = each.value.zone
  size     = each.value.disk_size
  image_id = var.image_id
}

# Создание виртуальных машин через итерацию (for_each)
resource "yandex_compute_instance" "vm" {
  for_each = var.instances
  
  name                      = each.key
  allow_stopping_for_update = true
  platform_id               = var.vm_platform_id
  zone                      = each.value.zone
  hostname = each.key
  resources {
    cores  = each.value.cores
    memory = each.value.memory
  }

  boot_disk {
    disk_id = yandex_compute_disk.boot_disk[each.key].id
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.subnet-a.id
    nat       = true
  }

  metadata = {
    user-data = "${file("./declaration.yaml")}"
  }

  scheduling_policy {
    preemptible = try(each.value.preemptible, var.default_preemptible)
  }

  depends_on = [
    yandex_vpc_subnet.subnet-a,
    yandex_compute_disk.boot_disk
  ]

}
