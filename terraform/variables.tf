variable "region" {
  description = "Регион размещения инфраструктуры"
  type        = string
  default     = "ru-central1"
}

variable "vpc_name" {
  description = "Имя VPC"
  type        = string
  default     = "etl-platform-vpc"
}

variable "vpc_cidr" {
  description = "CIDR блока VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "instance_type_large" {
  description = "Тип инстанса для ВМ с высокой нагрузкой"
  type        = string
  default     = "standard-v2"
}

variable "ssh_ip" {
  description = "IP адрес для доступа по SSH"
  type        = string
  default     = "0.0.0.0/0"
}

variable "key_name" {
  description = "Имя ключевой пары SSH"
  type        = string
  sensitive   = true
}
