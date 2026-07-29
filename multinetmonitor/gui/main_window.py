from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QScrollArea, QLabel, QCheckBox, QLineEdit)
from PySide6.QtCore import Qt
from .target_window import TargetWindow
from .add_target_dialog import AddTargetDialog
from .scanner_dialog import ScannerDialog
from .discovery_dialog import DiscoveryDialog
import json
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        from PySide6.QtCore import Qt
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        self.resize_margin = 8
        self.resizing_edges = None
        self.drag_start_position = None
        
        self.setWindowTitle("MultiNetMonitor - Control Panel")
        self.resize(900, 700)
        
        from PySide6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)
        scheme = app.styleHints().colorScheme() if app else Qt.ColorScheme.Dark
        self.is_dark_theme = (scheme != Qt.ColorScheme.Light)
        if app:
            app.styleHints().colorSchemeChanged.connect(self.on_system_theme_changed)
        
        from PySide6.QtWidgets import QSystemTrayIcon, QStyle
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.tray_icon.show()
        
        from ..utils.config import get_app_dir
        self.targets_file = os.path.join(get_app_dir(), 'targets.json')
        self.target_configs = []
        self.target_windows = []
        
        self.init_ui()
        self.set_theme(self.is_dark_theme)
        self.load_configs()

    def init_ui(self):
        self.setMinimumSize(500, 400)
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Custom Title Bar for Frameless MainWindow
        title_bar = QHBoxLayout()
        title_icon = QLabel("📡")
        title_icon.setStyleSheet("font-size: 16px;")
        
        title_label = QLabel("MultiNetMonitor - Control Panel")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        title_bar.addWidget(title_icon)
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        
        from PySide6.QtWidgets import QPushButton
        min_btn = QPushButton("🗕")
        min_btn.setObjectName("ToolBtn")
        min_btn.setFixedSize(26, 26)
        min_btn.setToolTip("Minimize")
        min_btn.clicked.connect(self.showMinimized)
        
        max_btn = QPushButton("🗖")
        max_btn.setObjectName("ToolBtn")
        max_btn.setFixedSize(26, 26)
        max_btn.setToolTip("Maximize / Restore")
        max_btn.clicked.connect(self.toggle_maximized)
        
        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseBtn")
        close_btn.setFixedSize(26, 26)
        close_btn.setToolTip("Keluar Aplikasi")
        close_btn.clicked.connect(self.close)
        
        title_bar.addWidget(min_btn)
        title_bar.addWidget(max_btn)
        title_bar.addWidget(close_btn)
        
        main_layout.addLayout(title_bar)
        
        from PySide6.QtWidgets import QTabWidget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # TAB 1: Dashboard
        self.dashboard_tab = QWidget()
        self.init_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        
        # TAB 2: Targets Control Panel
        self.targets_tab = QWidget()
        self.init_targets_tab()
        self.tabs.addTab(self.targets_tab, "Targets")

        # Bottom bar with size grip
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 0, 0, 0)
        bottom_bar.addStretch()
        
        from PySide6.QtWidgets import QSizeGrip
        sg = QSizeGrip(self)
        sg.setFixedSize(14, 14)
        bottom_bar.addWidget(sg, 0, Qt.AlignRight | Qt.AlignBottom)
        
        main_layout.addLayout(bottom_bar)

    def init_dashboard_tab(self):
        import pyqtgraph as pg
        import collections
        from PySide6.QtWidgets import QGroupBox
        from .dashboard_widgets import DonutGaugeWidget, LeaderboardWidget

        layout = QVBoxLayout(self.dashboard_tab)
        
        # Top Row: 3 Donut Gauges
        self.health_gauge = DonutGaugeWidget("Network Health", "%")
        self.latency_gauge = DonutGaugeWidget("Avg Latency", "ms")
        self.total_gauge = DonutGaugeWidget("Total Targets", "")
        
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.health_gauge)
        top_layout.addWidget(self.latency_gauge)
        top_layout.addWidget(self.total_gauge)
        
        layout.addLayout(top_layout)
        
        # Middle Row: Line Chart and Bar Chart
        middle_layout = QHBoxLayout()
        
        # Timeline
        timeline_box = QGroupBox("Global Latency Timeline")
        timeline_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        t_lay = QVBoxLayout(timeline_box)
        self.timeline_plot = pg.PlotWidget(background='#2D2D2D')
        self.timeline_plot.showGrid(x=True, y=True, alpha=0.3)
        self.timeline_plot.setYRange(0, 500)
        self.timeline_curve = self.timeline_plot.plot(pen=pg.mkPen(color='#00E5FF', width=2), fillLevel=0, fillBrush=(0, 229, 255, 30))
        t_lay.addWidget(self.timeline_plot)
        self.global_latency_data = collections.deque([0]*60, maxlen=60)
        
        # Distribution
        dist_box = QGroupBox("Ping Distribution")
        dist_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        d_lay = QVBoxLayout(dist_box)
        self.dist_plot = pg.PlotWidget(background='#2D2D2D')
        self.dist_plot.getAxis('bottom').setTicks([[(1, "<10ms"), (2, "10-50"), (3, "50-150"), (4, ">150"), (5, "Down")]])
        self.dist_bar = pg.BarGraphItem(x=[1, 2, 3, 4, 5], height=[0,0,0,0,0], width=0.6, brush='#00E5FF')
        self.dist_plot.addItem(self.dist_bar)
        d_lay.addWidget(self.dist_plot)
        
        middle_layout.addWidget(timeline_box)
        middle_layout.addWidget(dist_box)
        
        layout.addLayout(middle_layout)
        
        # Row 3: Bandwidth Timeline
        bw_layout = QHBoxLayout()
        bw_box = QGroupBox("Global Bandwidth Throughput (KB)")
        bw_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        b_lay = QVBoxLayout(bw_box)
        self.bw_plot = pg.PlotWidget(background='#2D2D2D')
        self.bw_plot.showGrid(x=True, y=True, alpha=0.3)
        self.bw_plot.addLegend(offset=(10, 10))
        
        self.bw_in_curve = self.bw_plot.plot(name="Traffic In", pen=pg.mkPen(color='#00FF00', width=2))
        self.bw_out_curve = self.bw_plot.plot(name="Traffic Out", pen=pg.mkPen(color='#FF9900', width=2))
        
        b_lay.addWidget(self.bw_plot)
        bw_layout.addWidget(bw_box)
        layout.addLayout(bw_layout)
        
        self.bw_in_data = collections.deque([0]*60, maxlen=60)
        self.bw_out_data = collections.deque([0]*60, maxlen=60)
        
        # Bottom Row: Leaderboards
        bottom_layout = QHBoxLayout()
        self.cpu_leaderboard = LeaderboardWidget("Top 5 CPU", color="#FF9900")
        self.traffic_leaderboard = LeaderboardWidget("Top 5 Traffic (KB)", color="#00E5FF")
        self.ping_leaderboard = LeaderboardWidget("Top 5 Latency", color="#FF3366")
        
        bottom_layout.addWidget(self.cpu_leaderboard)
        bottom_layout.addWidget(self.traffic_leaderboard)
        bottom_layout.addWidget(self.ping_leaderboard)
        
        layout.addLayout(bottom_layout)
        
        from PySide6.QtCore import QTimer
        self.dash_timer = QTimer(self)
        self.dash_timer.timeout.connect(self.update_dashboard_metrics)
        self.dash_timer.start(1000)

    def update_dashboard_stats(self):
        # Called implicitly on changes, handled by timer instead
        pass

    def update_dashboard_metrics(self):
        total = len(self.target_windows)
        if total == 0:
            return
            
        online = 0
        total_latency = 0
        
        dist_counts = [0, 0, 0, 0, 0] # <10, 10-50, 50-150, >150, Down
        
        cpu_list = []
        traffic_list = []
        ping_list = []
        
        total_traffic_in = 0
        total_traffic_out = 0
        
        for w in self.target_windows:
            is_down = w.error_flags[-1] if hasattr(w, 'error_flags') and w.error_flags else True
            lat = w.ping_data[-1] if hasattr(w, 'ping_data') and w.ping_data else 0
            
            if is_down:
                dist_counts[4] += 1
                ping_list.append((w.target_ip, 999, "RTO"))
            else:
                online += 1
                total_latency += lat
                
                if lat < 10: dist_counts[0] += 1
                elif lat < 50: dist_counts[1] += 1
                elif lat < 150: dist_counts[2] += 1
                else: dist_counts[3] += 1
                
                ping_list.append((w.target_ip, lat, f"{lat:.1f} ms"))
                
            if hasattr(w, 'cpu_bar'):
                cpu = w.cpu_bar.value()
                cpu_list.append((w.target_ip, cpu, f"{cpu}%"))
                
            if hasattr(w, 'traffic_in_label'):
                text = w.traffic_in_label.text()
                if "bytes" in text:
                    try:
                        val = int(text.split(" ")[0])
                        kb_val = val / 1024
                        total_traffic_in += kb_val
                        traffic_list.append((w.target_ip, min(100, kb_val / 100), f"{kb_val:.1f} KB"))
                    except:
                        pass
                        
            if hasattr(w, 'traffic_out_label'):
                text_out = w.traffic_out_label.text()
                if "bytes" in text_out:
                    try:
                        val_out = int(text_out.split(" ")[0])
                        kb_out = val_out / 1024
                        total_traffic_out += kb_out
                    except:
                        pass
                
        health_pct = (online / total) * 100
        avg_lat = (total_latency / max(1, online))
        
        self.health_gauge.set_value(health_pct, 100)
        self.latency_gauge.set_value(avg_lat, 500)
        self.total_gauge.set_value(total, total)
        
        self.global_latency_data.append(avg_lat)
        self.timeline_curve.setData(list(self.global_latency_data))
        
        self.bw_in_data.append(total_traffic_in)
        self.bw_out_data.append(total_traffic_out)
        self.bw_in_curve.setData(list(self.bw_in_data))
        self.bw_out_curve.setData(list(self.bw_out_data))
        
        self.dist_bar.setOpts(height=dist_counts)
        
        cpu_list.sort(key=lambda x: x[1], reverse=True)
        self.cpu_leaderboard.update_data(cpu_list[:5])
        
        traffic_list.sort(key=lambda x: float(x[2].split(" ")[0]), reverse=True)
        self.traffic_leaderboard.update_data(traffic_list[:5])
        
        ping_list.sort(key=lambda x: x[1], reverse=True)
        self.ping_leaderboard.update_data(ping_list[:5])

    def init_targets_tab(self):
        layout = QVBoxLayout(self.targets_tab)

        global_layout = QHBoxLayout()
        self.show_all_btn = QPushButton("Show All")
        self.show_all_btn.clicked.connect(self.show_all_targets)
        self.hide_all_btn = QPushButton("Hide All")
        self.hide_all_btn.clicked.connect(self.hide_all_targets)
        
        self.arrange_btn = QPushButton("Auto Arrange Grid...")
        self.arrange_btn.clicked.connect(self.auto_arrange_windows)
        from PySide6.QtWidgets import QComboBox
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("🎨 Cyberpunk Neon (Dark)", "cyberpunk")
        self.theme_combo.addItem("🎨 Midnight Indigo (Dark)", "midnight")
        self.theme_combo.addItem("🎨 Dracula Purple (Dark)", "dracula")
        self.theme_combo.addItem("🎨 Nordic Frost (Dark)", "nord")
        self.theme_combo.addItem("🎨 Crisp Slate (Light)", "light")
        self.theme_combo.currentIndexChanged.connect(self.on_theme_combo_changed)
        
        global_layout.addWidget(self.show_all_btn)
        global_layout.addWidget(self.hide_all_btn)
        global_layout.addWidget(self.arrange_btn)
        global_layout.addWidget(self.theme_combo)
        layout.addLayout(global_layout)
        
        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search targets...")
        self.search_input.textChanged.connect(self.filter_targets)
        layout.addWidget(self.search_input)

        # Actions
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Target")
        self.add_btn.clicked.connect(self.show_add_dialog)
        btn_layout.addWidget(self.add_btn)

        self.scan_btn = QPushButton("OID Scanner")
        self.scan_btn.clicked.connect(self.show_scanner_dialog)
        btn_layout.addWidget(self.scan_btn)
        
        self.discovery_btn = QPushButton("Auto-Discovery")
        self.discovery_btn.clicked.connect(self.show_discovery_dialog)
        btn_layout.addWidget(self.discovery_btn)
        
        layout.addLayout(btn_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.targets_container = QWidget()
        self.targets_layout = QVBoxLayout(self.targets_container)
        self.targets_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.targets_container)
        layout.addWidget(self.scroll_area)

    def filter_targets(self, text):
        query = text.lower()
        for win in self.target_windows:
            if hasattr(win, 'ui_frame'):
                if query in win.target_ip.lower() or query in win.config.get('name', '').lower():
                    win.ui_frame.setVisible(True)
                else:
                    win.ui_frame.setVisible(False)

    def show_all_targets(self):
        for win in self.target_windows:
            if hasattr(win, 'ui_checkbox'):
                win.ui_checkbox.setChecked(True)
        self.raise_()
        self.activateWindow()

    def hide_all_targets(self):
        for win in self.target_windows:
            if hasattr(win, 'ui_checkbox'):
                win.ui_checkbox.setChecked(False)

    def auto_arrange_windows(self):
        from .arrange_dialog import ArrangeDialog
        
        dialog = ArrangeDialog(
            self, 
            default_rows=getattr(self, 'last_grid_rows', 3), 
            default_cols=getattr(self, 'last_grid_cols', 3)
        )
        if not dialog.exec():
            return
            
        data = dialog.get_data()
        screen = data['screen']
        rows = data['rows']
        cols = data['cols']
        direction = data['direction']
        
        self.last_grid_rows = rows
        self.last_grid_cols = cols
        
        screen_geom = screen.availableGeometry()
        
        target_windows = [w for w in self.target_windows if not w.config.get('is_hidden', False)]
        if not target_windows:
            return
            
        win_width = screen_geom.width() // cols
        win_height = screen_geom.height() // rows
        
        for index, w in enumerate(target_windows):
            if direction == "top_right":
                row = index % rows
                col = (cols - 1) - ((index // rows) % cols)
            else: # top_left
                row = index // cols
                col = index % cols
                
            x = screen_geom.x() + (col * win_width)
            y = screen_geom.y() + (row * win_height)
            
            w.show()
            w.setGeometry(x, y, win_width, win_height)
            w.raise_()
            
        self.raise_()
        self.activateWindow()

    def on_theme_combo_changed(self, index):
        theme_key = self.theme_combo.itemData(index)
        self.set_theme(theme_key)

    def toggle_theme(self):
        new_theme = "light" if getattr(self, 'current_theme', 'cyberpunk') != "light" else "cyberpunk"
        self.set_theme(new_theme)

    def set_theme(self, theme_key):
        from .theme import load_theme, get_theme_info
        from PySide6.QtWidgets import QApplication
        import pyqtgraph as pg
        
        if isinstance(theme_key, bool):
            theme_key = "cyberpunk" if theme_key else "light"

        self.current_theme = theme_key
        info = get_theme_info(theme_key)
        self.is_dark_theme = info['is_dark']
        
        # Apply QSS
        qss = load_theme(theme_key)
        QApplication.instance().setStyleSheet(qss)
        
        # Sync combo box
        if hasattr(self, 'theme_combo'):
            idx = self.theme_combo.findData(theme_key)
            if idx >= 0 and self.theme_combo.currentIndex() != idx:
                self.theme_combo.blockSignals(True)
                self.theme_combo.setCurrentIndex(idx)
                self.theme_combo.blockSignals(False)

        # Update Donut Gauges theme
        if hasattr(self, 'health_gauge'):
            self.health_gauge.set_theme(theme_key)
        if hasattr(self, 'latency_gauge'):
            self.latency_gauge.set_theme(theme_key)
        if hasattr(self, 'total_gauge'):
            self.total_gauge.set_theme(theme_key)

        # Update Dashboard Plots
        if hasattr(self, 'timeline_plot'):
            self.timeline_plot.setBackground(info['bg'])
            self.timeline_plot.getAxis('left').setPen(info['grid'])
            self.timeline_plot.getAxis('left').setTextPen(info['text'])
            self.timeline_plot.getAxis('bottom').setPen(info['grid'])
            self.timeline_plot.getAxis('bottom').setTextPen(info['text'])
            if hasattr(self, 'timeline_curve'):
                self.timeline_curve.setPen(pg.mkPen(color=info['primary'], width=2))

        if hasattr(self, 'dist_plot'):
            self.dist_plot.setBackground(info['bg'])
            self.dist_plot.getAxis('left').setPen(info['grid'])
            self.dist_plot.getAxis('left').setTextPen(info['text'])
            self.dist_plot.getAxis('bottom').setPen(info['grid'])
            self.dist_plot.getAxis('bottom').setTextPen(info['text'])
            if hasattr(self, 'dist_bar'):
                self.dist_bar.setOpts(brush=info['primary'])

        # Update all TargetWindows
        for w in getattr(self, 'target_windows', []):
            if hasattr(w, 'update_theme'):
                w.update_theme(theme_key)

    def on_system_theme_changed(self, scheme):
        from PySide6.QtCore import Qt
        is_dark = (scheme != Qt.ColorScheme.Light)
        self.set_theme(is_dark)

    def load_configs(self):
        if os.path.exists(self.targets_file):
            try:
                with open(self.targets_file, 'r') as f:
                    self.target_configs = json.load(f)
                    for conf in self.target_configs:
                        self.init_target(conf)
            except Exception as e:
                print(f"Error loading configs: {e}")

    def save_configs(self):
        try:
            with open(self.targets_file, 'w') as f:
                json.dump(self.target_configs, f, indent=4)
        except Exception as e:
            print(f"Error saving configs: {e}")

    def show_add_dialog(self):
        dialog = AddTargetDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.target_configs.append(data)
            self.save_configs()
            self.init_target(data)

    def show_scanner_dialog(self):
        dialog = ScannerDialog(self)
        dialog.exec()

    def show_discovery_dialog(self):
        dialog = DiscoveryDialog(self)
        dialog.exec()
        
    def init_target(self, config):
        window = TargetWindow(config, self)
        window.update_theme(self.is_dark_theme)
        self.target_windows.append(window)
        
        if not config.get('is_hidden', False):
            window.show()
        else:
            window.hide()
        
        # UI Row
        frame = QWidget()
        frame.setObjectName("TargetRow")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)

        cb = QCheckBox()
        cb.setChecked(not config.get('is_hidden', False))
        cb.toggled.connect(lambda checked, w=window: self.toggle_window(w, checked))
        layout.addWidget(cb)
        
        status_lbl = QLabel("●")
        status_lbl.setStyleSheet("color: #888888; font-size: 14px;") # Gray pending
        layout.addWidget(status_lbl)
        
        window.status_changed.connect(lambda is_online, lbl=status_lbl: self.update_status_indicator(lbl, is_online))

        label_container = QVBoxLayout()
        label_container.setSpacing(0)

        target_name = config.get('name', '').strip()
        if target_name:
            name_lbl = QLabel(target_name)
            name_lbl.setStyleSheet("font-weight: bold; font-size: 13px; border: none;")
            
            ip_lbl = QLabel(config['ip'])
            ip_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; border: none;")
            
            label_container.addWidget(name_lbl)
            label_container.addWidget(ip_lbl)
        else:
            ip_lbl = QLabel(config['ip'])
            ip_lbl.setStyleSheet("font-weight: bold; font-size: 13px; border: none;")
            label_container.addWidget(ip_lbl)

        layout.addLayout(label_container)
        layout.addStretch()

        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setObjectName("EditBtn")
        edit_btn.clicked.connect(lambda _, c=config, w=window: self.edit_target(c, w))
        layout.addWidget(edit_btn)

        pin_btn = QPushButton("📌 Pin")
        pin_btn.setObjectName("PinBtn")
        pin_btn.setCheckable(True)
        pin_btn.setChecked(config.get('always_on_top', False))
        pin_btn.toggled.connect(lambda checked, w=window: w.set_always_on_top(checked))
        layout.addWidget(pin_btn)
        
        del_btn = QPushButton("🗑️ Hapus")
        del_btn.setObjectName("DeleteBtn")
        del_btn.clicked.connect(lambda _, c=config, w=window, f=frame: self.remove_target(c, w, f))
        layout.addWidget(del_btn)
        
        window.ui_frame = frame
        window.ui_checkbox = cb
        window.ui_status_lbl = status_lbl

        self.targets_layout.addWidget(frame)

        if not config.get('is_hidden', False):
            window.show()

    def update_status_indicator(self, lbl, is_online):
        if is_online:
            cyan_color = "#00E5FF" if self.is_dark_theme else "#0091EA"
            lbl.setStyleSheet(f"color: {cyan_color}; font-size: 14px;")
        else:
            lbl.setStyleSheet("color: #FF3366; font-size: 14px;")
            
        # Update dashboard numbers
        self.update_dashboard_stats()

    def toggle_window(self, window, show):
        if show:
            window.show()
            window.config['is_hidden'] = False
        else:
            window.hide()
            window.config['is_hidden'] = True
        self.save_configs()

    def update_ui_for_target(self, config):
        for w in self.target_windows:
            if w.config == config and hasattr(w, 'ui_checkbox'):
                w.ui_checkbox.blockSignals(True)
                w.ui_checkbox.setChecked(not config.get('is_hidden', False))
                w.ui_checkbox.blockSignals(False)

    def edit_target(self, config, window):
        dialog = AddTargetDialog(self, initial_data=config)
        if dialog.exec():
            new_data = dialog.get_data()
            new_data['is_hidden'] = config.get('is_hidden', False)
            new_data['always_on_top'] = config.get('always_on_top', False)
            new_data['geometry'] = config.get('geometry')
            
            idx = self.target_configs.index(config)
            self.target_configs[idx] = new_data
            
            window.stop_workers()
            window.close()
            self.target_windows.remove(window)
            if hasattr(window, 'ui_frame'):
                window.ui_frame.deleteLater()
            
            self.save_configs()
            self.init_target(new_data)

    def remove_target(self, config, window, frame):
        window.stop_workers()
        window.close()
        frame.deleteLater()
        if window in self.target_windows:
            self.target_windows.remove(window)
        if config in self.target_configs:
            self.target_configs.remove(config)
            self.save_configs()

    def toggle_maximized(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _get_resize_edges(self, pos):
        edges = set()
        margin = getattr(self, 'resize_margin', 8)
        if pos.x() <= margin:
            edges.add('left')
        elif pos.x() >= self.width() - margin:
            edges.add('right')
        if pos.y() <= margin:
            edges.add('top')
        elif pos.y() >= self.height() - margin:
            edges.add('bottom')
        return edges

    def _update_cursor_for_edges(self, edges):
        from PySide6.QtCore import Qt
        if ('top' in edges and 'left' in edges) or ('bottom' in edges and 'right' in edges):
            self.setCursor(Qt.SizeFDiagCursor)
        elif ('top' in edges and 'right' in edges) or ('bottom' in edges and 'left' in edges):
            self.setCursor(Qt.SizeBDiagCursor)
        elif 'left' in edges or 'right' in edges:
            self.setCursor(Qt.SizeHorCursor)
        elif 'top' in edges or 'bottom' in edges:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        from PySide6.QtCore import Qt
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            edges = self._get_resize_edges(pos)
            if edges:
                self.resizing_edges = edges
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_geom = self.geometry()
                event.accept()
                return
            
            self.resizing_edges = None
            self.drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        from PySide6.QtCore import Qt
        if not (event.buttons() & Qt.LeftButton):
            pos = event.position().toPoint()
            edges = self._get_resize_edges(pos)
            self._update_cursor_for_edges(edges)
            return

        if hasattr(self, 'resizing_edges') and self.resizing_edges:
            delta = event.globalPosition().toPoint() - self.resize_start_pos
            orig = self.resize_start_geom
            x, y, w, h = orig.x(), orig.y(), orig.width(), orig.height()
            min_w, min_h = self.minimumWidth(), self.minimumHeight()

            if 'right' in self.resizing_edges:
                w = max(min_w, orig.width() + delta.x())
            elif 'left' in self.resizing_edges:
                new_w = max(min_w, orig.width() - delta.x())
                x = orig.x() + (orig.width() - new_w)
                w = new_w

            if 'bottom' in self.resizing_edges:
                h = max(min_h, orig.height() + delta.y())
            elif 'top' in self.resizing_edges:
                new_h = max(min_h, orig.height() - delta.y())
                y = orig.y() + (orig.height() - new_h)
                h = new_h

            self.setGeometry(x, y, w, h)
            event.accept()
            return

        if hasattr(self, 'drag_start_position') and self.drag_start_position is not None:
            new_pos = event.globalPosition().toPoint() - self.drag_start_position
            
            snap_margin = 20
            my_w = self.width()
            my_h = self.height()
            
            # Snap MainWindow against all visible TargetWindows
            for w in getattr(self, 'target_windows', []):
                if w.isHidden(): continue
                other_geom = w.frameGeometry()
                
                # Check horizontal snapping
                if abs((new_pos.x() + my_w) - other_geom.left()) < snap_margin:
                    if new_pos.y() < other_geom.bottom() and (new_pos.y() + my_h) > other_geom.top():
                        new_pos.setX(other_geom.left() - my_w)
                elif abs(new_pos.x() - other_geom.right()) < snap_margin:
                    if new_pos.y() < other_geom.bottom() and (new_pos.y() + my_h) > other_geom.top():
                        new_pos.setX(other_geom.right())
                        
                # Check vertical snapping
                if abs((new_pos.y() + my_h) - other_geom.top()) < snap_margin:
                    if new_pos.x() < other_geom.right() and (new_pos.x() + my_w) > other_geom.left():
                        new_pos.setY(other_geom.top() - my_h)
                elif abs(new_pos.y() - other_geom.bottom()) < snap_margin:
                    if new_pos.x() < other_geom.right() and (new_pos.x() + my_w) > other_geom.left():
                        new_pos.setY(other_geom.bottom())
                        
                # Alignment snapping
                if abs(new_pos.y() - other_geom.top()) < snap_margin:
                    if new_pos.x() < other_geom.right() and (new_pos.x() + my_w) > other_geom.left():
                        new_pos.setY(other_geom.top())
                elif abs((new_pos.y() + my_h) - other_geom.bottom()) < snap_margin:
                    if new_pos.x() < other_geom.right() and (new_pos.x() + my_w) > other_geom.left():
                        new_pos.setY(other_geom.bottom() - my_h)
                        
                if abs(new_pos.x() - other_geom.left()) < snap_margin:
                    if new_pos.y() < other_geom.bottom() and (new_pos.y() + my_h) > other_geom.top():
                        new_pos.setX(other_geom.left())
                elif abs((new_pos.x() + my_w) - other_geom.right()) < snap_margin:
                    if new_pos.y() < other_geom.bottom() and (new_pos.y() + my_h) > other_geom.top():
                        new_pos.setX(other_geom.right() - my_w)
                        
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        from PySide6.QtCore import Qt
        if event.button() == Qt.LeftButton:
            self.resizing_edges = None
            self.drag_start_position = None
            pos = event.position().toPoint()
            edges = self._get_resize_edges(pos)
            self._update_cursor_for_edges(edges)
            event.accept()

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent, Qt
        from PySide6.QtWidgets import QWidget
        if event.type() in (QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
            if isinstance(obj, QWidget) and (obj == self or self.isAncestorOf(obj)):
                global_pos = event.globalPosition().toPoint()
                window_rect = self.frameGeometry()
                local_x = global_pos.x() - window_rect.x()
                local_y = global_pos.y() - window_rect.y()
                margin = getattr(self, 'resize_margin', 10)

                # Active Mouse Drag Resizing (executes anywhere on screen while dragging)
                if event.type() == QEvent.MouseMove and (event.buttons() & Qt.LeftButton):
                    if hasattr(self, 'resizing_edges') and self.resizing_edges:
                        delta = global_pos - self.resize_start_pos
                        orig = self.resize_start_geom
                        x, y, w, h = orig.x(), orig.y(), orig.width(), orig.height()
                        min_w, min_h = self.minimumWidth(), self.minimumHeight()

                        if 'right' in self.resizing_edges:
                            w = max(min_w, orig.width() + delta.x())
                        elif 'left' in self.resizing_edges:
                            new_w = max(min_w, orig.width() - delta.x())
                            x = orig.x() + (orig.width() - new_w)
                            w = new_w

                        if 'bottom' in self.resizing_edges:
                            h = max(min_h, orig.height() + delta.y())
                        elif 'top' in self.resizing_edges:
                            new_h = max(min_h, orig.height() - delta.y())
                            y = orig.y() + (orig.height() - new_h)
                            h = new_h

                        self.setGeometry(x, y, w, h)
                        return True

                if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                    if hasattr(self, 'resizing_edges') and self.resizing_edges:
                        self.resizing_edges = None
                        self.setCursor(Qt.ArrowCursor)
                        return True

                # Hover & Initial Press Detection on Borders
                edges = set()
                if local_x <= margin: edges.add('left')
                elif local_x >= window_rect.width() - margin: edges.add('right')
                if local_y <= margin: edges.add('top')
                elif local_y >= window_rect.height() - margin: edges.add('bottom')

                if event.type() == QEvent.MouseMove and not (event.buttons() & Qt.LeftButton):
                    self._update_cursor_for_edges(edges)

                elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                    if edges:
                        self.resizing_edges = edges
                        self.resize_start_pos = global_pos
                        self.resize_start_geom = self.geometry()
                        return True

        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        for w in self.target_windows:
            w.stop_workers()
            w.close()
        from ..database.db_manager import DBManager
        DBManager().stop()
        super().closeEvent(event)
