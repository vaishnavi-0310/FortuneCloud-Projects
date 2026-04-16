output "vpc_id" {
  value = module.vpc.vpc_id
}

output "public_subnet_a_id" {
  value = module.vpc.public_subnet_a_id
}

output "public_subnet_b_id" {
  value = module.vpc.public_subnet_b_id
}

output "private_subnet_a_id" {
  value = module.vpc.private_subnet_a_id
}

output "private_subnet_b_id" {
  value = module.vpc.private_subnet_b_id
}

output "web_sg_id" {
  value = module.vpc.web_sg_id
}

output "app_sg_id" {
  value = module.vpc.app_sg_id
}

output "rds_sg_id" {
  value = module.vpc.rds_sg_id
}

output "web_public_ip" {
  value = module.web_ec2.public_ip
}

output "web_private_ip" {
  value = module.web_ec2.private_ip
}

output "app_private_ip" {
  value = module.app_ec2.private_ip
}

output "web_url" {
  value = "http://${module.web_ec2.public_ip}"
}

output "ssh_web" {
  value = "ssh -i ${var.private_key_path} ubuntu@${module.web_ec2.public_ip}"
}

output "rds_endpoint" {
  value = module.rds.db_endpoint
}
