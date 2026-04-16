# Project 3: Automated Backup and Rotation Script with Google Drive Integration

## Overview

This project implements an automated backup system on an AWS EC2 instance. It creates timestamped backups of a project directory, stores them locally, uploads them to Google Drive, applies a rotation policy, logs all activities, and sends notifications using a webhook.

---

## Objective

- Automate project backups
- Store backups in structured format
- Upload backups to Google Drive
- Implement rotation (daily, weekly, monthly)
- Maintain logs
- Send notifications
- Schedule using cron

---

## Architecture

```
Project Folder (EC2)
↓
Python Script
↓
ZIP Backup Created
↓
Local Storage
↓
Upload via rclone
↓
Google Drive
↓
Rotation Cleanup
↓
Logging + Webhook
```


---

## Technologies Used

- AWS EC2
- Python
- rclone
- Google Drive
- Linux cron
- curl

---

## Project Files

- `backup.py` → main automation script  
- `run_backup.sh` → wrapper script for cron  
- `project3.env` → configuration file  
- `README.md` → documentation  

---

## Configuration

Example config:

```env
PROJECT_NAME=Docker
SOURCE_DIR=/home/ec2-user/Docker
BACKUP_BASE_DIR=/home/ec2-user/backups
LOG_FILE=/opt/project3/logs/backup.log

RCLONE_REMOTE=gdrive
GDRIVE_FOLDER=Project3Backups

DAILY_KEEP=7
WEEKLY_KEEP=4
MONTHLY_KEEP=3

WEBHOOK_URL=https://webhook.site/your-url
NOTIFY_ENABLED=true
