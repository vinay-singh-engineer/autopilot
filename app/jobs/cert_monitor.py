import time
import random
from datetime import datetime


ENDPOINTS = [
    "api.internal",
    "auth.internal",
    "dashboard.internal",
]

WARN_DAYS = 30


def run():
    time.sleep(random.uniform(6.0, 10.0))

    results = []
    for host in ENDPOINTS:
        days_left = random.randint(12, 180)
        status = "WARN" if days_left < WARN_DAYS else "OK"
        results.append((host, days_left, status))
        print(f"  {host}: {days_left}d remaining [{status}]")

    warnings = [r for r in results if r[2] == "WARN"]
    if warnings:
        hosts = ", ".join(r[0] for r in warnings)
        raise RuntimeError(f"Certificate expiry warning for: {hosts}")

    print(f"cert_monitor: all {len(ENDPOINTS)} certs OK [{datetime.now().strftime('%H:%M:%S')}]")


if __name__ == "__main__":
    run()
