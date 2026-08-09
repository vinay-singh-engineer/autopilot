import os
import json
import platform
import threading
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, redirect, url_for, render_template, session

from constants import JobStatus

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = "logs"
VERSION_FILE = os.path.join(BASE_DIR, "..", "VERSION")
JOB_CONFIG_FILE = os.path.join(BASE_DIR, "config", "jobs.json")
JOB_STATUS_FILE = "./config/status.json"
SETTINGS_FILE = "./config/settings.json"

app = Flask(__name__)
app.secret_key = os.getenv("AUTOPILOT_SECRET_KEY", "dev-secret-change-in-production")


def load_settings():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def get_version():
    with open(VERSION_FILE) as f:
        return f.read().strip()


APP_VERSION = get_version()

status_lock = threading.Lock()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def load_status():
    try:
        with open(JOB_STATUS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_status(status):
    with open(JOB_STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)


def load_config():
    try:
        with open(JOB_CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_config(config):
    with open(JOB_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_hostname():
    return platform.node()


def get_timezone():
    return datetime.now().astimezone().tzinfo


def update_logs(log_str):
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = f"{LOG_DIR}/autopilot_{datetime.now().strftime('%Y%m%d')}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        ts = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        f.write(f"{ts} | {log_str}\n")


@app.errorhandler(401)
def unauthorized(e):
    return render_template("401.html"), 401


@app.route("/autopilot/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        valid_user = os.getenv("AUTOPILOT_USERNAME", "admin")
        valid_pass = os.getenv("AUTOPILOT_PASSWORD", "changeme")
        if username == valid_user and password == valid_pass:
            session["user"] = username
            update_logs(f"user={username} | endpoint='/autopilot/login' | result=success")
            return redirect(url_for("index"))
        update_logs(f"user={username} | endpoint='/autopilot/login' | result=failed")
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/autopilot")
@login_required
def index():
    user = session.get("user", "NA")
    update_logs(f"user={user} | endpoint='/autopilot'")
    config = load_config()
    status = load_status()
    jobs_info = []
    for job_name, job in config.items():
        job_status = status.get(job_name, {})
        jobs_info.append({
            "name":       job_name,
            "enabled":    job["enabled"],
            "status":     job_status.get("status", JobStatus.IDLE),
            "start_time": job_status.get("start_time", "—"),
        })
    total = len(jobs_info)
    enabled = sum(1 for j in jobs_info if j["enabled"])
    success = sum(1 for j in jobs_info if j["status"] == JobStatus.SUCCESS)
    running = sum(1 for j in jobs_info if j["status"] == JobStatus.RUNNING)
    failed = sum(1 for j in jobs_info if j["status"] == JobStatus.FAILURE)
    ran = success + failed
    uptime_pct = round(success / ran * 100, 1) if ran > 0 else None
    return render_template(
        "index.html",
        user_name=user,
        app_version=APP_VERSION,
        jobs=jobs_info,
        total=total,
        enabled=enabled,
        success=success,
        running=running,
        uptime_pct=uptime_pct,
    )


@app.route("/autopilot/main")
@login_required
def main():
    import scheduler as sched_module  # noqa: F401 — imported to ensure scheduler is running
    config = load_config()
    status = load_status()
    hostname = get_hostname()
    timezone = get_timezone()
    user = session.get("user", "NA")
    update_logs(f"user={user} | endpoint='/autopilot/main'")

    jobs_info = []
    for job_name, job in config.items():
        job_status = status.get(job_name, {})
        running = job_status.get("running", False)
        jobs_info.append({
            "name":       job_name,
            "enabled":    job["enabled"],
            "cron":       job["cron"],
            "info":       job["info"],
            "status":     job_status.get("status", "-"),
            "start_time": job_status.get("start_time", "-"),
            "end_time":   "-" if running else job_status.get("end_time", "-"),
        })

    return render_template(
        "main.html",
        user_name=user,
        jobs=jobs_info,
        hostname=hostname,
        app_version=APP_VERSION,
        timezone=timezone,
    )


@app.route("/autopilot/main/run/<job_name>", methods=["POST"])
@login_required
def run_now(job_name):
    from runner import run_job
    user = session.get("user", "NA")
    update_logs(f"user={user} | endpoint='/autopilot/main/run/{job_name}'")
    config = load_config()
    if job_name not in config:
        return jsonify({"error": "Job not found"}), 404
    threading.Thread(target=run_job, args=(job_name, config[job_name]["path"])).start()
    return redirect(url_for("main"))


@app.route("/autopilot/main/toggle/<job_name>", methods=["POST"])
@login_required
def toggle_job(job_name):
    user = session.get("user", "NA")
    update_logs(f"user={user} | endpoint='/autopilot/main/toggle/{job_name}'")
    config = load_config()
    if job_name not in config:
        return jsonify({"error": "Job not found"}), 404
    config[job_name]["enabled"] = not config[job_name]["enabled"]
    save_config(config)
    return redirect(url_for("main"))


@app.route("/autopilot/settings", methods=["GET", "POST"])
@login_required
def settings_page():
    user = session.get("user", "NA")
    update_logs(f"user={user} | endpoint='/autopilot/settings'")
    if request.method == "POST":
        current = load_settings()
        current["webhook"]["enabled"] = request.form.get("webhook_enabled") == "on"
        current["webhook"]["url"] = request.form.get("webhook_url", "").strip()
        try:
            current["app"]["logRetention"] = max(1, int(request.form.get("log_retention", 7)))
        except ValueError:
            pass
        current["healthCheck"]["url"] = request.form.get("health_check_url", "").strip()
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
        return redirect(url_for("settings_page") + "?saved=1")
    settings = load_settings()
    saved = request.args.get("saved") == "1"
    return render_template("settings.html", settings=settings, user_name=user,
                           app_version=APP_VERSION, saved=saved)


@app.route("/autopilot/settings/test", methods=["POST"])
@login_required
def test_webhook():
    from notifier import notify
    user = session.get("user", "NA")
    update_logs(f"user={user} | endpoint='/autopilot/settings/test'")
    webhook = load_settings().get("webhook", {})
    result = notify(job="test",
                    description="AutoPilot test notification — webhook is working.",
                    settings=webhook)
    return jsonify({"result": result})


@app.route("/autopilot/logout", methods=["POST"])
@login_required
def logout():
    user = session.get("user", "unknown")
    session.clear()
    update_logs(f"user={user} | endpoint='/autopilot/logout'")
    return render_template("logout.html")


def start_scheduler():
    import scheduler
    scheduler.run_scheduler()


if __name__ == "__main__":
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
else:
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
