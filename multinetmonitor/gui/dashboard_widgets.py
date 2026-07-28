from PySide6.QtWidgets import QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QRectF
from .theme import get_theme_info

class DonutGaugeWidget(QWidget):
    def __init__(self, title, unit="%", parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.value = 0
        self.max_value = 100
        self.theme_key = "cyberpunk"
        self.setMinimumSize(150, 160)

    def set_value(self, val, max_val=100):
        self.value = val
        self.max_value = max_val
        self.update()

    def set_theme(self, theme_key):
        self.theme_key = theme_key
        self.update()

    def paintEvent(self, event):
        info = get_theme_info(self.theme_key)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Allocate space for donut ring (top) and title text (bottom)
        available_w = float(self.width())
        available_h = float(self.height() - 28) # Reserve 28px for title at the bottom
        
        gauge_size = max(50.0, min(available_w - 16.0, available_h - 16.0))
        x_offset = (available_w - gauge_size) / 2.0
        y_offset = (available_h - gauge_size) / 2.0
        
        rect = QRectF(x_offset, y_offset, gauge_size, gauge_size)
        
        # Background arc
        pen_bg = QPen(QColor(info['grid']))
        pen_bg.setWidth(10)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, 225 * 16, -270 * 16)

        # Foreground arc
        if self.max_value > 0:
            span = int(-270 * 16 * (min(self.value, self.max_value) / self.max_value))
        else:
            span = 0

        fg_color = QColor(info['primary'])
        if "Latency" in self.title and self.value > 100:
            fg_color = QColor("#FF3366")
        elif ("Health" in self.title or "Online" in self.title) and (self.value / max(1, self.max_value)) < 0.8:
            fg_color = QColor("#FF3366")

        pen_fg = QPen(fg_color)
        pen_fg.setWidth(10)
        pen_fg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_fg)
        painter.drawArc(rect, 225 * 16, span)

        # Numerical Value (Centered inside the ring)
        painter.setPen(QColor(info['text']))
        font_val = QFont('Inter', 15, QFont.Bold)
        painter.setFont(font_val)
        
        val_text = f"{self.value:.1f}{self.unit}" if isinstance(self.value, float) else f"{self.value}{self.unit}"
        painter.drawText(rect, Qt.AlignCenter, val_text)
        
        # Title Text (Positioned cleanly BELOW the ring)
        font_title = QFont('Inter', 11, QFont.DemiBold)
        painter.setFont(font_title)
        painter.setPen(QColor(info['text']))
        
        title_rect = QRectF(0, available_h + 2.0, available_w, 24.0)
        painter.drawText(title_rect, Qt.AlignCenter, self.title)


class LeaderboardWidget(QGroupBox):
    def __init__(self, title, color="#00E5FF", parent=None):
        super().__init__(title, parent)
        self.layout = QVBoxLayout(self)
        self.items = []
        self.color = color

        for i in range(5):
            row = QHBoxLayout()
            lbl = QLabel(f"{i+1}. --")
            lbl.setFixedWidth(140)
            bar = QProgressBar()
            bar.setTextVisible(True)
            bar.setFixedHeight(14)
            bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; border-radius: 7px; }} QProgressBar {{ border: 1px solid #444; border-radius: 7px; text-align: center; color: white; }}")
            row.addWidget(lbl)
            row.addWidget(bar)
            self.layout.addLayout(row)
            self.items.append((lbl, bar))

    def update_data(self, data_list):
        for i in range(5):
            lbl, bar = self.items[i]
            if i < len(data_list):
                name, val, text = data_list[i]
                lbl.setText(f"{i+1}. {name}")
                bar.setValue(min(100, max(0, int(val))))
                bar.setFormat(text)
            else:
                lbl.setText(f"{i+1}. --")
                bar.setValue(0)
                bar.setFormat("")
