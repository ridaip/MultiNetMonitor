from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox, QMessageBox,
                               QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView)
from .scanner_dialog import ScannerDialog

class AddTargetDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Monitor Target" if initial_data else "Add Monitor Target")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Target Label / Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Label Target:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Contoh: Server Utama, Router Core (opsional)")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # IP Address
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("IP Address:"))
        self.ip_input = QLineEdit()
        ip_layout.addWidget(self.ip_input)
        layout.addLayout(ip_layout)

        # SNMP Enable
        self.snmp_check = QCheckBox("Enable SNMP Monitoring")
        self.snmp_check.toggled.connect(self.toggle_snmp)
        layout.addWidget(self.snmp_check)

        # SNMP Config
        self.snmp_community_input = QLineEdit("public")
        self.snmp_community_input.setEnabled(False)
        self.snmp_version_combo = QComboBox()
        self.snmp_version_combo.addItems(["v2c", "v1", "v3"])
        self.snmp_version_combo.setEnabled(False)
        self.snmp_version_combo.currentTextChanged.connect(self.on_version_changed)
        self.snmp_version_combo.setEnabled(False)
        self.snmp_port_input = QLineEdit("161")
        self.snmp_port_input.setEnabled(False)
        self.snmp_port_input.setFixedWidth(50)

        snmp_layout = QHBoxLayout()
        snmp_layout.addWidget(QLabel("Community:"))
        snmp_layout.addWidget(self.snmp_community_input)
        snmp_layout.addWidget(QLabel("Version:"))
        snmp_layout.addWidget(self.snmp_version_combo)
        snmp_layout.addWidget(QLabel("Port:"))
        snmp_layout.addWidget(self.snmp_port_input)
        layout.addLayout(snmp_layout)

        # SNMP v3 Advanced Config
        self.v3_group = QGroupBox("SNMP v3 Credentials")
        self.v3_group.setVisible(False)
        v3_layout = QVBoxLayout(self.v3_group)
        
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Username:"))
        self.v3_user = QLineEdit()
        user_layout.addWidget(self.v3_user)
        v3_layout.addLayout(user_layout)
        
        auth_layout = QHBoxLayout()
        auth_layout.addWidget(QLabel("Auth Proto:"))
        self.v3_auth_proto = QComboBox()
        self.v3_auth_proto.addItems(["NONE", "MD5", "SHA"])
        auth_layout.addWidget(self.v3_auth_proto)
        auth_layout.addWidget(QLabel("Auth Key:"))
        self.v3_auth_key = QLineEdit()
        self.v3_auth_key.setEchoMode(QLineEdit.Password)
        auth_layout.addWidget(self.v3_auth_key)
        v3_layout.addLayout(auth_layout)
        
        priv_layout = QHBoxLayout()
        priv_layout.addWidget(QLabel("Priv Proto:"))
        self.v3_priv_proto = QComboBox()
        self.v3_priv_proto.addItems(["NONE", "DES", "AES"])
        priv_layout.addWidget(self.v3_priv_proto)
        priv_layout.addWidget(QLabel("Priv Key:"))
        self.v3_priv_key = QLineEdit()
        self.v3_priv_key.setEchoMode(QLineEdit.Password)
        priv_layout.addWidget(self.v3_priv_key)
        v3_layout.addLayout(priv_layout)
        
        layout.addWidget(self.v3_group)

        # Custom OIDs
        self.custom_oids_group = QGroupBox("Custom OIDs")
        self.custom_oids_group.setEnabled(False)
        custom_oids_layout = QVBoxLayout(self.custom_oids_group)
        
        self.oids_table = QTableWidget(0, 4)
        self.oids_table.setHorizontalHeaderLabels(["Name", "OID", "Suffix", "Type"])
        self.oids_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.oids_table.setSelectionBehavior(QTableWidget.SelectRows)
        custom_oids_layout.addWidget(self.oids_table)
        
        btn_oid_layout = QHBoxLayout()
        self.add_oid_btn = QPushButton("Add OID")
        self.add_oid_btn.clicked.connect(self.add_oid_row)
        self.remove_oid_btn = QPushButton("Remove Selected")
        self.remove_oid_btn.clicked.connect(self.remove_oid_row)
        
        self.open_scanner_btn = QPushButton("Open OID Scanner")
        self.open_scanner_btn.clicked.connect(self.open_scanner)
        self.open_scanner_btn.setObjectName("OpenScannerBtn")
        
        btn_oid_layout.addWidget(self.add_oid_btn)
        btn_oid_layout.addWidget(self.remove_oid_btn)
        btn_oid_layout.addWidget(self.open_scanner_btn)
        custom_oids_layout.addLayout(btn_oid_layout)
        
        layout.addWidget(self.custom_oids_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Save" if initial_data else "Add")
        self.cancel_btn = QPushButton("Cancel")
        self.add_btn.clicked.connect(self.accept_data)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        if initial_data:
            self.name_input.setText(initial_data.get('name', ''))
            self.ip_input.setText(initial_data.get('ip', ''))
            self.snmp_check.setChecked(initial_data.get('snmp_enabled', False))
            self.snmp_community_input.setText(initial_data.get('snmp_community', 'public'))
            self.snmp_port_input.setText(str(initial_data.get('snmp_port', 161)))
            version_int = initial_data.get('snmp_version', 2)
            if version_int == 3:
                version = "v3"
            else:
                version = "v2c" if version_int == 2 else "v1"
            self.snmp_version_combo.setCurrentText(version)
            
            if version == "v3":
                self.v3_user.setText(initial_data.get('v3_user', ''))
                self.v3_auth_proto.setCurrentText(initial_data.get('v3_auth_proto', 'NONE'))
                self.v3_auth_key.setText(initial_data.get('v3_auth_key', ''))
                self.v3_priv_proto.setCurrentText(initial_data.get('v3_priv_proto', 'NONE'))
                self.v3_priv_key.setText(initial_data.get('v3_priv_key', ''))
                
            self.toggle_snmp(self.snmp_check.isChecked())
            
            for custom_oid in initial_data.get('custom_oids', []):
                self.add_oid_row(custom_oid.get('name'), custom_oid.get('oid'), custom_oid.get('suffix'), custom_oid.get('type', 'Text'))

    def add_oid_row(self, name="", oid="", suffix="", type_val="Text"):
        row = self.oids_table.rowCount()
        self.oids_table.insertRow(row)
        self.oids_table.setItem(row, 0, QTableWidgetItem(name or ""))
        self.oids_table.setItem(row, 1, QTableWidgetItem(oid or ""))
        self.oids_table.setItem(row, 2, QTableWidgetItem(suffix or ""))
        
        combo = QComboBox()
        combo.addItems(["Text", "Progress Bar", "Line Graph"])
        combo.setCurrentText(type_val)
        self.oids_table.setCellWidget(row, 3, combo)

    def remove_oid_row(self):
        current_row = self.oids_table.currentRow()
        if current_row >= 0:
            self.oids_table.removeRow(current_row)

    def open_scanner(self):
        dialog = ScannerDialog(self)
        dialog.ip_input.setText(self.ip_input.text().strip() or "127.0.0.1")
        dialog.community_input.setText(self.snmp_community_input.text().strip())
        dialog.port_input.setText(self.snmp_port_input.text().strip())
        dialog.version_combo.setCurrentText(self.snmp_version_combo.currentText())
        
        dialog.oid_selected.connect(self.add_oid_from_scanner)
        dialog.exec()

    def add_oid_from_scanner(self, oid_str):
        self.add_oid_row("Scanned OID", oid_str, "", "Text")

    def toggle_snmp(self, checked):
        self.snmp_community_input.setEnabled(checked)
        self.snmp_version_combo.setEnabled(checked)
        self.snmp_port_input.setEnabled(checked)
        self.custom_oids_group.setEnabled(checked)
        self.on_version_changed(self.snmp_version_combo.currentText())
        
    def on_version_changed(self, text):
        if self.snmp_check.isChecked() and text == "v3":
            self.v3_group.setVisible(True)
            self.snmp_community_input.setEnabled(False)
        else:
            self.v3_group.setVisible(False)
            self.snmp_community_input.setEnabled(self.snmp_check.isChecked())

    def accept_data(self):
        if not self.ip_input.text().strip():
            QMessageBox.warning(self, "Error", "IP Address cannot be empty")
            return
        self.accept()

    def get_data(self):
        try:
            port = int(self.snmp_port_input.text().strip())
        except ValueError:
            port = 161
            
        custom_oids = []
        for i in range(self.oids_table.rowCount()):
            name_item = self.oids_table.item(i, 0)
            oid_item = self.oids_table.item(i, 1)
            suffix_item = self.oids_table.item(i, 2)
            type_widget = self.oids_table.cellWidget(i, 3)
            
            if name_item and oid_item and name_item.text().strip() and oid_item.text().strip():
                custom_oids.append({
                    "name": name_item.text().strip(),
                    "oid": oid_item.text().strip(),
                    "suffix": suffix_item.text().strip() if suffix_item else "",
                    "type": type_widget.currentText() if type_widget else "Text"
                })
            
        ver_text = self.snmp_version_combo.currentText()
        if ver_text == "v3":
            ver_int = 3
        elif ver_text == "v2c":
            ver_int = 2
        else:
            ver_int = 1
            
        return {
            "name": self.name_input.text().strip(),
            "ip": self.ip_input.text().strip(),
            "snmp_enabled": self.snmp_check.isChecked(),
            "snmp_community": self.snmp_community_input.text().strip(),
            "snmp_version": ver_int,
            "snmp_port": port,
            "custom_oids": custom_oids,
            "v3_user": self.v3_user.text().strip(),
            "v3_auth_proto": self.v3_auth_proto.currentText(),
            "v3_auth_key": self.v3_auth_key.text().strip(),
            "v3_priv_proto": self.v3_priv_proto.currentText(),
            "v3_priv_key": self.v3_priv_key.text().strip()
        }
