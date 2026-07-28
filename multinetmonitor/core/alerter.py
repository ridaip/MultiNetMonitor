import urllib.request
import urllib.parse
import threading

class Alerter:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Alerter, cls).__new__(cls)
                cls._instance._init()
            return cls._instance
            
    def _init(self):
        self.telegram_token = "" # Optional Telegram config
        self.telegram_chat_id = "" # Optional Telegram config
        self.tray_icon = None # Configured by main_window.py
        
        self.rto_counters = {}
        self.rto_threshold = 3
        self.alerted_hosts = set()
        
    def report_ping(self, ip, is_error):
        if is_error:
            self.rto_counters[ip] = self.rto_counters.get(ip, 0) + 1
            if self.rto_counters[ip] >= self.rto_threshold and ip not in self.alerted_hosts:
                self.trigger_alert(f"Host Down: {ip}", f"Device {ip} has failed to respond {self.rto_threshold} times.")
                self.alerted_hosts.add(ip)
        else:
            if ip in self.alerted_hosts:
                self.trigger_alert(f"Host Recovered: {ip}", f"Device {ip} is back online.")
                self.alerted_hosts.remove(ip)
            self.rto_counters[ip] = 0
            
    def trigger_alert(self, title, message):
        # 1. Desktop Notification
        if self.tray_icon and self.tray_icon.isSystemTrayAvailable():
            from PySide6.QtWidgets import QSystemTrayIcon
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.Warning, 5000)
        else:
            print(f"ALERT: {title} - {message}")
            
        # 2. Telegram Notification (if configured)
        if self.telegram_token and self.telegram_chat_id:
            def send_tg():
                try:
                    msg = urllib.parse.quote(f"*{title}*\n{message}")
                    url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage?chat_id={self.telegram_chat_id}&text={msg}&parse_mode=Markdown"
                    urllib.request.urlopen(url, timeout=5)
                except Exception as e:
                    print(f"Telegram error: {e}")
            threading.Thread(target=send_tg, daemon=True).start()
