# -*- coding: utf-8 -*-
# アプリ名: 0. アナログ時計

import sys
import traceback
import tkinter as tk
import math
import time
import os
import socket
import csv

# 定数定義
WINDOW_SIZE = "400x420"
CLOCK_RADIUS = 190
CENTER = (200, 200)
LENGTH_SECOND_HAND = 175
LENGTH_MINUTE_HAND = 150
LENGTH_HOUR_HAND = 100
NUMBER_DISTANCE = 155  # 中心から数字までの距離
UPDATE_INTERVAL = 1000  # 1秒ごとに更新
FONT_SIZE = 32

# 変更可能な定数
clock_size = 1  # 時計のサイズモード
factor = 1.0

# 定数としてウィンドウ位置情報を保存するファイル名を設定
POSITION_FILE = 'window_position_app_analog_clock.csv'

# 定数としてホスト名を取得
HOSTNAME = socket.gethostname()

def get_exception_trace():
    '''例外のトレースバックを取得'''
    t, v, tb = sys.exc_info()
    trace = traceback.format_exception(t, v, tb)
    return trace

def save_position(root):
    """
    ウィンドウの位置のみをCSVファイルに保存する。異なるホストの情報も保持。
    """
    print("ウィンドウ位置を保存中...")
    # root.geometry()から位置情報のみを取り出す
    position_info = root.geometry().split('+')[1:]
    position_str = '+' + '+'.join(position_info)
    position_data = [HOSTNAME, position_str]
    existing_data = []
    try:
        # 既存のデータを読み込んで、現在のホスト以外の情報を保持
        with open(POSITION_FILE, newline='', encoding="utf_8_sig") as csvfile:
            reader = csv.reader(csvfile)
            existing_data = [row for row in reader if row[0] != HOSTNAME]
    except FileNotFoundError:
        print("ファイルが存在しないため、新規作成します。")
    
    # 現在のホストの情報を含む全データを書き込む
    existing_data.append(position_data)
    with open(POSITION_FILE, 'w', newline='', encoding="utf_8_sig") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(existing_data)
    print("保存完了")

def restore_position(root):
    """
    CSVファイルからウィンドウの位置のみを復元する。
    """
    print("ウィンドウ位置を復元中...")
    try:
        with open(POSITION_FILE, newline='', encoding="utf_8_sig") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row[0] == HOSTNAME:
                    position_str = row[1].strip()  # 余計な空白がないか確認
                    if position_str.startswith('+'):
                        position_str = position_str[1:]  # 先頭の余分な '+' を取り除く
                    print(f"復元データ: {position_str}")
                    # サイズ情報なしで位置情報のみを設定
                    root.geometry('+' + position_str)
                    break
    except FileNotFoundError:
        print("位置情報ファイルが見つかりません。")


def toggle_clock_size():
    global factor, clock_size, root
    clock_size = (clock_size % 4) + 1
    factor = [1, 1.5, 2, 2.5][clock_size - 1]

    # factor を保存する処理（ファイルに書き込みなど）
    with open('factor.txt', 'w') as f:
        f.write(str(factor))

    # 位置情報の保存
    save_position(root)

    # 現在のウィンドウを破壊
    root.destroy()

    # アプリケーションを再起動
    restart_application()


def restart_application():
    global root, canvas

    # アプリケーションの再起動
    root = tk.Tk()
    root.title("アナログ時計")
    root.geometry(WINDOW_SIZE)

    # factor を読み込む
    with open('factor.txt', 'r') as f:
        global factor
        factor = float(f.read())

    # ウィンドウサイズと中心の再計算
    apply_factor_settings()

    # サイズ変更ボタンをウィンドウの左上に配置
    size_button = tk.Button(root, text="サイズ変更", command=toggle_clock_size)
    size_button.pack(side='top', anchor='nw')

    # 時計の文字盤を描画
    canvas = tk.Canvas(root, width=400, height=400, bg='white')
    canvas.pack(expand=True, fill=tk.BOTH)

    draw_clock(canvas)

    # 位置情報の復元
    restore_position(root)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


def apply_factor_settings():
    global WINDOW_SIZE, CENTER, CLOCK_RADIUS, LENGTH_SECOND_HAND, LENGTH_MINUTE_HAND, LENGTH_HOUR_HAND, NUMBER_DISTANCE, FONT_SIZE
    window_width = 400 * factor
    window_height = 420 * factor
    CENTER = (window_width / 2, window_height / 2 - 25)
    CLOCK_RADIUS = 190 * factor
    LENGTH_SECOND_HAND = 175 * factor
    LENGTH_MINUTE_HAND = 150 * factor
    LENGTH_HOUR_HAND = 100 * factor
    NUMBER_DISTANCE = 155 * factor
    FONT_SIZE = int(32 * factor)
    WINDOW_SIZE = f"{int(window_width)}x{int(window_height)}"
    root.geometry(WINDOW_SIZE)

