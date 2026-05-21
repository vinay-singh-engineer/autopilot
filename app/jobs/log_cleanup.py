import os
import json
import time
import random
from datetime import datetime, timedelta

LOGS_DIR = "./logs"
SETTINGS_FILE = "./config/settings.json"


def run():
    with open(SETTINGS_FILE) as f:
        retention_days = json.load(f)["app"]["logRetention"]
    cutoff = datetime.now() - timedelta(days=retention_days)
    removed = 0
    if os.path.exists(LOGS_DIR):
        for filename in os.listdir(LOGS_DIR):
            path = os.path.join(LOGS_DIR, filename)
            if os.path.isfile(path):
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                if mtime < cutoff:
                    os.remove(path)
                    removed += 1
                    print(f"Removed: {filename}")
    print(f"Log cleanup complete. Removed {removed} file(s) older than {retention_days} days.")
    time.sleep(random.uniform(5.0, 9.0))


if __name__ == "__main__":
    run()
