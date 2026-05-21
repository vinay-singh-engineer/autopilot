import time
import json
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from runner import run_job

JOB_CONFIG_FILE = "./config/jobs.json"
scheduler = BackgroundScheduler()
current_jobs = {}


def load_config():
    with open(JOB_CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def parse_cron(cron_str):
    parts = cron_str.split()
    return {
        "minute":      parts[0],
        "hour":        parts[1],
        "day":         parts[2],
        "month":       parts[3],
        "day_of_week": parts[4],
    }


def sync_jobs():
    config = load_config()

    for job_name, job_info in config.items():
        job_enabled = job_info.get("enabled", False)

        if not job_enabled and job_name in current_jobs:
            try:
                scheduler.remove_job(job_name)
                print(f"Removed disabled job: {job_name}")
            except Exception as e:
                print(f"Error removing job {job_name}: {e}")
            current_jobs.pop(job_name, None)
            continue

        if job_enabled and job_name not in current_jobs:
            try:
                cron_args = parse_cron(job_info["cron"])
                scheduler.add_job(
                    run_job,
                    "cron",
                    id=job_name,
                    name=job_name,
                    kwargs={"job_name": job_name, "script_path": job_info["path"]},
                    replace_existing=True,
                    **cron_args
                )
                current_jobs[job_name] = job_info
                print(f"Scheduled job: {job_name}")
            except Exception as e:
                print(f"Error scheduling job {job_name}: {e}")

        elif job_enabled and job_name in current_jobs:
            if job_info["cron"] != current_jobs[job_name]["cron"]:
                try:
                    scheduler.remove_job(job_name)
                    cron_args = parse_cron(job_info["cron"])
                    scheduler.add_job(
                        run_job,
                        "cron",
                        id=job_name,
                        name=job_name,
                        kwargs={"job_name": job_name, "script_path": job_info["path"]},
                        replace_existing=True,
                        **cron_args
                    )
                    current_jobs[job_name] = job_info
                    print(f"Rescheduled job with updated cron: {job_name}")
                except Exception as e:
                    print(f"Error updating cron for {job_name}: {e}")


def run_scheduler():
    print("Scheduler started.")
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    try:
        while True:
            sync_jobs()
            time.sleep(30)
    except KeyboardInterrupt:
        print("Scheduler stopped.")


if __name__ == "__main__":
    run_scheduler()
