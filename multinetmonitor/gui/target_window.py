import collections
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QCheckBox, QProgressBar, QGroupBox, QFormLayout,
                               QPushButton, QSplitter, QSizeGrip, QStyle)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent
import pyqtgraph as pg
from ..network.ping_worker import PingWorker
from ..network.snmp_worker import SNMPWorker
from ..database.db_manager import DBManager
from ..core.alerter import Alerter
import re

class TargetWindow(QWidget):
    status_changed = Signal(bool)

    def __init__(self, config, main_window, parent=None):
        super().__init__(None)
        
        self.config = config
        self.main_window = main_window 
        self.target_ip = config['ip']
        self.snmp_enabled = config.get('snmp_enabled', False)
        
        self.ping_data = collections.deque(maxlen=100)
        self.error_flags = collections.deque(maxlen=100)
        for _ in range(100):
            self.ping_data.append(0)
            self.error_flags.append(False)
            
        self.custom_graph_data = {}
        for co in self.config.get('custom_oids', []):
            if co.get('type') == 'Line Graph':
                dq = collections.deque(maxlen=100)
                for _ in range(100):
                    dq.append(0)
                self.custom_graph_data[co['name']] = dq
        
        flags = Qt.Window | Qt.FramelessWindowHint
        if self.config.get('always_on_top', False):
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        
        self.setMouseTracking(True)
        self.resizing_edges = None
        self.resize_margin = 8
        self.drag_start_position = None
        
        self.setWindowTitle(f"Monitor: {self.target_ip}")
            
        self.init_ui()
        self.start_workers()
        
        from PySide6.QtCore import QTimer
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._do_save_config_state)
        
        geom = self.config.get('geometry')
        if geom:
            if isinstance(geom, list):
                self.setGeometry(*geom)
            else:
                self.setGeometry(geom['x'], geom['y'], geom['w'], geom['h'])
        else:
            self.resize(400, 300)

    def init_ui(self):
        self.setMinimumSize(100, 80)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)
        self.setStyleSheet("QGroupBox { font-weight: bold; }")

        # Top Bar
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        title_container = QVBoxLayout()
        title_container.setSpacing(0)

        target_name = self.config.get('name', '').strip()
        if target_name:
            title_label = QLabel(target_name)
            title_label.setStyleSheet("font-size: 15px; font-weight: bold;")
            
            sub_label = QLabel(f"IP: {self.target_ip}")
            sub_label.setStyleSheet("font-size: 11px; color: #94a3b8;")
            
            title_container.addWidget(title_label)
            title_container.addWidget(sub_label)
        else:
            title_label = QLabel(f"{self.target_ip}")
            title_label.setStyleSheet("font-size: 15px; font-weight: bold;")
            title_container.addWidget(title_label)

        top_layout.addLayout(title_container)
        
        self.graph_btn = QPushButton("📈")
        self.graph_btn.setObjectName("ToggleBtn")
        self.graph_btn.setCheckable(True)
        self.graph_btn.setChecked(True)
        self.graph_btn.setFixedSize(26, 26)
        self.graph_btn.setToolTip("Tampilkan / Sembunyikan Grafik Ping")
        self.graph_btn.toggled.connect(self.toggle_graph)
        top_layout.addWidget(self.graph_btn)
        
        if self.snmp_enabled:
            self.snmp_btn = QPushButton("⚡")
            self.snmp_btn.setObjectName("ToggleBtn")
            self.snmp_btn.setCheckable(True)
            self.snmp_btn.setChecked(True)
            self.snmp_btn.setFixedSize(26, 26)
            self.snmp_btn.setToolTip("Tampilkan / Sembunyikan Metrik SNMP")
            self.snmp_btn.toggled.connect(self.toggle_snmp)
            top_layout.addWidget(self.snmp_btn)

            self.orient_btn = QPushButton("🔀")
            self.orient_btn.setObjectName("ToolBtn")
            self.orient_btn.setFixedSize(26, 26)
            self.orient_btn.setToolTip("Ganti Tata Letak (Horizontal / Vertikal)")
            self.orient_btn.clicked.connect(self.toggle_orientation)
            top_layout.addWidget(self.orient_btn)

        top_layout.addStretch()
        
        self.pin_btn = QPushButton("📌")
        self.pin_btn.setObjectName("PinBtn")
        self.pin_btn.setCheckable(True)
        self.pin_btn.setChecked(self.config.get('always_on_top', False))
        self.pin_btn.setFixedSize(26, 26)
        self.pin_btn.setToolTip("Pin Window (Always on Top)")
        self.pin_btn.toggled.connect(self.set_always_on_top)
        top_layout.addWidget(self.pin_btn)
        
        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseBtn")
        close_btn.setFixedSize(26, 26)
        close_btn.setToolTip("Tutup / Sembunyikan Window")
        close_btn.clicked.connect(self.close)
        top_layout.addWidget(close_btn)
        
        main_layout.addLayout(top_layout)

        # Ping Graph
        self.graph_box = QGroupBox("Ping Latency (ms)")
        self.graph_box.setMinimumSize(50, 50)
        graph_layout = QVBoxLayout(self.graph_box)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setMinimumSize(50, 50)
        self.plot_widget.setBackground('#2D2D2D')
        self.plot_widget.setYRange(0, 500, padding=0)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.getAxis('left').setPen('#888888')
        self.plot_widget.getAxis('left').setTextPen('#888888')
        self.plot_widget.getAxis('bottom').setPen('#888888')
        self.plot_widget.getAxis('bottom').setTextPen('#888888')
        self.plot_curve = self.plot_widget.plot(
            pen=pg.mkPen(color='#00E5FF', width=2),
            fillLevel=0, 
            fillBrush=(0, 229, 255, 30)
        )
        
        self.error_ticks = pg.VTickGroup(xvals=[], yrange=[0, 1], pen=pg.mkPen('#FF3366', width=2))
        self.plot_widget.addItem(self.error_ticks)
        
        self.current_ping_label = QLabel("Current: -- ms")
        
        graph_layout.addWidget(self.current_ping_label)
        graph_layout.addWidget(self.plot_widget)

        # SNMP Data
        if self.snmp_enabled:
            self.snmp_box = QGroupBox("SNMP Metrics")
            self.snmp_box.setMinimumSize(50, 50)
            snmp_layout = QFormLayout(self.snmp_box)
            
            self.uptime_label = QLabel("--")
            snmp_layout.addRow("Uptime:", self.uptime_label)
            
            self.cpu_bar = QProgressBar()
            self.cpu_bar.setRange(0, 100)
            self.cpu_bar.setValue(0)
            snmp_layout.addRow("CPU Usage:", self.cpu_bar)
            
            self.traffic_in_label = QLabel("-- bytes")
            self.traffic_out_label = QLabel("-- bytes")
            snmp_layout.addRow("Traffic In:", self.traffic_in_label)
            snmp_layout.addRow("Traffic Out:", self.traffic_out_label)
            
            self.custom_widgets = {}
            for co in self.config.get('custom_oids', []):
                name = co['name']
                vtype = co.get('type', 'Text')
                
                if vtype == 'Progress Bar':
                    bar = QProgressBar()
                    bar.setRange(0, 100)
                    bar.setValue(0)
                    snmp_layout.addRow(f"{name}:", bar)
                    self.custom_widgets[name] = {'widget': bar, 'type': vtype}
                elif vtype == 'Line Graph':
                    plot_wdg = pg.PlotWidget(background='#2D2D2D')
                    plot_wdg.setFixedHeight(100)
                    plot_wdg.showGrid(x=True, y=True, alpha=0.3)
                    plot_wdg.getAxis('left').setPen('#888888')
                    plot_wdg.getAxis('left').setTextPen('#888888')
                    plot_wdg.getAxis('bottom').setPen('#888888')
                    plot_wdg.getAxis('bottom').setTextPen('#888888')
                    curve = plot_wdg.plot(pen=pg.mkPen(color='#00E5FF', width=2), fillLevel=0, fillBrush=(0, 229, 255, 30))
                    
                    lbl = QLabel("--")
                    lbl.setObjectName("CustomGraphLabel")
                    lbl.setStyleSheet("color: #00E5FF;")
                    
                    container = QVBoxLayout()
                    container.addWidget(lbl)
                    container.addWidget(plot_wdg)
                    
                    snmp_layout.addRow(f"{name}:", container)
                    self.custom_widgets[name] = {'widget': lbl, 'curve': curve, 'type': vtype, 'plot_wdg': plot_wdg}
                else:
                    lbl = QLabel("--")
                    snmp_layout.addRow(f"{name}:", lbl)
                    self.custom_widgets[name] = {'widget': lbl, 'type': vtype}
            
        saved_orient = self.config.get('splitter_orientation', 'horizontal')
        orient = Qt.Vertical if saved_orient == 'vertical' else Qt.Horizontal
        
        self.splitter = QSplitter(orient)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.graph_box)
        
        if self.snmp_enabled:
            self.splitter.addWidget(self.snmp_box)
            
        saved_sizes = self.config.get('splitter_sizes')
        if saved_sizes:
            self.splitter.setSizes(saved_sizes)

        self.splitter.splitterMoved.connect(lambda pos, index: self.save_config_state())
        main_layout.addWidget(self.splitter)
        
        # Bottom Status Bar Frame
        from PySide6.QtWidgets import QFrame
        self.status_bar_frame = QFrame()
        self.status_bar_frame.setObjectName("StatusBarFrame")
        status_bar_layout = QHBoxLayout(self.status_bar_frame)
        status_bar_layout.setContentsMargins(6, 3, 6, 3)
        status_bar_layout.setSpacing(6)
        
        self.status_badge = QLabel("● ONLINE")
        self.status_badge.setStyleSheet("font-weight: bold; font-size: 11px; color: #10B981;")
        
        self.ping_stats_label = QLabel("Min: -- | Avg: -- | Max: -- | Loss: 0%")
        self.ping_stats_label.setStyleSheet("font-weight: 500; font-size: 11px;")
        
        sg = QSizeGrip(self)
        sg.setFixedSize(12, 12)
        
        status_bar_layout.addWidget(self.status_badge)
        status_bar_layout.addStretch()
        status_bar_layout.addWidget(self.ping_stats_label)
        status_bar_layout.addWidget(sg, 0, Qt.AlignRight | Qt.AlignBottom)
        
        main_layout.addWidget(self.status_bar_frame)

    def update_theme(self, theme_key):
        from .theme import get_theme_info
        info = get_theme_info(theme_key)
        
        bg = info['bg']
        grid = info['grid']
        primary = info['primary']
        text = info['text']
        
        if hasattr(self, 'current_ping_label'):
            self.current_ping_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {primary};")
                
        if hasattr(self, 'plot_widget'):
            self.plot_widget.setBackground(bg)
            self.plot_widget.getAxis('left').setPen(grid)
            self.plot_widget.getAxis('left').setTextPen(text)
            self.plot_widget.getAxis('bottom').setPen(grid)
            self.plot_widget.getAxis('bottom').setTextPen(text)
            if hasattr(self, 'plot_curve'):
                self.plot_curve.setPen(pg.mkPen(color=primary, width=2))
            
        for _, cw in getattr(self, 'custom_widgets', {}).items():
            if cw['type'] == 'Line Graph':
                if 'widget' in cw:
                    cw['widget'].setStyleSheet(f"font-weight: bold; color: {primary};")
                if 'plot_wdg' in cw:
                    plot_wdg = cw['plot_wdg']
                    plot_wdg.setBackground(bg)
                    plot_wdg.getAxis('left').setPen(grid)
                    plot_wdg.getAxis('left').setTextPen(text)
                    plot_wdg.getAxis('bottom').setPen(grid)
                    plot_wdg.getAxis('bottom').setTextPen(text)
                if 'curve' in cw:
                    cw['curve'].setPen(pg.mkPen(color=primary, width=2))

    def toggle_graph(self, checked):
        self.graph_box.setVisible(checked)

    def toggle_snmp(self, checked):
        if hasattr(self, 'snmp_box'):
            self.snmp_box.setVisible(checked)

    def start_workers(self):
        self.ping_worker = PingWorker(self.target_ip)
        self.ping_worker.result_ready.connect(self.update_ping)
        self.ping_worker.start()

        if self.snmp_enabled:
            v3_creds = None
            if self.config.get('snmp_version') == 3:
                v3_creds = {
                    'user': self.config.get('v3_user', ''),
                    'auth_proto': self.config.get('v3_auth_proto', 'NONE'),
                    'auth_key': self.config.get('v3_auth_key', ''),
                    'priv_proto': self.config.get('v3_priv_proto', 'NONE'),
                    'priv_key': self.config.get('v3_priv_key', '')
                }
                
            self.snmp_worker = SNMPWorker(
                self.target_ip, 
                self.config.get('snmp_community', 'public'), 
                self.config.get('snmp_version', 2),
                self.config.get('snmp_port', 161),
                custom_oids=self.config.get('custom_oids', []),
                v3_creds=v3_creds
            )
            self.snmp_worker.result_ready.connect(self.update_snmp)
            self.snmp_worker.start()

    def update_ping(self, latency):
        is_dark = getattr(self.main_window, 'is_dark_theme', True)
        cyan_color = '#00E5FF' if is_dark else '#0091EA'
        db = DBManager()
        
        if latency is None:
            self.ping_data.append(0) 
            self.error_flags.append(True)
            self.current_ping_label.setText("Current: RTO / Offline")
            self.current_ping_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #FF3366;")
            if hasattr(self, 'status_badge'):
                self.status_badge.setText("● OFFLINE")
                self.status_badge.setStyleSheet("font-weight: bold; font-size: 11px; color: #FF3366;")
            self.status_changed.emit(False)
            db.log_ping(self.target_ip, 0, True)
            Alerter().report_ping(self.target_ip, True)
        else:
            self.ping_data.append(latency)
            self.error_flags.append(False)
            self.current_ping_label.setText(f"Current: {latency:.1f} ms")
            self.current_ping_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {cyan_color};")
            if hasattr(self, 'status_badge'):
                self.status_badge.setText("● ONLINE")
                self.status_badge.setStyleSheet("font-weight: bold; font-size: 11px; color: #10B981;")
            self.status_changed.emit(True)
            db.log_ping(self.target_ip, latency, False)
            Alerter().report_ping(self.target_ip, False)
            
        self.plot_curve.setData(list(self.ping_data))
        
        xvals = [i for i, err in enumerate(self.error_flags) if err]
        self.error_ticks.setXVals(xvals)
        
        # Calculate statistics for bottom status bar
        if hasattr(self, 'ping_stats_label'):
            valid_pings = [p for p, err in zip(self.ping_data, self.error_flags) if not err]
            total_count = len(self.ping_data)
            fail_count = sum(1 for err in self.error_flags if err)
            loss_pct = (fail_count / total_count * 100.0) if total_count > 0 else 0.0
            
            if valid_pings:
                min_p = min(valid_pings)
                avg_p = sum(valid_pings) / len(valid_pings)
                max_p = max(valid_pings)
                self.ping_stats_label.setText(f"Min: {min_p:.1f}ms | Avg: {avg_p:.1f}ms | Max: {max_p:.1f}ms | Loss: {loss_pct:.0f}%")
            else:
                self.ping_stats_label.setText(f"Min: -- | Avg: -- | Max: -- | Loss: {loss_pct:.0f}%")
        
    def _parse_numeric(self, val_str):
        matches = re.findall(r"[-+]?\d*\.\d+|\d+", str(val_str).replace(",", ""))
        if matches:
            return float(matches[0])
        return 0.0

    def update_snmp(self, data):
        db = DBManager()
        
        if 'error' in data:
            self.uptime_label.setText(f"Error: {data['error']}")
            return
            
        if 'uptime' in data:
            self.uptime_label.setText(data['uptime'])
            
        if 'cpu' in data and data['cpu'] is not None:
            self.cpu_bar.setValue(data['cpu'])
            db.log_snmp(self.target_ip, "cpu", data['cpu'])
            
        if 'traffic_in' in data:
            self.traffic_in_label.setText(f"{data['traffic_in']} bytes")
            db.log_snmp(self.target_ip, "traffic_in", data['traffic_in'])
            
        if 'traffic_out' in data:
            self.traffic_out_label.setText(f"{data['traffic_out']} bytes")
            db.log_snmp(self.target_ip, "traffic_out", data['traffic_out'])
            
        if 'custom' in data:
            for name, val_str in data['custom'].items():
                if name in getattr(self, 'custom_widgets', {}):
                    cw = self.custom_widgets[name]
                    vtype = cw['type']
                    
                    if vtype == 'Progress Bar':
                        num = self._parse_numeric(val_str)
                        cw['widget'].setValue(min(max(int(num), 0), 100))
                        db.log_snmp(self.target_ip, name, num, val_str)
                    elif vtype == 'Line Graph':
                        num = self._parse_numeric(val_str)
                        self.custom_graph_data[name].append(num)
                        cw['curve'].setData(list(self.custom_graph_data[name]))
                        cw['widget'].setText(val_str)
                        db.log_snmp(self.target_ip, name, num, val_str)
                    else:
                        num = self._parse_numeric(val_str)
                        cw['widget'].setText(val_str)
                        db.log_snmp(self.target_ip, name, num, val_str)

    def stop_workers(self):
        if hasattr(self, 'ping_worker'):
            self.ping_worker.stop()
            self.ping_worker.wait()
        if hasattr(self, 'snmp_worker'):
            self.snmp_worker.stop()
            self.snmp_worker.wait()

    def set_always_on_top(self, on_top):
        self.config['always_on_top'] = on_top
        flags = self.windowFlags()
        if on_top:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        self.save_config_state()

    def closeEvent(self, event=None):
        self.hide()
        self.config['is_hidden'] = True
        self.main_window.update_ui_for_target(self.config)
        self.save_config_state()
        if hasattr(event, 'ignore'):
            event.ignore()

    def resizeEvent(self, event):
        self.save_config_state()
        super().resizeEvent(event)

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
            self.save_config_state()
            event.accept()
            return

        if hasattr(self, 'drag_start_position') and self.drag_start_position is not None:
            new_pos = event.globalPosition().toPoint() - self.drag_start_position
            
            snap_margin = 20
            my_w = self.width()
            my_h = self.height()
            
            for w in self.main_window.target_windows:
                if w == self or w.isHidden(): continue
                other_geom = w.frameGeometry()
                
                # Check horizontal snapping (My Right to Their Left)
                if abs((new_pos.x() + my_w) - other_geom.left()) < snap_margin:
                    if new_pos.y() < other_geom.bottom() and (new_pos.y() + my_h) > other_geom.top():
                        new_pos.setX(other_geom.left() - my_w)
                # (My Left to Their Right)
                elif abs(new_pos.x() - other_geom.right()) < snap_margin:
                    if new_pos.y() < other_geom.bottom() and (new_pos.y() + my_h) > other_geom.top():
                        new_pos.setX(other_geom.right())
                        
                # Check vertical snapping (My Bottom to Their Top)
                if abs((new_pos.y() + my_h) - other_geom.top()) < snap_margin:
                    if new_pos.x() < other_geom.right() and (new_pos.x() + my_w) > other_geom.left():
                        new_pos.setY(other_geom.top() - my_h)
                # (My Top to Their Bottom)
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
            self.save_config_state()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.resizing_edges = None
            self.drag_start_position = None
            pos = event.position().toPoint()
            edges = self._get_resize_edges(pos)
            self._update_cursor_for_edges(edges)
            event.accept()

    def toggle_orientation(self):
        if not hasattr(self, 'splitter'):
            return
        if self.splitter.orientation() == Qt.Horizontal:
            self.splitter.setOrientation(Qt.Vertical)
        else:
            self.splitter.setOrientation(Qt.Horizontal)
        self.save_config_state()

    def save_config_state(self):
        # Debounce to prevent massive I/O overhead
        if hasattr(self, 'save_timer'):
            self.save_timer.start(500)

    def _do_save_config_state(self):
        self.config['geometry'] = {
            'x': self.x(), 'y': self.y(),
            'w': self.width(), 'h': self.height()
        }
        if hasattr(self, 'splitter'):
            self.config['splitter_sizes'] = self.splitter.sizes()
            orient = 'vertical' if self.splitter.orientation() == Qt.Vertical else 'horizontal'
            self.config['splitter_orientation'] = orient
        self.main_window.save_configs()
