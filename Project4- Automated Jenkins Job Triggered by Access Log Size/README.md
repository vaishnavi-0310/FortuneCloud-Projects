# Project 4: Automated Jenkins Job Triggered by Access Log Size

---

## Overview
This project implements an automated system that monitors an Apache access log file on an Ubuntu server. When the log file exceeds **1 GB**, a Jenkins Pipeline job is triggered automatically to:

- Upload the log file to **Amazon S3**
- Verify the upload
- Clear the original log file safely

The system is fully automated using a **cron job** and includes proper logging and error handling.

---

## Objective
- Monitor log file size automatically  
- Trigger Jenkins job based on condition  
- Archive logs in S3  
- Ensure safe cleanup of logs  
- Automate everything with minimal manual intervention  

---

## Architecture

```
Apache (access.log)
↓
Monitoring Script (Bash)
↓
Jenkins API Trigger
↓
Jenkins Pipeline
↓
S3 Upload + Verification
↓
Log File Truncated
```

---

## Services Used
- **AWS EC2 (Ubuntu)** – Hosting environment  
- **Apache2** – Log generation  
- **Jenkins** – Automation engine  
- **Amazon S3** – Log storage  
- **IAM** – Access control  
- **AWS CLI** – S3 operations  
- **cron** – Scheduling  
- **Bash scripting** – Monitoring logic  

---

## Working

### 🔹 Step 1: Log Generation
- Apache continuously writes access logs to: `/var/log/apache2/access.log`


---

### 🔹 Step 2: Monitoring Script Execution
- A Bash script runs every **5 minutes** using cron  
- It checks the size of the log file  

---

### 🔹 Step 3: Condition Evaluation
- If log size **≤ 1 GB**  
→ Script exits (no action)  

- If log size **> 1 GB**  
→ Script triggers Jenkins job using API  

---

### 🔹 Step 4: Jenkins Pipeline Execution
- Jenkins receives parameters:
- Log file path  
- S3 bucket  
- S3 prefix  

- Performs:
- Upload log file to S3  
- Verify upload using AWS CLI  

---

### 🔹 Step 5: Log Cleanup
- Jenkins clears the log file using: `truncate -s 0`
- Ensures Apache continues writing to the same file  

---

### 🔹 Step 6: Logging & Automation
- Script logs activity in: `/opt/project4/project4_monitor.log`
- Cron ensures continuous automation  

---

## Final Outcome

- Automated monitoring system successfully implemented  
- Jenkins job triggered dynamically based on log size condition  
- Log files archived securely in Amazon S3  
- Original log file cleared safely after successful upload  
- Complete workflow automated using cron scheduling 

---

## Author
Vaishnavi Chikhale
