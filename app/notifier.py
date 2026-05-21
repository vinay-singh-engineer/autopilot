import requests


def notify(job=None, description=None, settings=None):
    """Posts a failure notification to the configured webhook URL (e.g. Slack)."""
    if not settings or not settings.get("enabled", False):
        return "disabled"
    url = settings.get("url", "")
    if not url:
        return "no-url-configured"
    payload = {"text": f"AutoPilot job failure\njob: {job}\ndetail: {description}"}
    try:
        resp = requests.post(url, json=payload, timeout=5)
        return f"notified ({resp.status_code})"
    except Exception as e:
        return f"notify-failed: {e}"
