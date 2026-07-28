# AI Notes for MultiNetMonitor

This document contains notes for future AI assistants working on this project.

## Architecture
- **GUI Framework**: PySide6. The application follows a "Control Panel" pattern where the Main Window manages a list of targets, while each Target is its own independent floating `TargetWindow` (using `Qt.Window` flag) that remembers its geometry across sessions.
- **Concurrency**: Use `QThread` and `pyqtSignal` for network monitoring (ping and SNMP) to prevent blocking the GUI.
- **Graphing**: `pyqtgraph` is used for high-performance plotting of latency, utilizing `VTickGroup` for error markers.
- **Dependencies**: Use a virtual environment. Target OS compatibility is Windows, macOS, Linux.

## Known Limitations & Pitfalls
- **Ping**: Uses the OS-native `ping` command via `subprocess` to avoid requiring administrator privileges. The output parsing is OS-dependent (handled in `network/ping_worker.py`).
- **PySNMP**: The project utilizes modern PySNMP v7+ because Python 3.13 completely removed the `asyncore` standard library which legacy PySNMP relied upon. 
- **PySNMP Asyncio Pitfall**: PySNMP 7+ is strictly `asyncio` based. Since we are running it inside a PySide6 `QThread`, each worker must manually spin up its own event loop using `asyncio.run()`. Furthermore, do NOT use `async for` over `bulk_cmd` or `next_cmd` as they are single-step coroutines. For MIB walking, you must use the async generators `walk_cmd` and `bulk_walk_cmd`.

## File Structure
- `main.py`: Entry point
- `multinetmonitor/`
  - `gui/`: UI components (`main_window.py` (Control Panel), `target_window.py` (Floating Monitors), `scanner_dialog.py` (OID Scanner))
  - `network/`: QThread workers (`ping_worker.py`, `snmp_worker.py`, `snmp_scanner.py`)
  - `utils/`: `logger.py` for error logs, `config.py` for target persistence.
