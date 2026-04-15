data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

module "vpc" {
  source = "./modules/vpc"

  project_name          = var.project_name
  vpc_cidr              = var.vpc_cidr
  public_subnet_a_cidr  = var.public_subnet_a_cidr
  public_subnet_b_cidr  = var.public_subnet_b_cidr
  private_subnet_a_cidr = var.private_subnet_a_cidr
  private_subnet_b_cidr = var.private_subnet_b_cidr
  az_a                  = var.az_a
  az_b                  = var.az_b
  my_ip                 = var.my_ip
}

module "rds" {
  source = "./modules/rds"

  project_name       = var.project_name
  db_name            = var.db_name
  db_username        = var.db_username
  db_password        = var.db_password
  db_instance_class  = var.db_instance_class
  private_subnet_ids = [module.vpc.private_subnet_a_id, module.vpc.private_subnet_b_id]
  rds_sg_id          = module.vpc.rds_sg_id
}

module "app_ec2" {
  source = "./modules/ec2"

  instance_name               = "${var.project_name}-app"
  ami_id                      = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = module.vpc.private_subnet_a_id
  security_group_ids          = [module.vpc.app_sg_id]
  key_name                    = var.key_name
  associate_public_ip_address = false

  user_data = templatefile("${path.module}/userdata/app.sh.tpl", {
    db_host     = module.rds.db_endpoint
    db_name     = var.db_name
    db_user     = var.db_username
    db_password = var.db_password
  })
}

module "web_ec2" {
  source = "./modules/ec2"

  instance_name               = "${var.project_name}-web"
  ami_id                      = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = module.vpc.public_subnet_a_id
  security_group_ids          = [module.vpc.web_sg_id]
  key_name                    = var.key_name
  associate_public_ip_address = true

  user_data = templatefile("${path.module}/userdata/web.sh.tpl", {
    app_private_ip = module.app_ec2.private_ip
  })
}
