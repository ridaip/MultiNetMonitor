import logging
import os

LOG_FILE = "error.log"

def setup_logger():
    logger = logging.getLogger("MultiNetMonitor")
    logger.setLevel(logging.ERROR)
    
    # Avoid adding multiple handlers if setup is called multiple times
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

def get_logger():
    return logging.getLogger("MultiNetMonitor")
