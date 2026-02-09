# Переменные для провайдера Yandex Cloud
variable "cloud_id" {
  type        = string
  description = "ID облака Yandex Cloud"
  sensitive   = true
}

variable "folder_id" {
  type        = string
  description = "ID каталога Yandex Cloud"
  sensitive   = true
}

variable "default_zone" {
  type        = string
  description = "Зона по умолчанию"
  default     = "ru-central1-a"
}

# Основные параметры сети
variable "network_name" {
  type        = string
  description = "Имя создаваемой сети"
  default     = "network1"
}

# Переменные для первой подсети
variable "subnet_a_name" {
  type        = string
  description = "Имя первой подсети (зона A)"
  default     = "subnet-a"
}

variable "subnet_a_cidr" {
  type        = tuple([string])
  description = "CIDR блок для первой подсети"
  default     = ["192.168.1.0/24"]
}

variable "zone1" {
  type        = string
  description = "Зона доступности для первой подсети"
  default     = "ru-central1-a"
}

# Переменные для второй подсети
variable "subnet_b_name" {
  type        = string
  description = "Имя второй подсети (зона B)"
  default     = "subnet-b"
}

variable "subnet_b_cidr" {
  type        = tuple([string])
  description = "CIDR блок для второй подсети"
  default     = ["192.168.2.0/24"]
}

variable "zone2" {
  type        = string
  description = "Зона доступности для второй подсети"
  default     = "ru-central1-b"
}

# Переменные для внешнего IP-адреса
variable "external_ip_name" {
  type        = string
  description = "Имя внешнего IP-адреса"
  default     = "external-ip"
}

# Дополнительные переменные
variable "labels" {
  type        = map(string)
  description = "Метки для всех ресурсов"
  default     = {}
}

variable "create_external_ip" {
  type        = bool
  description = "Создавать ли внешний IP-адрес"
  default     = true
}


#variable "subnet_id" {
#  type        = string
#  description = "ID of existing subnet"
#}

variable "default_preemptible" {
  type        = bool
  default = true
  description = "SSH public key for VM access"
}

variable "ssh_public_key" {
  type        = string
  description = "SSH public key for VM access"
}

variable "instances" {
  type = map(object({
    zone     = string
    cores    = number
    memory   = number
    disk_size = optional(number, 20)
    disk_type = optional(string, "network-hdd")
    preemptible = bool
  }))
  description = "Configuration for VMs"
  default = {
    "vm-1" = {
      zone      = "ru-central1-a"
      cores     = 2
      memory    = 4
      disk_size = 20
      disk_type = "network-hdd"
      preemptible = true
    }
    "vm-2" = {
      zone      = "ru-central1-a"
      cores     = 2
      memory    = 2
      disk_size = 20
      disk_type = "network-hdd"
      preemptible = true
    }
    "vm-3" = {
      zone      = "ru-central1-a"
      cores     = 2
      memory    = 2
      disk_size = 25
      disk_type = "network-ssd"
      preemptible = true
    }
  }
}


variable "image_id" {
  type        = string
  description = "ID of OS image"
  default     = "fd84mnbiarffhtfrhnog" # Ubuntu 24.04
}

variable "vm_platform_id" {
  type        = string
  description = "VM platform type"
  default     = "standard-v3"
}

variable "username" {
  type        = string
  description = "Username for SSH access"
  default     = "ubuntu"
}
