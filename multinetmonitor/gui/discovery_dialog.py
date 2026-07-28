import ipaddress
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QProgressBar, QMessageBox)
from PySide6.QtCore import Qt
from ..network.subnet_scanner import SubnetScannerWorker

class DiscoveryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Auto-Discovery Scanner")
        self.resize(600, 400)
        self.parent_window = parent
        
        self.worker = None
        self.found_devices = []
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Top Input Area
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Subnet (CIDR):"))
        self.subnet_input = QLineEdit("192.168.1.0/24")
        input_layout.addWidget(self.subnet_input)
        
        input_layout.addWidget(QLabel("Community:"))
        self.community_input = QLineEdit("public")
        input_layout.addWidget(self.community_input)
        
        self.scan_btn = QPushButton("Start Discovery")
        self.scan_btn.clicked.connect(self.toggle_scan)
        input_layout.addWidget(self.scan_btn)
        
        layout.addLayout(input_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Results Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Add", "IP Address", "Status", "sysName"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)
        
        # Bottom Buttons
        btn_layout = QHBoxLayout()
        self.add_selected_btn = QPushButton("Add Selected to Monitor")
        self.add_selected_btn.clicked.connect(self.add_selected)
        btn_layout.addStretch()
        btn_layout.addWidget(self.add_selected_btn)
        
        layout.addLayout(btn_layout)

    def toggle_scan(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            self.scan_btn.setText("Start Discovery")
            return
            
        subnet_str = self.subnet_input.text().strip()
        try:
            ipaddress.IPv4Network(subnet_str, strict=False)
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid Subnet format. Use CIDR (e.g. 192.168.1.0/24)")
            return
            
        self.table.setRowCount(0)
        self.found_devices.clear()
        self.progress_bar.setValue(0)
        
        self.scan_btn.setText("Stop Scan")
        
        self.worker = SubnetScannerWorker(subnet_str, self.community_input.text().strip())
        self.worker.host_found.connect(self.on_host_found)
        self.worker.progress_update.connect(self.on_progress)
        self.worker.scan_finished.connect(self.on_scan_finished)
        self.worker.start()

    def on_host_found(self, ip, status, sys_name):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Add Checkbox
        cb = QTableWidgetItem()
        cb.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        cb.setCheckState(Qt.Checked)
        self.table.setItem(row, 0, cb)
        
        self.table.setItem(row, 1, QTableWidgetItem(ip))
        
        status_item = QTableWidgetItem(status)
        status_item.setForeground(Qt.green)
        self.table.setItem(row, 2, status_item)
        
        self.table.setItem(row, 3, QTableWidgetItem(sys_name))
        
        self.found_devices.append({
            'ip': ip,
            'sys_name': sys_name
        })

    def on_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def on_scan_finished(self):
        self.scan_btn.setText("Start Discovery")

    def add_selected(self):
        if not self.parent_window:
            return
            
        added_count = 0
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).checkState() == Qt.Checked:
                ip = self.table.item(row, 1).text()
                sys_name = self.table.item(row, 3).text()
                
                # Create config
                config = {
                    'ip': ip,
                    'name': sys_name,
                    'snmp_enabled': True,
                    'snmp_version': 2,
                    'snmp_community': self.community_input.text().strip(),
                    'snmp_port': 161,
                    'custom_oids': []
                }
                
                # Check if exists
                exists = any(c['ip'] == ip for c in self.parent_window.target_configs)
                if not exists:
                    self.parent_window.target_configs.append(config)
                    self.parent_window.init_target(config)
                    added_count += 1
                    
        if added_count > 0:
            self.parent_window.save_configs()
            QMessageBox.information(self, "Success", f"Added {added_count} new devices to monitor!")
            self.accept()
        else:
            QMessageBox.warning(self, "Warning", "No new devices selected or they already exist.")

    def closeEvent(self, event):
        if self.worker is not None:
            self.worker.stop()
            self.worker.wait()
        super().closeEvent(event)
