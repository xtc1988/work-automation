# 工数管理システム自動化ツール

勤務実績入力（日次用）システムを自動化するPythonツールです。

## 機能

- CSV ファイルから複数日分の工数データを一括入力
- 既存のChrome ブラウザへの接続（ログイン済みセッションの利用）
- エラーハンドリングと検証機能
- 進捗管理とログ出力

## 必要要件

- Python 3.8以上
- Google Chrome ブラウザ
- Chrome WebDriver（seleniumが自動でダウンロード）

## インストール

### 🚀 クイックセットアップ（推奨）

```bash
# 1. 自動環境セットアップ
python setup_environment.py

# 2. クイックスタートガイドを参照
# QUICKSTART.md を確認してください
```

### 📋 手動セットアップ

```bash
# リポジトリのクローン
git clone [repository-url]
cd work_automation

# 仮想環境作成（推奨）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate     # Windows

# 必要なパッケージのインストール
pip install -r requirements.txt
```

## 使用方法

### 1. Chrome をデバッグモードで起動

Windows:
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome_dev"
```

Mac:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_dev"
```

Linux:
```bash
google-chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_dev"
```

### 2. 手動でログインと画面遷移

1. 起動したChromeで工数管理システムにログイン
2. 勤務実績入力（日次用）画面まで遷移

### 3. CSVテンプレートの生成

```bash
# 5日分のテンプレートを生成
python work_automation.py --create-template --days 5

# 特定の開始日から生成
python work_automation.py --create-template --days 5 --start-date 2025-07-01
```

### 4. CSVファイルの編集

生成された `work_template_YYYYMMDD.csv` をExcelまたはテキストエディタで開き、実際の勤務データを入力します。

#### CSV形式

| 列名 | 説明 | 形式 | 必須 |
|------|------|------|------|
| 日付 | 作業日 | YYYY-MM-DD | ○ |
| 開始時刻 | 就業開始時刻 | HH:MM | ○ |
| 終了時刻 | 就業終了時刻 | HH:MM | ○ |
| 在宅/出社区分 | 勤務場所 | 文字列 | ○ |
| 休憩1_開始 | 1つ目の休憩開始 | HH:MM | - |
| 休憩1_終了 | 1つ目の休憩終了 | HH:MM | - |
| プロジェクト1_時間 | 作業時間 | H:MM | - |
| プロジェクト1_備考 | 作業内容 | 文字列 | - |

#### 在宅/出社区分の選択肢
- 在宅
- 出社（通勤費往復）
- 出社（通勤費片道）
- 出社（通勤費なし）
- その他

### 5. データ検証（ドライラン）

```bash
# 実際の入力前にデータを検証
python work_automation.py --csv work_data.csv --dry-run
```

### 6. 一括処理の実行

```bash
# CSVファイルから一括入力
python work_automation.py --csv work_data.csv

# 確認なしで自動提出（注意して使用）
python work_automation.py --csv work_data.csv --auto-submit
```

## オプション

| オプション | 説明 |
|-----------|------|
| `--csv FILE` | 処理するCSVファイルを指定 |
| `--dry-run` | 実際の入力を行わず検証のみ実行 |
| `--create-template` | CSVテンプレートを生成 |
| `--days N` | テンプレート生成時の日数（デフォルト: 5） |
| `--start-date DATE` | テンプレートの開始日（YYYY-MM-DD） |
| `--auto-submit` | 確認画面で自動的に提出（デフォルトは一時保存） |

## ログファイル

処理結果は `logs/` ディレクトリに保存されます：
- `work_automation_YYYYMMDD_HHMMSS.log` - 詳細な処理ログ
- `work_result_YYYYMMDD_HHMMSS.csv` - 処理結果サマリー

## トラブルシューティング

### Chrome に接続できない場合
1. Chromeがデバッグモードで起動していることを確認
2. ポート9222が他のプロセスで使用されていないか確認
3. ファイアウォールがポート9222をブロックしていないか確認

### エラー：在宅/出社区分が入力されていません
CSVファイルの「在宅/出社区分」列に正しい値が入力されているか確認してください。

### プロジェクト時間の合計が実働時間と一致しない
休憩時間を除いた実働時間とプロジェクト時間の合計が一致するように調整してください。

## 注意事項

- 本ツールは既存のブラウザセッションを使用するため、事前にログインが必要です
- 大量のデータを処理する場合は、適度に休憩を入れてサーバーへの負荷を軽減してください
- エラーが発生した場合は、ログファイルを確認して原因を特定してください

## ライセンス

社内利用限定