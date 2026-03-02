import os
import sys
import time
import signal
import queue
import logging
import threading
import subprocess
import requests
from dataclasses import dataclass
from typing import List, Optional

# ==========================================================
# CONFIG
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PYTHON_DEFAULT = sys.executable
PYTHON_312 = ["py", "-3.12"]

LOG_FILE = os.path.join(BASE_DIR, "core.log")

BIBLE_PATH = os.path.join(BASE_DIR, "bible.py")
HABITS_PATH = os.path.join(BASE_DIR, "habits.py")
READER_PATH = os.path.join(BASE_DIR, "reader.py")


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("core")


# ==========================================================
# SERVICE ABSTRACTION
# ==========================================================

@dataclass
class Service:
    name: str
    command: List[str]
    process: Optional[subprocess.Popen] = None

    def start(self):
        logger.info(f"Starting service: {self.name}")
        self.process = subprocess.Popen(self.command)

    def wait(self):
        if self.process:
            return self.process.wait()
        return None

    def stop(self):
        if self.process and self.process.poll() is None:
            logger.info(f"Stopping service: {self.name}")
            self.process.terminate()
            self.process.wait(timeout=5)

    def is_running(self):
        return self.process and self.process.poll() is None


# ==========================================================
# PROCESS MANAGER
# ==========================================================

class ProcessManager:
    def __init__(self):
        self.services = {}
        self.shutdown_event = threading.Event()

    def register(self, key: str, service: Service):
        self.services[key] = service

    def launch(self, key: str):
        service = self.services.get(key)
        if not service:
            logger.error(f"Service not found: {key}")
            return

        try:
            service.start()
            exit_code = service.wait()

            if exit_code != 0:
                logger.error(f"{service.name} exited with code {exit_code}")
            else:
                logger.info(f"{service.name} exited normally")

        except Exception as e:
            logger.exception(f"Service crash: {service.name}")

    def shutdown(self):
        logger.info("Shutting down process manager")
        self.shutdown_event.set()
        for service in self.services.values():
            service.stop()


# ==========================================================
# CONNECTIVITY MONITOR
# ==========================================================

class ConnectivityMonitor(threading.Thread):
    def __init__(self, shutdown_event: threading.Event):
        super().__init__(daemon=True)
        self.shutdown_event = shutdown_event

    def run(self):
        while not self.shutdown_event.is_set():
            try:
                requests.head("https://www.google.com", timeout=3)
                logger.debug("Connectivity OK")
            except Exception:
                logger.warning("Connectivity lost")

            time.sleep(5)


# ==========================================================
# SIGNAL HANDLING
# ==========================================================

def attach_signal_handlers(manager: ProcessManager):
    def handler(signum, frame):
        logger.info(f"Received signal: {signum}")
        manager.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


# ==========================================================
# MENU
# ==========================================================

def menu(manager: ProcessManager):
    while not manager.shutdown_event.is_set():

        print("\n========== CORE TERMINAL ==========")
        print("1. Bible Study")
        print("2. Habits Tracker")
        print("3. PDF Reader (Python 3.12)")
        print("4. Exit")
        print("===================================")

        choice = input("Select option: ").strip()

        if choice == "1":
            manager.launch("bible")
        elif choice == "2":
            manager.launch("habits")
        elif choice == "3":
            manager.launch("reader")
        elif choice == "4":
            manager.shutdown()
            break
        else:
            print("Invalid option.")


# ==========================================================
# ENTRY
# ==========================================================

def main():
    manager = ProcessManager()

    # Register services
    manager.register(
        "bible",
        Service("Bible Study", [PYTHON_DEFAULT, BIBLE_PATH])
    )

    manager.register(
        "habits",
        Service("Habits Tracker", [PYTHON_DEFAULT, HABITS_PATH])
    )

    manager.register(
        "reader",
        Service("PDF Reader", PYTHON_312 + [READER_PATH])
    )

    attach_signal_handlers(manager)

    monitor = ConnectivityMonitor(manager.shutdown_event)
    monitor.start()

    menu(manager)


if __name__ == "__main__":
    main()