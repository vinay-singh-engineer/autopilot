import os
import time
import random
from datetime import datetime

REPORT_DIR = "./reports"


def run():
    os.makedirs(REPORT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(REPORT_DIR, f"daily_report_{ts}.txt")

    jobs_run = random.randint(18, 34)
    jobs_failed = random.randint(0, 2)
    active_users = random.randint(40, 120)
    avg_duration_ms = random.randint(210, 980)

    time.sleep(random.uniform(1.0, 2.5))

    with open(report_file, "w") as f:
        f.write(f"Daily Summary Report\n")
        f.write(f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Jobs run  : {jobs_run}\n")
        f.write(f"Failed    : {jobs_failed}\n")
        f.write(f"Users     : {active_users}\n")
        f.write(f"Avg dur   : {avg_duration_ms} ms\n")
        f.write(f"Status    : {'OK' if jobs_failed == 0 else 'DEGRADED'}\n")

    print(f"Report written: {report_file} ({jobs_run} jobs, {jobs_failed} failures)")


if __name__ == "__main__":
    run()
