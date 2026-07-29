import json
import os
import sys
from .logger import get_logger

def get_app_dir():
    """Returns the base application directory where the .exe or main.py resides."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # When running from source
    main_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    if os.path.exists(os.path.join(main_dir, 'main.py')):
        return main_dir
    # Fallback to current working directory
    return os.getcwd()

CONFIG_FILE = os.path.join(get_app_dir(), "targets.json")

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

