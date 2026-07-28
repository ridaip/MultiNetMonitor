import sys
import os
import signal
from PySide6.QtWidgets import QApplication
from multinetmonitor.gui.main_window import MainWindow
from multinetmonitor.gui.theme import load_theme

def main():
    # Force X11/XWayland to allow absolute window positioning on Wayland desktops
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
