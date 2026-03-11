terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"

#   Хранение состояния Terraform (terraform.tfstate) в бакете (bucket) Yandex Cloud
  backend "s3" {
     endpoints =  {
       s3 = "https://storage.yandexcloud.net"
       dynamodb = "https://docapi.serverless.yandexcloud.net/ru-central1/b1gh21o21vel0a01nq8h/etnk36svp2clivqppik9"
     }
     bucket   = "ignatov-state-lock-bucket"
     region   = "ru-central1"
     key      = "terraform.tfstate"

     dynamodb_table = "state-lock-table"

     skip_region_validation      = true
     skip_credentials_validation = true
     skip_requesting_account_id  = true # Необходимая опция Terraform для версии 1.6.1 и старше.
     skip_s3_checksum            = true # Необходимая опция при описании бэкенда для Terraform версии 1.6.3 и старше.
   }
}


provider "yandex" {
  zone = "ru-central1-a"
}
