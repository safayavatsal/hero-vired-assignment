import os
import time


class Worker:
    def __init__(self, poll_interval: float = 1.0) -> None:
        self.poll_interval = poll_interval

    def run_once(self) -> None:
        return None

    def run(self) -> None:
        while True:
            self.run_once()
            time.sleep(self.poll_interval)


if __name__ == "__main__":
    Worker(float(os.getenv("WORKER_POLL_INTERVAL", "1"))).run()
