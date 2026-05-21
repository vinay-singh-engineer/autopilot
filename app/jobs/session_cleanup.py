import time
import random
from datetime import datetime


def run():
    expired = random.randint(12, 280)
    stale = random.randint(0, 15)

    time.sleep(random.uniform(0.2, 0.8))

    purged = expired + stale
    print(f"Session cleanup complete: {expired} expired + {stale} stale = {purged} sessions purged "
          f"[{datetime.now().strftime('%H:%M:%S')}]")


if __name__ == "__main__":
    run()
