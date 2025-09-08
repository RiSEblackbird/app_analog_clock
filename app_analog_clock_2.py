# -*- coding: utf-8 -*-
# アプリ名: 0. アナログ時計2
"""PySide6 アナログ時計アプリ"""

import sys
import math
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QPoint, QUrl
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QPushButton,
    QCheckBox, QHBoxLayout, QVBoxLayout, QLayout, QSlider
)
from PySide6.QtMultimedia import QSoundEffect

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
VOLUME_MAX_SCALE = 0.40  # UIの100%が実効40%になるように補正

LIGHT_THEME = {
    "bg": "#ffffff",
    "line": "#000000",
    "number": "#000000",
    "tick": "#666666",
    "second": "#ff0000"
}
DARK_THEME = {
    "bg": "#2b2b2b",
    "line": "#ffffff",
    "number": "#dddddd",
    "tick": "#bbbbbb",
    "second": "#ff4d4d"
}

# ---------------------- アナログ時計ウィジェット ----------------------
class ClockWidget(QWidget):
    def __init__(self, parent=None, factor=1.0):
        super().__init__(parent)
        self.factor = factor
        self.theme = LIGHT_THEME
        self.setMinimumSize(WINDOW_SIZE, WINDOW_SIZE)
        self.setFixedSize(int(WINDOW_SIZE * factor), int(WINDOW_SIZE * factor))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(UPDATE_INTERVAL)

    def set_theme(self, theme):
        self.theme = theme
        self.setStyleSheet(f"background-color:{theme['bg']}")
        self.update()

    def resize_by_factor(self, factor):
        self.factor = factor
        size = int(WINDOW_SIZE * factor)
        self.setFixedSize(size, size)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # factor に基づきスケール（描画とウィジェットサイズの両方で一貫）
        painter.scale(self.factor, self.factor)

        pen = QPen(QColor(self.theme["line"]))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawEllipse(CENTER, CLOCK_RADIUS, CLOCK_RADIUS)

        # 目盛り（秒/分）を描画（60分割。5分毎は長く太く）
        tick_pen = QPen(QColor(self.theme["tick"]))
        for i in range(60):
            is_five = (i % 5 == 0)
            tick_len = 10 if is_five else 6
            tick_width = 3 if is_five else 1
            tick_pen.setWidth(tick_width)
            painter.setPen(tick_pen)
            angle = math.radians(i * 6)
            # Qtの座標系は右が+X、下が+Y。
            # 円周上の点: (cx + r*cos, cy + r*sin)
            start_x = CENTER.x() + (CLOCK_RADIUS - tick_len) * math.cos(angle)
            start_y = CENTER.y() + (CLOCK_RADIUS - tick_len) * math.sin(angle)
            end_x = CENTER.x() + CLOCK_RADIUS * math.cos(angle)
            end_y = CENTER.y() + CLOCK_RADIUS * math.sin(angle)
            painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))

        painter.setPen(QColor(self.theme["number"]))
        font = QFont("Helvetica", FONT_SIZE)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        for i in range(1, 13):
            angle = math.radians(i * 30 - 90)
            x = CENTER.x() + NUMBER_DISTANCE * math.cos(angle)
            y = CENTER.y() + NUMBER_DISTANCE * math.sin(angle)
            text = str(i)
            w = metrics.horizontalAdvance(text)
            h = metrics.height()
            # 中心 (x,y) にテキストを配置するため、左上原点を補正
            painter.drawText(int(x - w/2), int(y + h/2 - metrics.descent()), text)

        now = time.localtime()
        second = now.tm_sec
        minute = now.tm_min
        hour = now.tm_hour % 12 + minute / 60.0

        self.draw_hand(painter, hour * 30, LENGTH_HOUR_HAND, 8)
        self.draw_hand(painter, minute * 6, LENGTH_MINUTE_HAND, 5)
        self.draw_hand(painter, second * 6, LENGTH_SECOND_HAND, 2, color=self.theme["second"])

    def draw_hand(self, painter, angle_deg, length, width, color=None):
        angle = math.radians(angle_deg)
        end = QPoint(
            CENTER.x() + length * math.sin(angle),
            CENTER.y() - length * math.cos(angle)
        )
        pen = painter.pen()
        pen.setWidth(width)
        pen.setColor(QColor(color if color else self.theme["line"]))
        painter.setPen(pen)
        painter.drawLine(CENTER, end)

