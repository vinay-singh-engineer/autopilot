import os
import time
import random
from datetime import datetime

BACKUP_DIR = "./backups"


def run():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"backup_{ts}.tar.gz.sim")
    size_mb = random.randint(120, 480)
    time.sleep(random.uniform(6.0, 12.0))
    with open(backup_file, "w") as f:
        f.write(f"Simulated backup\ntimestamp: {ts}\nsize: {size_mb} MB\nstatus: OK\n")
    print(f"Backup complete: {backup_file} ({size_mb} MB)")


if __name__ == "__main__":
    run()
