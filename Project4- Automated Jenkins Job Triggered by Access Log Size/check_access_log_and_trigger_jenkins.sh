#!/bin/bash
#This is Monitoring Script
set -u

LOG_FILE="/var/log/apache2/access.log"
THRESHOLD_BYTES=1073741824
JENKINS_URL="http://3.88.28.113:8080"
JENKINS_JOB="AccessLogToS3Pipeline"
JENKINS_USER="admin"
JENKINS_API_TOKEN="112e900c949740eae44c251358a3e87263"
S3_BUCKET="project4-access-log-archive-12345"
S3_PREFIX="apache-access-logs"
LOCAL_LOG_FILE="/opt/project4/project4_monitor.log"
LOCK_FILE="/opt/project4/project4_access_log_monitor.lock"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOCAL_LOG_FILE"
}

cleanup() {
    [ -f "$LOCK_FILE" ] && rm -f "$LOCK_FILE"
}
trap cleanup EXIT

if [ -e "$LOCK_FILE" ]; then
    log "Another monitor instance is already running. Exiting."
    exit 0
fi

touch "$LOCK_FILE"
