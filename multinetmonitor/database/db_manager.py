import sqlite3
import os
import threading
import queue
import time

class DBManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DBManager, cls).__new__(cls)
                cls._instance._init_db()
            return cls._instance

    def _init_db(self):
        from ..utils.config import get_app_dir
        self.db_path = os.path.join(get_app_dir(), 'monitor.db')
        self.write_queue = queue.Queue()
        self.running = True
        
        # Initialize schema
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ping_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_ip TEXT,
                    timestamp REAL,
                    latency REAL,
                    is_error BOOLEAN
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS snmp_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_ip TEXT,
                    timestamp REAL,
                    metric_name TEXT,
                    metric_value REAL,
                    raw_value TEXT
                )
            ''')
            conn.commit()

        # Start background writer thread
        self.writer_thread = threading.Thread(target=self._db_writer_loop, daemon=True)
        self.writer_thread.start()

    def _db_writer_loop(self):
        while self.running:
            try:
                # Batch writes
                queries = []
                while not self.write_queue.empty():
                    queries.append(self.write_queue.get_nowait())
                
                if queries:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        for query, args in queries:
                            cursor.execute(query, args)
                        conn.commit()
                        
                time.sleep(1.0)
            except Exception as e:
                print(f"Database write error: {e}")
                time.sleep(2.0)

    def log_ping(self, ip, latency, is_error):
        query = "INSERT INTO ping_history (target_ip, timestamp, latency, is_error) VALUES (?, ?, ?, ?)"
        args = (ip, time.time(), latency, is_error)
        self.write_queue.put((query, args))

    def log_snmp(self, ip, metric_name, metric_value, raw_value=""):
        query = "INSERT INTO snmp_history (target_ip, timestamp, metric_name, metric_value, raw_value) VALUES (?, ?, ?, ?, ?)"
        args = (ip, time.time(), metric_name, metric_value, raw_value)
        self.write_queue.put((query, args))

    def stop(self):
        self.running = False
        if hasattr(self, 'writer_thread'):
            self.writer_thread.join(timeout=2.0)
