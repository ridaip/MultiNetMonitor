# Changelog

## [Latest Updates]
### Added
- **OID Hinting Database**: SNMP Scanner now actively checks every OID against an offline database of over 130 common MIB-II entries and displays a hint (e.g. `sysDescr`, `ifInOctets`) directly in the results table.
- **Light Theme**: Added a pristine Light Theme toggle in the main Control Panel.
- **Dedicated QSS Files**: Decoupled the styling from Python logic into dedicated `dark_theme.qss` and `light_theme.qss` files in `multinetmonitor/gui/` for easier customization.
- **Graceful Thread Shutdown**: Added explicit `stop_workers()` execution during the `MainWindow` close event and Target Deletion events, preventing the application from crashing via `QThread: Destroyed while thread is still running` exceptions.
- **Ctrl+C Graceful Exit**: Hooked Python's `SIGINT` signal to safely shut down the application from the terminal.

### Fixed
- **Light Theme Styling**: Fixed hardcoded dark-mode elements (control panel frames, cyan neon text labels) overriding the new Light Theme. Dynamic elements now intelligently shift to readable blue (`#0091EA`) in Light mode instead of maintaining neon cyan (`#00E5FF`).
- **Background Thread Leaks**: Addressed a severe bug where deleted targets or closing application windows would just "hide" the window, leaving the background SNMP and Ping routines firing forever until application exit, heavily draining system resources.

## [Previous Updates]
- Added Advanced Custom OID Graphs (Line Graph, Progress Bar).
- Refactored MainWindow to act as a Control Panel tracking 30+ separate detached TargetWindows.
- Allowed adding OIDs directly from the SNMP Scanner via the 'Add Selected OID to Target' button.
