#!/usr/bin/env python3

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class Config:
    project_name: str
    source_dir: Path
    backup_base_dir: Path
    log_file: Path
    rclone_remote: str
    gdrive_folder: str
    daily_keep: int
    weekly_keep: int
    monthly_keep: int
    webhook_url: str
    notify_enabled: bool


def parse_env_file(env_path: Path) -> Dict[str, str]:
    if not env_path.exists():
        raise FileNotFoundError(f"Config file not found: {env_path}")

    values: Dict[str, str] = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def str_to_bool(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "y", "on"}


def load_config(env_path: Path) -> Config:
    env = parse_env_file(env_path)

    required = [
        "PROJECT_NAME",
        "SOURCE_DIR",
        "BACKUP_BASE_DIR",
        "LOG_FILE",
        "RCLONE_REMOTE",
        "GDRIVE_FOLDER",
        "DAILY_KEEP",
        "WEEKLY_KEEP",
        "MONTHLY_KEEP",
        "WEBHOOK_URL",
        "NOTIFY_ENABLED",
    ]

    missing = [key for key in required if key not in env]
    if missing:
        raise ValueError(f"Missing config values: {', '.join(missing)}")

    return Config(
        project_name=env["PROJECT_NAME"],
        source_dir=Path(env["SOURCE_DIR"]).expanduser(),
        backup_base_dir=Path(env["BACKUP_BASE_DIR"]).expanduser(),
        log_file=Path(env["LOG_FILE"]).expanduser(),
        rclone_remote=env["RCLONE_REMOTE"],
        gdrive_folder=env["GDRIVE_FOLDER"],
        daily_keep=int(env["DAILY_KEEP"]),
        weekly_keep=int(env["WEEKLY_KEEP"]),
        monthly_keep=int(env["MONTHLY_KEEP"]),
        webhook_url=env["WEBHOOK_URL"],
        notify_enabled=str_to_bool(env["NOTIFY_ENABLED"]),
    )


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def log_message(log_file: Path, message: str) -> None:
    ensure_parent_dir(log_file)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def run_command(command: List[str], log_file: Path) -> Tuple[int, str, str]:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.stdout.strip():
        log_message(log_file, f"STDOUT: {result.stdout.strip()}")
    if result.stderr.strip():
        log_message(log_file, f"STDERR: {result.stderr.strip()}")
    return result.returncode, result.stdout, result.stderr


def validate_source_dir(source_dir: Path) -> None:
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")
    if not source_dir.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {source_dir}")


def create_backup_directory(base_dir: Path, project_name: str, now: datetime) -> Path:
    backup_dir = base_dir / project_name / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def create_zip_backup(config: Config, now: datetime) -> Path:
    validate_source_dir(config.source_dir)

    backup_dir = create_backup_directory(config.backup_base_dir, config.project_name, now)
    backup_filename = f"{config.project_name}_{now.strftime('%Y%m%d_%H%M%S')}.zip"
    backup_path = backup_dir / backup_filename

    source_parent = config.source_dir.parent
    source_name = config.source_dir.name

    shutil.make_archive(
        base_name=str(backup_path.with_suffix("")),
        format="zip",
        root_dir=str(source_parent),
        base_dir=str(source_name),
    )

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup ZIP was not created: {backup_path}")

    return backup_path


def upload_to_gdrive(config: Config, backup_path: Path) -> bool:
    destination = f"{config.rclone_remote}:{config.gdrive_folder}"
    command = ["rclone", "copy", str(backup_path), destination]
    code, _, _ = run_command(command, config.log_file)
    return code == 0


def list_all_backups(base_dir: Path, project_name: str) -> List[Path]:
    project_root = base_dir / project_name
    if not project_root.exists():
        return []
    backups = sorted(project_root.rglob("*.zip"))
    return [p for p in backups if p.is_file()]


def parse_backup_datetime(file_path: Path, project_name: str) -> datetime:
    prefix = f"{project_name}_"
    suffix = ".zip"
    name = file_path.name

    if not name.startswith(prefix) or not name.endswith(suffix):
        raise ValueError(f"Unexpected backup filename format: {name}")

    dt_str = name[len(prefix):-len(suffix)]
    return datetime.strptime(dt_str, "%Y%m%d_%H%M%S")


