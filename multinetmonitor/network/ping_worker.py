import subprocess
import platform
import time
import re
from PySide6.QtCore import QThread, Signal
from ..utils.logger import get_logger

class PingWorker(QThread):
    # Emit (latency in ms or None if RTO)
    result_ready = Signal(object)

    def __init__(self, target_ip, interval_sec=1.0):
        super().__init__()
        self.target_ip = target_ip
        self.interval_sec = interval_sec
        self.running = True
        self.logger = get_logger()
        self.os_type = platform.system().lower()

    def run(self):
        while self.running:
            latency = self._ping()
            self.result_ready.emit(latency)
            
            # Sleep in small increments to allow quick termination
            for _ in range(int(self.interval_sec * 10)):
                if not self.running:
                    break
                time.sleep(0.1)

    def _ping(self):
        try:
            # Use shell=False for security, capture output
            extra_kwargs = {}
            if self.os_type == "windows":
                command = ["ping", "-n", "1", "-w", "1000", self.target_ip]
                extra_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            else:
                # macOS doesn't support -W the same way, but most Linux do
                if self.os_type == "darwin":
                    command = ["ping", "-c", "1", "-W", "1000", self.target_ip]
                else:
                    command = ["ping", "-c", "1", "-W", "1", self.target_ip]

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2.0,
                **extra_kwargs
            )

            output = result.stdout
            if result.returncode == 0:
                # Parse latency
                # Look for "time=X.X ms" or "time<Xms" (windows)
                match = re.search(r"time[=<]([0-9.]+)", output)
                if match:
                    return float(match.group(1))
            return None # RTO

        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            self.logger.error(f"Ping exception for {self.target_ip}: {e}")
            return None

    def stop(self):
        self.running = False
