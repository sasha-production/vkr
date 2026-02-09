# Основные параметры сети
variable "network_name" {
  type        = string
  description = "Имя создаваемой сети"
  default     = "network1"
}

variable "network_description" {
  type        = string
  description = "Описание сети"
  default     = "Создана через Terraform"
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

variable "subnet_b_description" {
  type        = string
  description = "Описание второй подсети"
  default     = "Вторая подсеть в зоне B"
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
