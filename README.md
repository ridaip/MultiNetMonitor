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

## 🛠️ Installation & Setup

### Prerequisites

- **Python**: `Python 3.10+`
- **System Permissions**: ICMP ping requires network access permissions on Linux/Windows.

### 1. Clone Repository

```bash
git clone https://github.com/your-username/MultiNetMonitor.git
cd MultiNetMonitor
```

### 2. Create Virtual Environment & Install Dependencies

```bash
python3 -m venv venv
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
├── requirements.txt          # Python Dependencies
├── .gitignore                # Git Ignore Rules
├── targets.json.example      # Example Configuration Template
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
