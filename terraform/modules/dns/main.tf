resource "yandex_dns_zone" "zone1" {
  name        = "<имя_зоны>"
  description = "<описание_зоны>"

  labels = {
    label1 = "<метка_зоны>"
  }

  zone    = "<доменная_зона>."
  public           = false
  private_networks = ["<идентификатор_сети_1>","<идентификатор_сети_2"]
}