# ---------------------- メインウィンドウ ----------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_dark_theme = False
        self.is_auto_theme = True
        self.factor = self.load_factor()
        self.last_second = None
        self.is_tick_sound = False

        self.clock = ClockWidget(self, self.factor)
        # デジタル表示は時計上にオーバーレイ配置（2行目左端相当）
        self.digital_label = QLabel(self.clock)
        self.digital_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.size_button = QPushButton("サイズ変更")
        self.size_button.clicked.connect(self.toggle_size)

        self.color_button = QPushButton("カラー変更")
        self.color_button.clicked.connect(self.toggle_theme)

        self.auto_checkbox = QCheckBox("Auto")
        self.auto_checkbox.setChecked(True)
        self.auto_checkbox.stateChanged.connect(self.on_auto_changed)

        # 秒針音スイッチと音量
        self.sound_checkbox = QCheckBox("秒針音")
        self.sound_checkbox.setChecked(False)
        self.sound_checkbox.stateChanged.connect(self.on_sound_changed)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.setTickPosition(QSlider.NoTicks)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        self.volume_label = QLabel("50%")

        header = QHBoxLayout()
        # サイズ変更ボタンをデジタル時計の左側に配置
        header.addWidget(self.size_button)
        header.addWidget(self.color_button)
        header.addWidget(self.auto_checkbox)
        header.addWidget(self.sound_checkbox)
        header.addWidget(self.volume_slider)
        header.addWidget(self.volume_label)

        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SetDefaultConstraint)
        layout.setSpacing(2)  # 行間を詰める
        layout.setContentsMargins(6, 4, 6, 6)  # 余白を小さめに
        layout.addLayout(header)
        layout.addWidget(self.clock)

        self.container = QWidget()
        self.container.setObjectName("central")
        self.container.setLayout(layout)
        self.setCentralWidget(self.container)

        self.setWindowTitle("アナログ時計")
        self.apply_ui_scale()
        self.resize_to_content()

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_datetime_label)
        self.update_timer.start(UPDATE_INTERVAL)
        self.update_datetime_label()

        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self.apply_auto_theme)
        self.auto_timer.start(AUTO_CHECK_INTERVAL_MS)
        self.apply_auto_theme()

        # 秒針音の初期化
        self.tick_effect = QSoundEffect(self)
        try:
            tick_path = self.ensure_tick_wav()
            self.tick_effect.setSource(QUrl.fromLocalFile(str(tick_path)))
        except Exception as e:
            print(f"[warn] tick sound init failed: {e}")
        self.tick_effect.setLoopCount(1)
        self.tick_effect.setVolume(self._scaled_volume(self.volume_slider.value()))
        # 初期の音量ラベル反映
        self.on_volume_changed(self.volume_slider.value())

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
        # 近似一致でインデックスを求める（浮動小数の誤差対策）
        def nearest_index(val):
            diffs = [abs(val - f) for f in factors]
            return diffs.index(min(diffs))
        idx = (nearest_index(self.factor) + 1) % len(factors)
        self.factor = factors[idx]
        self.save_factor()
        self.clock.resize_by_factor(self.factor)
        self.apply_ui_scale()
        self.resize_to_content()
        # OSの最小サイズ制約で縮まらないことがあるため二度実行
        self.resize_to_content()
        self.log_state("[サイズ変更]")

    # -------- テーマ関連 --------
    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()
        self.log_state("[カラー変更]")

    def apply_theme(self):
        theme = DARK_THEME if self.is_dark_theme else LIGHT_THEME
        self.clock.set_theme(theme)
        # スタイルシートで中央ウィジェット配下にテーマを適用
        style = (
            f"QWidget#central {{ background-color: {theme['bg']}; color: {theme['number']}; }}"
            f" QLabel {{ color: {theme['number']}; }}"
            f" QCheckBox {{ color: {theme['number']}; }}"
            f" QPushButton {{ color: {theme['number']}; border: 1px solid {theme['tick']}; background-color: transparent; }}"
            f" QSlider::groove:horizontal {{ background: {theme['tick']}; height: 4px; border-radius: 2px; }}"
            f" QSlider::handle:horizontal {{ background: {theme['number']}; border: 1px solid {theme['tick']}; width: 12px; margin: -6px 0; border-radius: 6px; }}"
        )
        self.container.setStyleSheet(style)

    def apply_ui_scale(self):
        # UIのフォントとボタン幅をスケール
        ui_font_size = max(10, int(12 * self.factor))
        ui_font = QFont()
        ui_font.setPixelSize(ui_font_size)
        self.digital_label.setFont(ui_font)
        self.size_button.setFont(ui_font)
        self.color_button.setFont(ui_font)
        self.auto_checkbox.setFont(ui_font)
        self.sound_checkbox.setFont(ui_font)
        self.volume_label.setFont(ui_font)

        # デジタル時計の位置を時計ウィジェット左上へ（より左に寄せる）
        margin_x = max(2, int(4 * self.factor))
        margin_y = max(2, int(6 * self.factor))
        self.digital_label.move(margin_x, margin_y)
        self.digital_label.raise_()

        # ボタンの横幅を「サイズヒントの半分」かつ「文字列幅+余白」を下回らないように設定
        fm = QFontMetrics(ui_font)
        def half_or_text(btn):
            half = btn.sizeHint().width() // 2
            text_w = fm.horizontalAdvance(btn.text()) + 24  # 左右余白
            return max(40, max(half, text_w))
        self.size_button.setFixedWidth(half_or_text(self.size_button))
        self.color_button.setFixedWidth(half_or_text(self.color_button))
        # スライダー幅をスケール
        base_slider_w = 50
        self.volume_slider.setFixedWidth(max(100, int(base_slider_w * self.factor)))

    def log_state(self, source: str):
        theme_name = "DARK" if self.is_dark_theme else "LIGHT"
        auto = "ON" if self.is_auto_theme else "OFF"
        print(f"{source} factor={self.factor:.2f}, clock={self.clock.width()}x{self.clock.height()}, window={self.width()}x{self.height()}, theme={theme_name}, auto={auto}")

    def resize_to_content(self):
        # 幾何情報を更新し、推奨サイズに合わせて縮小も許可
        self.container.updateGeometry()
        self.layout().activate()
        self.container.adjustSize()
        content = self.container.sizeHint()
        frame_w = self.frameGeometry().width() - self.geometry().width()
        frame_h = self.frameGeometry().height() - self.geometry().height()
        self.resize(content.width() + frame_w, content.height() + frame_h)

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
        self.digital_label.setText(time.strftime("%Y-%m-%d %H:%M:%S"))
        self.digital_label.adjustSize()
        # 秒針音の再生（毎秒）
        now = time.localtime()
        current_second = now.tm_sec
        if self.sound_checkbox.isChecked():
            if self.last_second != current_second:
                if hasattr(self, "tick_effect") and self.tick_effect is not None:
                    if self.tick_effect.isPlaying():
                        self.tick_effect.stop()
                    self.tick_effect.play()
        self.last_second = current_second

    # -------- 秒針音関連 --------
    def on_sound_changed(self, state):
        self.is_tick_sound = bool(state)

        # 無音から有効化時の即時反映（音量も適用）
        if hasattr(self, "tick_effect") and self.tick_effect is not None:
            self.tick_effect.setVolume(self._scaled_volume(self.volume_slider.value()))

    def on_volume_changed(self, value: int):
        if hasattr(self, "tick_effect") and self.tick_effect is not None:
            self.tick_effect.setVolume(self._scaled_volume(value))
        if hasattr(self, "volume_label"):
            self.volume_label.setText(f"{value}%")

    def _scaled_volume(self, slider_value: int | float) -> float:
        # 0-100のスライダー値を0-1へ正規化し、最大40%で打ち止め
        try:
            normalized = float(slider_value) / 100.0
        except Exception:
            normalized = 0.0
        scaled = max(0.0, min(1.0, normalized * VOLUME_MAX_SCALE))
        return scaled

    def ensure_tick_wav(self) -> Path:
        path = Path(__file__).parent / "tick.wav"
        if not path.exists():
            self.generate_tick_wav(path)
        return path

    def generate_tick_wav(self, path: Path):
        # 機械式のクリックに近い短いインパルス＋減衰ノイズを合成
        import wave
        import struct
        import random
        sample_rate = 44100
        duration_sec = 0.06
        num_samples = int(sample_rate * duration_sec)
        attack_samples = int(0.002 * sample_rate)   # 2ms 立ち上がり
        decay_samples = num_samples - attack_samples
        click_amp = 12000
        noise_amp = 7000
        # ハイパス気味のノイズ成分を入れてメカ感を演出
        prev = 0.0
        samples = []
        for i in range(num_samples):
            if i < attack_samples:
                env = i / max(1, attack_samples)
            else:
                env = max(0.0, 1.0 - (i - attack_samples) / max(1, decay_samples))
                env = env * env  # 急速減衰
            # 小さなインパルス（矩形に近い）
            impulse = click_amp * (1.0 if i < int(0.0015 * sample_rate) else 0.0)
            # ハイパス風ノイズ（差分）
            white = (random.random() * 2.0 - 1.0)
            hp = white - prev
            prev = white
            val = impulse + noise_amp * hp * env
            val = max(-32767, min(32767, int(val)))
            samples.append(val)
        with wave.open(str(path), 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            for v in samples:
                wf.writeframes(struct.pack('<h', v))

# ---------------------- エントリポイント ----------------------
def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
