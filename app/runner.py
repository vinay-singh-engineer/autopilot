import json
import os
import threading
import subprocess
import platform
from datetime import datetime

LOG_DIR = "logs"
JOB_STATUS_FILE = "./config/status.json"
SETTINGS_FILE = "./config/settings.json"

status_lock = threading.Lock()


def load_settings():
    with open(SETTINGS_FILE, encoding="utf-8") as f:
        return json.load(f)


def update_job_status(job_name, running=None, status=None, start_time=None, end_time=None):
    with status_lock:
        try:
            with open(JOB_STATUS_FILE, "r", encoding="utf-8") as f:
                status_ = json.load(f)
        except FileNotFoundError:
            status_ = {}

        if job_name not in status_:
            status_[job_name] = {}

        if running is not None:
            status_[job_name]["running"] = running
        if status is not None:
            status_[job_name]["status"] = status
        if start_time is not None:
            status_[job_name]["start_time"] = start_time
        if end_time is not None:
            status_[job_name]["end_time"] = end_time

        with open(JOB_STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_, f, indent=2)


def log_job_execution(job=None, status=None, start=None, end=None, notification=None):
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = f"{LOG_DIR}/autopilot_{datetime.now().strftime('%Y%m%d')}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        ts = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        f.write(f"{ts} | job={job} | status={status} | start={start} | end={end} | notification={notification}\n")  # noqa: E501


def run_job(job_name, script_path):
    import notifier
    status = "Success"
    exception_ = None
    start_time = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
    update_job_status(job_name, running=True, status="Running", start_time=start_time)
    timestamp = datetime.now().strftime("%m%d%Y_%H%M%S")

    try:
        result = subprocess.run(["python3", script_path], check=True, capture_output=True, text=True)
        print(f"{timestamp} [run_job] {job_name} exited with code {result.returncode}")
    except subprocess.CalledProcessError as e:
        print(f"{timestamp} [run_job] {job_name} failed: {e}")
        status = "Failure"
        exception_ = e
    except Exception as e:
        print(f"{timestamp} [run_job] Unexpected error running {job_name}: {e}")
        status = "Failure"
        exception_ = e
    finally:
        end_time = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        update_job_status(job_name, running=False, status=status, end_time=end_time)

        notification = "NA"
        if status == "Failure":
            settings = load_settings()
            notification = notifier.notify(
                job=job_name,
                description=f"host={platform.node()}, error={exception_}",
                settings=settings.get("webhook", {})
            )

        log_job_execution(
            job=job_name,
            status=status,
            start=start_time,
            end=end_time,
            notification=notification
        )
