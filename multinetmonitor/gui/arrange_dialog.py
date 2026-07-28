from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QSpinBox, QComboBox, QPushButton, QLabel)
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt

class ArrangeDialog(QDialog):
    def __init__(self, parent=None, default_rows=3, default_cols=3):
        super().__init__(parent)
        self.setWindowTitle("Pengaturan Tata Ulang (Auto Arrange Grid)")
        self.resize(380, 240)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # Screen Selector
        self.screen_combo = QComboBox()
        screens = QGuiApplication.screens()
        primary = QGuiApplication.primaryScreen()
        
        for i, s in enumerate(screens):
            geom = s.availableGeometry()
            is_prim = " (Utama)" if s == primary else ""
            self.screen_combo.addItem(f"Layar {i+1}{is_prim}: {geom.width()}x{geom.height()}", i)
            
        form.addRow("Pilih Layar Aktif:", self.screen_combo)
        
        # Rows
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 12)
        self.rows_spin.setValue(default_rows)
        form.addRow("Jumlah Baris (Rows):", self.rows_spin)
        
        # Cols
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 12)
        self.cols_spin.setValue(default_cols)
        form.addRow("Jumlah Kolom (Cols):", self.cols_spin)
        
        # Direction
        self.direction_combo = QComboBox()
        self.direction_combo.addItem("Kiri-Atas ➔ Kanan-Bawah", "top_left")
        self.direction_combo.addItem("Kanan-Atas ➔ Kiri-Bawah", "top_right")
        form.addRow("Arah Urutan Grid:", self.direction_combo)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Tata Sekarang")
        self.apply_btn.setStyleSheet("background-color: #06b6d4; color: white; font-weight: bold; padding: 6px 12px;")
        self.apply_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("Batal")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def get_data(self):
        screens = QGuiApplication.screens()
        screen_idx = self.screen_combo.currentData()
        target_screen = screens[screen_idx] if screen_idx < len(screens) else QGuiApplication.primaryScreen()
        
        return {
            'screen': target_screen,
            'rows': self.rows_spin.value(),
            'cols': self.cols_spin.value(),
            'direction': self.direction_combo.currentData()
        }
