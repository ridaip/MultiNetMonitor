import json
import os
from .logger import get_logger

CONFIG_FILE = "targets.json"

def load_targets():
    if not os.path.exists(CONFIG_FILE):
        return []
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        get_logger().error(f"Failed to load targets from {CONFIG_FILE}: {e}")
        return []

def save_targets(targets):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(targets, f, indent=4)
    except Exception as e:
        get_logger().error(f"Failed to save targets to {CONFIG_FILE}: {e}")
