from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QComboBox, QMessageBox)
from PySide6.QtCore import Qt, Signal
from ..network.snmp_scanner import SNMPScannerWorker
from .oid_db import COMMON_OIDS

class ScannerDialog(QDialog):
    oid_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SNMP OID Scanner")
        self.resize(700, 500)
        
        self.worker = None

        layout = QVBoxLayout(self)

        # Config row
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("IP:"))
        self.ip_input = QLineEdit("127.0.0.1")
        config_layout.addWidget(self.ip_input)
        
        config_layout.addWidget(QLabel("Community:"))
        self.community_input = QLineEdit("public")
        config_layout.addWidget(self.community_input)

        config_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("161")
        self.port_input.setFixedWidth(50)
        config_layout.addWidget(self.port_input)

        config_layout.addWidget(QLabel("Version:"))
        self.version_combo = QComboBox()
        self.version_combo.addItems(["v2c", "v1"])
        config_layout.addWidget(self.version_combo)
        
        self.start_btn = QPushButton("Start Scan")
        self.start_btn.clicked.connect(self.start_scan)
        config_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Scan")
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setEnabled(False)
        config_layout.addWidget(self.stop_btn)

        layout.addLayout(config_layout)

        # Filter row
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Type to filter OID or Value...")
        self.filter_input.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_input)
        
        self.status_label = QLabel("Ready.")
        filter_layout.addWidget(self.status_label)
        layout.addLayout(filter_layout)

        # Results Table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["OID", "Value / Type", "Hint (Database)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table)
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.add_to_target_btn = QPushButton("Add Selected OID to Target")
        self.add_to_target_btn.setEnabled(False)
        self.add_to_target_btn.clicked.connect(self.emit_selected_oid)
        self.add_to_target_btn.setStyleSheet("background-color: #00E5FF; color: black; font-weight: bold;")
        bottom_layout.addWidget(self.add_to_target_btn)
        layout.addLayout(bottom_layout)

    def on_selection_changed(self):
        self.add_to_target_btn.setEnabled(len(self.table.selectedItems()) > 0)
        
    def emit_selected_oid(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            # We select full rows, so row is known
            row = selected_items[0].row()
            oid_str = self.table.item(row, 0).text()
            self.oid_selected.emit(oid_str)
            
            # Show brief confirmation on button
            self.add_to_target_btn.setText("Added!")
            
    def start_scan(self):
        ip = self.ip_input.text().strip()
        if not ip:
            QMessageBox.warning(self, "Error", "IP Address required.")
            return
            
        try:
            port = int(self.port_input.text().strip())
        except:
            port = 161
            
        self.table.setRowCount(0)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Scanning...")
        
        version = 2 if self.version_combo.currentText() == "v2c" else 1
        
        self.worker = SNMPScannerWorker(ip, self.community_input.text().strip(), version, port)
        self.worker.data_found.connect(self.on_data_found)
        self.worker.finished_scan.connect(self.on_scan_finished)
        self.worker.start()

    def stop_scan(self):
        if self.worker:
            self.worker.stop()
            self.status_label.setText("Stopping...")

    def on_data_found(self, batch):
        for oid, result in batch:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            oid_item = QTableWidgetItem(oid)
            self.table.setItem(row, 0, oid_item)
            
            val_item = QTableWidgetItem(str(result))
            self.table.setItem(row, 1, val_item)
            
            # Check against common OIDs
            hint_text = ""
            best_match = ""
            for k, v in COMMON_OIDS.items():
                if oid.startswith(k) and len(k) > len(best_match):
                    best_match = k
                    hint_text = v
                    
            if hint_text:
                hint_item = QTableWidgetItem(hint_text)
                self.table.setItem(row, 2, hint_item)
            else:
                self.table.setItem(row, 2, QTableWidgetItem("Unknown"))
                
            self.table.scrollToBottom()
            
        # Re-apply filter if active
        if self.filter_input.text():
            self.apply_filter(self.filter_input.text())
            
        self.status_label.setText(f"Scanning... ({self.table.rowCount()} found)")

    def on_scan_finished(self, msg):
        self.status_label.setText(msg)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.worker = None

    def apply_filter(self, text):
        search_term = text.lower()
        for i in range(self.table.rowCount()):
            oid_item = self.table.item(i, 0)
            val_item = self.table.item(i, 1)
            if oid_item and val_item:
                match = search_term in oid_item.text().lower() or search_term in val_item.text().lower()
                self.table.setRowHidden(i, not match)

    def closeEvent(self, event):
        self.stop_scan()
        if self.worker:
            self.worker.wait()
        super().closeEvent(event)