def classify_backups(backups: List[Path], project_name: str) -> Tuple[List[Path], List[Path], List[Path]]:
    daily: List[Path] = []
    weekly: List[Path] = []
    monthly: List[Path] = []

    latest_weekly: Dict[Tuple[int, int], Path] = {}
    latest_monthly: Dict[Tuple[int, int], Path] = {}

    sorted_backups = sorted(
        backups,
        key=lambda p: parse_backup_datetime(p, project_name),
        reverse=True
    )

    daily = sorted_backups

    for backup in sorted_backups:
        dt = parse_backup_datetime(backup, project_name)
        year, week_num, _ = dt.isocalendar()
        if dt.weekday() == 6:
            key = (year, week_num)
            if key not in latest_weekly:
                latest_weekly[key] = backup

    weekly = list(latest_weekly.values())

    for backup in sorted_backups:
        dt = parse_backup_datetime(backup, project_name)
        key = (dt.year, dt.month)
        if key not in latest_monthly:
            latest_monthly[key] = backup

    monthly = list(latest_monthly.values())

    return daily, weekly, monthly


def determine_backups_to_keep(
    backups: List[Path],
    project_name: str,
    daily_keep: int,
    weekly_keep: int,
    monthly_keep: int,
) -> List[Path]:
    daily, weekly, monthly = classify_backups(backups, project_name)

    keep_set = set(daily[:daily_keep])
    keep_set.update(weekly[:weekly_keep])
    keep_set.update(monthly[:monthly_keep])

    return sorted(keep_set, key=lambda p: parse_backup_datetime(p, project_name), reverse=True)


def delete_old_backups(config: Config) -> List[Path]:
    backups = list_all_backups(config.backup_base_dir, config.project_name)
    keep = determine_backups_to_keep(
        backups=backups,
        project_name=config.project_name,
        daily_keep=config.daily_keep,
        weekly_keep=config.weekly_keep,
        monthly_keep=config.monthly_keep,
    )

    keep_set = set(keep)
    deleted: List[Path] = []

    for backup in backups:
        if backup not in keep_set:
            backup.unlink(missing_ok=True)
            deleted.append(backup)

    return deleted


def send_webhook(config: Config, backup_date: str) -> bool:
    payload = {
        "project": config.project_name,
        "date": backup_date,
        "test": "BackupSuccessful"
    }

    command = [
        "curl",
        "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
        config.webhook_url
    ]

    code, _, _ = run_command(command, config.log_file)
    return code == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Automated Backup and Rotation Script")
    parser.add_argument(
        "--config",
        default="/opt/project3/config/project3.env",
        help="Path to config file"
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="Disable webhook notification for this run"
    )
    args = parser.parse_args()

    now = datetime.now()

    try:
        config = load_config(Path(args.config))
        log_message(config.log_file, "========== Backup job started ==========")

        backup_path = create_zip_backup(config, now)
        log_message(config.log_file, f"Backup created: {backup_path}")

        uploaded = upload_to_gdrive(config, backup_path)
        if not uploaded:
            log_message(config.log_file, "Google Drive upload failed")
            return 1

        log_message(config.log_file, f"Upload successful: {backup_path.name}")

        deleted_backups = delete_old_backups(config)
        if deleted_backups:
            for deleted in deleted_backups:
                log_message(config.log_file, f"Deleted old backup: {deleted}")
        else:
            log_message(config.log_file, "No old backups deleted")

        should_notify = config.notify_enabled and not args.no_notify
        if should_notify:
            backup_date = now.strftime("%Y-%m-%d %H:%M:%S")
            notified = send_webhook(config, backup_date)
            if notified:
                log_message(config.log_file, "Webhook notification sent successfully")
            else:
                log_message(config.log_file, "Webhook notification failed")

        log_message(config.log_file, "========== Backup job completed successfully ==========")
        return 0

    except Exception as exc:
        try:
            log_file = Path("/opt/project3/logs/backup.log")
            log_message(log_file, f"Backup job failed: {exc}")
        except Exception:
            pass
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
