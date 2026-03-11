# Основная переменная с конфигурацией ВМ
variable "instances" {
  type = map(object({
    # Обязательные параметры
    zone = string
    
    # Ресурсы ВМ
    resources = object({
      cores  = number
      memory = number
      core_fraction = optional(number)
    })
    
    # Параметры загрузочного диска (опционально)
    boot_disk = optional(object({
      type       = optional(string)
      size_gb    = optional(number)
      auto_delete = optional(bool)
    }))
    
    # Сетевые параметры (опционально)
    network = optional(object({
      subnet_id      = optional(string)
      nat            = optional(bool)
      nat_ip_address = optional(string)
      ip_address     = optional(string)
      dns_record     = optional(list(object({
        fqdn = string
        dns_zone_id = string
        ttl = optional(number)
      })))
    }))
    
    # Дополнительные параметры (опционально)
    platform_id = optional(string)
    image_id    = optional(string)
    description = optional(string)
    
    # SSH доступ (опционально)
    ssh = optional(object({
      user              = optional(string)
      public_key_path   = optional(string)
    }))
    
    # Дополнительные настройки
    user_data          = optional(string)
    serial_port_enable = optional(bool)
    preemptible        = optional(bool)
    
    # Метки
    labels = optional(map(string))
  }))
  
  description = "Конфигурация виртуальных машин"
  default     = {}
  
  validation {
    condition = alltrue([
      for name, config in var.instances :
      config.resources.cores >= 1 && config.resources.cores <= 32 &&
      config.resources.memory >= 1 && config.resources.memory <= 256 &&
      contains(["ru-central1-a", "ru-central1-b", "ru-central1-c", "ru-central1-d"], config.zone)
    ])
    error_message = "Некорректные параметры ВМ. Ядра: 1-32, память: 1-256 ГБ, зона: ru-central1-a/b/c/d"
  }
}

# Параметры по умолчанию
variable "default_platform_id" {
  type        = string
  description = "Тип платформы по умолчанию"
  default     = "standard-v3"
  validation {
    condition     = contains(["standard-v1", "standard-v2", "standard-v3"], var.default_platform_id)
    error_message = "Платформа должна быть standard-v1, standard-v2 или standard-v3"
  }
}

variable "default_image_id" {
  type        = string
  description = "ID образа по умолчанию (Ubuntu 24.04 LTS)"
  default     = "fd8q58gr0c7bdoh1c6qf"
}

variable "default_core_fraction" {
  type        = number
  description = "Гарантированная доля vCPU по умолчанию"
  default     = 100
  validation {
    condition     = contains([5, 20, 100], var.default_core_fraction)
    error_message = "Доля vCPU должна быть 5, 20 или 100 процентов"
  }
}

# Параметры дисков по умолчанию
variable "default_boot_disk_type" {
  type        = string
  description = "Тип загрузочного диска по умолчанию"
  default     = "network-ssd"
  validation {
    condition     = contains(["network-hdd", "network-ssd", "network-ssd-nonreplicated"], var.default_boot_disk_type)
    error_message = "Тип диска должен быть network-hdd, network-ssd или network-ssd-nonreplicated"
  }
}

variable "default_boot_disk_size_gb" {
  type        = number
  description = "Размер загрузочного диска по умолчанию (ГБ)"
  default     = 20
  validation {
    condition     = var.default_boot_disk_size_gb >= 10 && var.default_boot_disk_size_gb <= 4096
    error_message = "Размер диска должен быть от 10 до 4096 ГБ"
  }
}

variable "default_boot_disk_auto_delete" {
  type        = bool
  description = "Автоматически удалять диск при удалении ВМ по умолчанию"
  default     = true
}

# Сетевые параметры по умолчанию
variable "default_subnet_id" {
  type        = string
  description = "ID подсети по умолчанию"
  default     = ""
}

variable "default_nat" {
  type        = bool
  description = "Назначать публичный IP по умолчанию"
  default     = true
}

# SSH параметры по умолчанию
variable "default_ssh_user" {
  type        = string
  description = "Имя пользователя SSH по умолчанию"
  default     = "ubuntu"
}

variable "default_ssh_public_key_path" {
  type        = string
  description = "Путь к публичному SSH ключу по умолчанию"
  default     = "~/.ssh/id_rsa.pub"
}

# Дополнительные параметры по умолчанию
variable "default_user_data" {
  type        = string
  description = "Cloud-init конфигурация по умолчанию"
  default     = ""
}

variable "default_serial_port_enable" {
  type        = bool
  description = "Включить serial port по умолчанию"
  default     = false
}

variable "default_preemptible" {
  type        = bool
  description = "Создавать прерываемые ВМ по умолчанию"
  default     = false
}

# Общие параметры
variable "domain_name" {
  type        = string
  description = "Доменное имя для хостов"
  default     = "local"
}

variable "common_labels" {
  type        = map(string)
  description = "Общие метки для всех ресурсов"
  default     = {}
}
