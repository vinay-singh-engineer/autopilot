import json
import time
import random
import requests

SETTINGS_FILE = "./config/settings.json"


def run():
    with open(SETTINGS_FILE) as f:
        url = json.load(f).get("healthCheck", {}).get("url", "")
    if not url:
        print("No health check URL configured.")
        return
    time.sleep(random.uniform(5.0, 8.0))
    resp = requests.get(url, timeout=10, allow_redirects=True)
    if resp.status_code < 400:
        print(f"Health check passed: {url} → HTTP {resp.status_code}")
    else:
        raise RuntimeError(f"Health check failed: {url} → HTTP {resp.status_code}")


if __name__ == "__main__":
    run()