def draw_ticks(canvas):
    """
    時計の目盛り線を描画する関数
    各目盛りは、1分ごと（6度ごと）に描画される
    """
    for i in range(60):  # 1分ごとの目盛りのため、60回繰り返す
        if i % 5 == 0:
            tick_length = 20  # 目盛りの長さ
            tick_width = 3
        else:
            tick_length = 10  # 目盛りの長さ
            tick_width = 1

        angle = math.radians(i * 6)  # 1分につき6度
        start_x = CENTER[0] + (CLOCK_RADIUS - tick_length) * math.cos(angle)
        start_y = CENTER[1] + (CLOCK_RADIUS - tick_length) * math.sin(angle)
        end_x = CENTER[0] + CLOCK_RADIUS * math.cos(angle)
        end_y = CENTER[1] + CLOCK_RADIUS * math.sin(angle)
        canvas.create_line(start_x, start_y, end_x, end_y, fill='gray', width=tick_width)

def draw_clock(canvas):
    canvas.delete("all")  # 既存の描画をすべて削除
    canvas.create_oval(CENTER[0] - CLOCK_RADIUS, CENTER[1] - CLOCK_RADIUS, CENTER[0] + CLOCK_RADIUS, CENTER[1] + CLOCK_RADIUS)
    draw_numbers(canvas)
    draw_ticks(canvas)  
    draw_center_dot(canvas)
    update_clock(canvas, [])

def draw_center_dot(canvas):
    """
    時計の中心に小さな黒い丸を描画する関数
    """
    dot_radius = 7  # 中心点の半径
    canvas.create_oval(CENTER[0] - dot_radius, CENTER[1] - dot_radius, CENTER[0] + dot_radius, CENTER[1] + dot_radius, fill='black', outline='black')

# アプリケーションの終了時の処理をカスタマイズする
def on_close():
    save_position(root)  # ウィンドウの位置を保存
    root.destroy()  # ウィンドウを破壊する

def draw_hand(canvas, center, length, angle, width):
    """
    時計の針を描画する関数
    center: 中心点 (x, y)
    length: 針の長さ
    angle: 針の角度 (度)
    width: 針の幅
    返り値: 針のアイテムID
    """
    angle_rad = math.radians(angle)
    end_x = center[0] + length * math.sin(angle_rad)
    end_y = center[1] - length * math.cos(angle_rad)
    return canvas.create_line(center[0], center[1], end_x, end_y, width=width, fill='black')

def update_clock(canvas, hand_ids):
    """
    時計を更新する関数
    """
    # 既存の針を削除
    for hand_id in hand_ids:
        canvas.delete(hand_id)

    now = time.localtime()
    hour = now.tm_hour
    minute = now.tm_min
    second = now.tm_sec

    # 時針、分針、秒針の角度を計算
    hour_angle = ((hour % 12) + minute / 60) * 30  # 1時間あたり30度
    minute_angle = minute * 6  # 1分あたり6度
    second_angle = second * 6  # 1秒あたり6度

    # 針を描画して、各アイテムIDを保存
    new_hand_ids = [
        draw_hand(canvas, CENTER, LENGTH_HOUR_HAND, hour_angle, width=14),
        draw_hand(canvas, CENTER, LENGTH_MINUTE_HAND, minute_angle, width=8),
        draw_hand(canvas, CENTER, LENGTH_SECOND_HAND, second_angle, width=3)
    ]

    canvas.after(UPDATE_INTERVAL, update_clock, canvas, new_hand_ids)  # 1秒後に再度更新


def draw_numbers(canvas):
    """
    時計の数字を描画する関数
    """
    for i in range(1, 13):
        angle = math.radians(i * 30 - 90)
        x = CENTER[0] + NUMBER_DISTANCE * math.cos(angle)
        y = CENTER[1] + NUMBER_DISTANCE * math.sin(angle)
        canvas.create_text(x, y, text=str(i), font=("Helvetica", FONT_SIZE), fill="gray")


# メイン処理
try:
    # Tkinterのウィンドウを作成
    root = tk.Tk()
    root.title("アナログ時計")
    root.geometry(WINDOW_SIZE)
    restore_position(root)
    root.protocol("WM_DELETE_WINDOW", on_close)  # 終了時処理の設定

    # 「サイズ変更」ボタンの配置
    size_button = tk.Button(root, text="サイズ変更", command=toggle_clock_size)
    size_button.pack(side='top', anchor='nw')

    # 時計の文字盤を描画
    canvas = tk.Canvas(root, width=400, height=400, bg='white')
    canvas.pack(expand=True, fill=tk.BOTH)
    draw_clock(canvas)

    root.mainloop()

except Exception as e:
    t, v, tb = sys.exc_info()
    trace = traceback.format_exception(t, v, tb)
    print(trace)
