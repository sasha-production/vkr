# Вызов модулей в нужном порядке
module "network" {
  source = "./modules/network"
  
  vpc_name    = var.vpc_name
  vpc_cidr    = var.vpc_cidr
  subnet_cidr = var.subnet_cidr
  region      = var.region
}

module "security" {
  source = "./modules/security"
  
  vpc_id      = module.network.vpc_id
  ssh_ip      = var.ssh_ip
  app_ports   = var.app_ports
}
