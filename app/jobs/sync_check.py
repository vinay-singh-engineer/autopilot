import os
import random
import time
from datetime import datetime

REPORTS_DIR = "./reports"


def run():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(REPORTS_DIR, f"sync_report_{ts}.txt")
    total = random.randint(1000, 9999)
    synced = total - random.randint(0, 5)
    skipped = total - synced
    time.sleep(random.uniform(7.0, 12.0))
    with open(report_file, "w") as f:
        f.write(f"Sync Report: {ts}\n")
        f.write(f"Total records : {total}\n")
        f.write(f"Synced        : {synced}\n")
        f.write(f"Skipped       : {skipped}\n")
        f.write(f"Status        : {'OK' if skipped == 0 else 'WARN'}\n")
    print(f"Sync complete: {synced}/{total} records. Report: {report_file}")


if __name__ == "__main__":
    run()
