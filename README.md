# MultiNetMonitor 📡

**MultiNetMonitor** is a modern, high-performance desktop application for real-time network latency, ICMP ping, and SNMP metric monitoring. Built with Python 3, PySide6 (Qt 6), PyQtGraph, and PySNMP 7+, it offers a dynamic multi-theme dashboard and customizable floating target monitor widgets.

---

## ✨ Features

- **📡 Real-Time ICMP & SNMP Monitoring**: Monitor ICMP latency, CPU usage, Uptime, Network Traffic In/Out, and custom OIDs with asynchronous workers.
- **🎨 5 Aesthetic Modern Themes**: Toggle between Cyberpunk Neon, Midnight Indigo, Dracula Purple, Nordic Frost, and Crisp Slate.
- **🖼️ Frameless Interactive Widgets**: Floating, frameless monitor widgets with 8-directional edge/corner resizing, Always-on-Top pin mode, and status bar statistics (Min, Avg, Max, Loss %).
- **📐 Interactive Auto-Arrange Grid**: Automatically arrange floating monitor widgets in custom rows and columns across multi-monitor setups.
- **🏷️ Target Labeling**: Assign custom device names/labels (e.g. `Server Utama 192.168.1.1`) with optimized layout hierarchy.
- **🔍 Subnet & OID Scanners**: Built-in network subnet discovery scanner and SNMP OID browser/scanner.
- **📊 Interactive Dashboard**: High-level network health donut gauges, latency timeline graphs, and top target leaderboards.
- **💾 SQLite Database Logging**: Asynchronous background queue logging of all metrics to SQLite (`monitor.db`).

---

## 📦 Standalone Windows Release (No Python Required)

End-users on Windows do **NOT** need to install Python or any dependencies!

1. Download **`MultiNetMonitor-Windows-x64.zip`** from the [GitHub Releases](https://github.com/ridaip/MultiNetMonitor/releases) page.
2. Extract the `.zip` package.
3. Double-click **`MultiNetMonitor.exe`** to launch instantly.

---

## 🛠️ Building Standalone Windows Executable Locally

To bundle Python runtime and all libraries into a standalone Windows package:

```bash
pip install -r requirements.txt
pip install pyinstaller
python build_exe.py
```

The output standalone folder will be generated in `dist/MultiNetMonitor/`.

---

## 💻 Developer Installation & Setup

### Prerequisites

- **Python**: `Python 3.10+`
- **System Permissions**: ICMP ping requires network access permissions.

### 1. Clone Repository

```bash
git clone https://github.com/ridaip/MultiNetMonitor.git
cd MultiNetMonitor
```

### 2. Create Virtual Environment & Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run Application

```bash
python main.py
```

---

## 📁 Project Structure

```
MultiNetMonitor/
├── main.py                   # Application Entry Point
├── build_exe.py              # Windows PyInstaller Build Script
├── requirements.txt          # Python Dependencies
├── .gitignore                # Git Ignore Rules
├── targets.json.example      # Example Configuration Template
├── .github/workflows/        # Automated GitHub Actions Windows Release Builder
├── multinetmonitor/
│   ├── core/                 # Core Alerters & Utilities
│   ├── database/             # SQLite DB Queue Writer
│   ├── gui/                  # PySide6 GUI Windows & Stylesheets
│   ├── network/              # Async Ping & SNMP Network Workers
│   └── utils/                # Logging System
```

---

## 📄 License

Distributed under the MIT License.
