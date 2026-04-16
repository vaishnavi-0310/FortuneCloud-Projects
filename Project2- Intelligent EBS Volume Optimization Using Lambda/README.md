# Project 2: Intelligent EBS Volume Optimization (Serverless AWS Project)

## Project Overview
This project implements a **serverless automation pipeline** that monitors Amazon EBS volumes and automatically converts **gp2 volumes to gp3** for better performance and cost optimization.

The solution uses AWS services like **Lambda, Step Functions, DynamoDB, SNS, and CloudWatch** to create a fully automated, event-driven workflow.

---

## Objective
- Identify EBS volumes of type **gp2**
- Filter volumes tagged with `AutoConvert=true`
- Automatically convert them to **gp3**
- Maintain logs and audit trail
- Send notifications on success/failure

---

## Architecture

```
EventBridge (Scheduler)
        ↓
Step Functions (Orchestrator)
        ↓
Lambda (Scan Volumes)
        ↓
DynamoDB (Log)
        ↓
Lambda (Modify Volume)
        ↓
Lambda (Verify Status)
        ↓
SNS (Notification)
```

---

## AWS Services Used
- **Amazon EC2 / EBS** – Target volumes  
- **AWS Lambda** – Core logic execution  
- **AWS Step Functions** – Workflow orchestration  
- **Amazon DynamoDB** – Logging and audit storage  
- **Amazon SNS** – Notifications  
- **Amazon CloudWatch** – Monitoring and logs  
- **IAM** – Access control  

---

## Workflow Explanation

### 1. Scan Volumes
- Lambda scans for:
  - `VolumeType = gp2`
  - Tag: `AutoConvert = true`

### 2. Modify Volumes
- Converts detected volumes to **gp3** using:
  - `ec2.modifyvolumes()`

### 3. Wait State
- Waits for volume modification to complete

### 4. Verify and Notify
- Checks modification status  
- Logs results to DynamoDB  
- Sends notification via SNS

---

## Expected Output

- EBS volume converted to gp3  
- Log entry in DynamoDB  
- Notification email via SNS  
- Execution logs in CloudWatch

---

## Security Best Practices

- Used IAM roles with least privilege access  
- Avoided hardcoding credentials  
- Scoped permissions where possible  
- Enabled CloudWatch logging for observability

---

## Cleanup

To avoid charges:
- Delete Lambda functions  
- Remove Step Function  
- Delete DynamoDB table  
- Delete SNS topic  
- Remove IAM roles and policies  
- Delete test EBS volumes and EC2 instances  

---

## Author
Vaishnavi Chikhale
