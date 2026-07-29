import os
import sys
import subprocess

def build():
    """
    Builds a standalone Windows executable for MultiNetMonitor using PyInstaller.
    Includes embedded Python runtime and all dependencies (PySide6, PySNMP, PyQtGraph).
    """
    sep = ";" if sys.platform == "win32" else ":"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=MultiNetMonitor",
        f"--add-data=multinetmonitor/gui/*.qss{sep}multinetmonitor/gui",
        f"--add-data=targets.json.example{sep}.",
        "--hidden-import=pyqtgraph",
        "--hidden-import=pysnmp",
        "--hidden-import=pysnmp.hlapi.v3arch.asyncio",
        "main.py"
    ]
    print("Running command:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("\n[SUCCESS] Build complete! Standalone package created at: dist/MultiNetMonitor/")

if __name__ == "__main__":
    build()
