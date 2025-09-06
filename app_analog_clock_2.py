# -*- coding: utf-8 -*-
"""PySide6 アナログ時計アプリ"""

import sys
import math
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QPushButton,
    QCheckBox, QHBoxLayout, QVBoxLayout
)

# ---------------------- 定数 ----------------------
WINDOW_SIZE = 400
CLOCK_RADIUS = 190
CENTER = QPoint(200, 200)
LENGTH_SECOND_HAND = 175
LENGTH_MINUTE_HAND = 150
LENGTH_HOUR_HAND = 100
NUMBER_DISTANCE = 155
UPDATE_INTERVAL = 1000        # アナログ＆デジタル更新間隔
AUTO_CHECK_INTERVAL_MS = 60000
FONT_SIZE = 32
FACTOR_FILE = Path("factor.txt")

LIGHT_THEME = {
    "bg": "#ffffff",
    "line": "#000000",
    "number": "#000000",
    "tick": "#666666"
}
DARK_THEME = {
    "bg": "#2b2b2b",
    "line": "#ffffff",
    "number": "#dddddd",
    "tick": "#bbbbbb"
}

# ---------------------- アナログ時計ウィジェット ----------------------
class ClockWidget(QWidget):
    def __init__(self, parent=None, factor=1.0):
        super().__init__(parent)
        self.factor = factor
        self.theme = LIGHT_THEME
        self.setFixedSize(int(WINDOW_SIZE * factor), int(WINDOW_SIZE * factor))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(UPDATE_INTERVAL)

    def set_theme(self, theme):
        self.theme = theme
        self.setStyleSheet(f"background:{theme['bg']}")
        self.update()

    def resize_by_factor(self, factor):
        self.factor = factor
        size = int(WINDOW_SIZE * factor)
        self.setFixedSize(size, size)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(self.factor, self.factor)

        pen = QPen(QColor(self.theme["line"]))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawEllipse(CENTER, CLOCK_RADIUS, CLOCK_RADIUS)

        painter.setPen(QColor(self.theme["number"]))
        painter.setFont(QFont("Helvetica", FONT_SIZE))
        for i in range(1, 13):
            angle = math.radians(i * 30 - 90)
            x = CENTER.x() + NUMBER_DISTANCE * math.cos(angle)
            y = CENTER.y() + NUMBER_DISTANCE * math.sin(angle) + FONT_SIZE/3
            painter.drawText(int(x-10), int(y), str(i))

        now = time.localtime()
        second = now.tm_sec
        minute = now.tm_min
        hour = now.tm_hour % 12 + minute / 60.0

        self.draw_hand(painter, hour * 30, LENGTH_HOUR_HAND, 8)
        self.draw_hand(painter, minute * 6, LENGTH_MINUTE_HAND, 5)

        pen.setColor(QColor("#ff0000"))
        pen.setWidth(2)
        painter.setPen(pen)
        self.draw_hand(painter, second * 6, LENGTH_SECOND_HAND, 2)

    def draw_hand(self, painter, angle_deg, length, width):
        angle = math.radians(angle_deg)
        end = QPoint(
            CENTER.x() + length * math.sin(angle),
            CENTER.y() - length * math.cos(angle)
        )
        pen = painter.pen()
        pen.setWidth(width)
        pen.setColor(QColor(self.theme["line"]))
        painter.setPen(pen)
        painter.drawLine(CENTER, end)

# ---------------------- メインウィンドウ ----------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_dark_theme = False
        self.is_auto_theme = True
        self.factor = self.load_factor()

        self.clock = ClockWidget(self, self.factor)
        self.digital = QLabel()
        self.digital.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.size_button = QPushButton("サイズ変更")
        self.size_button.clicked.connect(self.toggle_size)

        self.color_button = QPushButton("カラー変更")
        self.color_button.clicked.connect(self.toggle_theme)

        self.auto_checkbox = QCheckBox("Auto")
        self.auto_checkbox.setChecked(True)
        self.auto_checkbox.stateChanged.connect(self.on_auto_changed)

        header = QHBoxLayout()
        header.addWidget(self.digital)
        header.addWidget(self.size_button)
        header.addWidget(self.color_button)
        header.addWidget(self.auto_checkbox)

        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addWidget(self.clock)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.setWindowTitle("アナログ時計")
        self.resize(self.clock.width(), self.clock.height() + 40)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_datetime_label)
        self.update_timer.start(UPDATE_INTERVAL)
        self.update_datetime_label()

        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self.apply_auto_theme)
        self.auto_timer.start(AUTO_CHECK_INTERVAL_MS)
        self.apply_auto_theme()

    # -------- サイズ関連 --------
    def load_factor(self):
        try:
            return float(FACTOR_FILE.read_text())
        except Exception:
            return 1.0

    def save_factor(self):
        FACTOR_FILE.write_text(str(self.factor))

    def toggle_size(self):
        factors = [1.0, 1.5, 2.0, 2.5]
        idx = (factors.index(self.factor) + 1) % len(factors)
        self.factor = factors[idx]
        self.save_factor()
        self.clock.resize_by_factor(self.factor)
        self.resize(self.clock.width(), self.clock.height() + 40)

    # -------- テーマ関連 --------
    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

    def apply_theme(self):
        theme = DARK_THEME if self.is_dark_theme else LIGHT_THEME
        self.clock.set_theme(theme)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(theme["bg"]))
        self.setPalette(palette)

    def on_auto_changed(self, state):
        self.is_auto_theme = bool(state)
        if self.is_auto_theme:
            self.apply_auto_theme()

    def apply_auto_theme(self):
        if not self.is_auto_theme:
            return
        hour = time.localtime().tm_hour
        self.is_dark_theme = (hour < 6 or hour >= 18)
        self.apply_theme()

    # -------- デジタル表示 --------
    def update_datetime_label(self):
        self.digital.setText(time.strftime("%Y-%m-%d %H:%M:%S"))

# ---------------------- エントリポイント ----------------------
def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
