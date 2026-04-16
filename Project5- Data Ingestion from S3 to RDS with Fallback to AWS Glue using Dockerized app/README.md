# Project 5: Data Ingestion from S3 to RDS with Glue Fallback (Dockerized)

---

## Overview

This project demonstrates a **Dockerized Python data pipeline** that:

- Reads a CSV file from Amazon S3  
- Loads data into Amazon RDS (MySQL)  
- Falls back to AWS Glue Data Catalog if RDS fails  

The application runs inside a Docker container on an Ubuntu EC2 instance.

---

## Objective

To build a containerized data ingestion system that:

- Integrates S3, RDS, and Glue  
- Handles failures using fallback logic  
- Demonstrates real-world DevOps practices  

---

## Architecture

```
S3 → EC2 Docker container → RDS MySQL
    ↓
If RDS insert fails:
    ↓
S3 → EC2 Docker container → AWS Glue Data Catalog

```

---

## AWS Services Used

- Amazon S3 – Stores input CSV file  
- Amazon EC2 (Ubuntu) – Runs Docker container  
- Docker – Containerizes the application  
- Amazon RDS (MySQL) – Primary database  
- AWS Glue Data Catalog – Fallback metadata store  
- IAM Role – Secure access to AWS services  

---

## Data Flow

1. CSV file stored in S3  
2. Application reads file using boto3  
3. Data parsed using pandas  
4. Attempt to insert into RDS  
5. If RDS fails → fallback to Glue  

---

## Sample Output (Glue Fallback)

```
Starting Project 5 ingestion pipeline
Reading CSV from S3
CSV loaded successfully
Trying to load data into RDS
RDS load failed. Switching to Glue fallback
Glue database created
Glue table created successfully
Pipeline completed using Glue fallback
```

---

## Outcome

- Built a resilient data pipeline  
- Implemented fallback mechanism  
- Integrated Docker with AWS services  

---

## Cleanup

Delete after use:

- RDS instance  
- EC2 instance  
- S3 bucket  
- Glue database  
- IAM role (if unused)  

---

## Author

Vaishnavi  Chikhale

