# Project 6: 3-Tier Infrastructure Deployment Using Terraform Modules

## Overview
This project demonstrates a complete 3-tier architecture deployed on AWS using Terraform modules.

### Architecture:
- Web Tier: EC2 (Nginx + HTML form) - Public subnet
- App Tier: EC2 (Nginx + PHP) - Private subnet
- Database Tier: RDS MySQL - Private subnets

---

## Architecture Flow

User → Web EC2 → App EC2 → RDS MySQL

- Web server serves registration form
- Form submission is reverse proxied to app server
- App server processes data and inserts into RDS

---

## Project Structure

project6-3tier-terraform/
├── main.tf
├── variables.tf
├── outputs.tf
├── providers.tf
├── versions.tf
├── terraform.tfvars
├── modules/
│ ├── vpc/
│ ├── ec2/
│ └── rds/
└── userdata/
├── web.sh.tpl
└── app.sh.tpl

---

## Deployment Steps

```bash
terraform init
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
