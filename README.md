## アナログ時計2（app_analog_clock_2.py / PySide6）

### 概要
**PySide6（Qt）製のシンプルなアナログ時計**。1秒ごとにアナログ（針）とデジタル（ヘッダの日時）を更新します。ライト/ダークのテーマ切替に加え、時刻帯に応じた自動テーマ（Auto）を備え、サイズ倍率は `factor.txt` に永続化されます。UIのフォント/ボタン幅も倍率に合わせてスケールします。

### 主な機能
- **アナログ時計表示**: 秒針/分針/時針を1秒ごとに更新
- **デジタル日時**: ヘッダ左側に現在日時を表示
- **テーマ切替**: 「カラー変更」でライト/ダークを手動切替
- **自動テーマ（Auto）**: 18:00〜05:59 をダーク、06:00〜17:59 をライトに自動切替
- **サイズ変更**: 「サイズ変更」で倍率を循環（1.0 → 1.5 → 2.0 → 2.5）。`factor.txt` に保存し次回起動時に復元
- **UIスケール**: デジタル表示やボタンのフォント/幅を倍率に応じて自動調整

### 画面と操作
- 上部ヘッダ順序
  - 「サイズ変更」ボタン
  - 現在日時（デジタル）
  - 「カラー変更」ボタン
  - 「Auto」チェック
- 中央: アナログ時計（目盛・数字・針）

### 技術仕様
- **言語/GUI**: Python 3.9+ / PySide6（Qt）
- **OS**: Windows 10/11 など（Qt 対応 OS）
- **更新間隔**: `UPDATE_INTERVAL = 1000` ms
- **自動テーマチェック間隔**: `AUTO_CHECK_INTERVAL_MS = 60000` ms

### 永続化されるファイル（本ディレクトリ内）
- `factor.txt`: サイズ倍率（1.0 / 1.5 / 2.0 / 2.5）
- `window_position_app_analog_clock.csv`: 本 PySide6 版では未使用（tkinter 版のみで利用）

### 起動方法
1. 依存関係のインストール

```powershell
pip install PySide6
```

2. 作業ディレクトリを本フォルダに移動（相対パスの `factor.txt` を本フォルダに作成するため）
3. スクリプトを実行

```bat
cd app_analog_clock
python app_analog_clock_2.py
```

PowerShell の例:
```powershell
Set-Location app_analog_clock
python .\app_analog_clock_2.py
```

### 設定/カスタマイズ（任意）
- コード内の定数で調整可能
  - `UPDATE_INTERVAL`: 時計とデジタル更新間隔（既定: 1000ms）
  - `AUTO_CHECK_INTERVAL_MS`: 自動テーマのチェック間隔（既定: 60000ms）
  - `LIGHT_THEME` / `DARK_THEME`: 各テーマの色（背景/線/数字/目盛/秒針）
  - `WINDOW_SIZE`, `CLOCK_RADIUS`, `LENGTH_*`, `NUMBER_DISTANCE`, `FONT_SIZE` など描画パラメータ
- 自動テーマ判定: `apply_auto_theme()`（`hour < 6` または `hour >= 18` をダークとする）

### 注意点/既知の制約
- `factor.txt` はカレントディレクトリに作成されます。基本的に本フォルダで実行してください。
- OS/ウィンドウマネージャの最小サイズ制約により、縮小が一度で反映されない場合があります（コード内で再調整を二度行っています）。
- タイトルバー配色は OS 側のテーマに依存し、本 PySide6 版では特別な切替処理は行っていません。

