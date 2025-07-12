# 🚀 クイックスタートガイド

## 📋 最小手順で実行

### 1️⃣ 環境準備（5分）

#### 🚀 簡単自動セットアップ
```bash
# 1. プロジェクトディレクトリに移動
cd work_automation

# 2. 自動セットアップ実行
python auto_setup.py
```

#### 📋 手動セットアップ（推奨）
```bash
# 1. プロジェクトディレクトリに移動
cd work_automation

# 2. 仮想環境作成
python -m venv venv

# 3. 仮想環境をアクティベート
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. パッケージインストール
pip install -r requirements.txt
```

#### 🆘 エラー時の緊急対応
```bash
# requirements.txt が見つからない場合
python quick_setup.py

# または手動インストール
pip install selenium pandas python-dateutil openpyxl
```

### 2️⃣ Chrome 準備（2分）

```bash
# Chrome をデバッグモードで起動（新しいターミナルで実行）

# Windows:
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome_dev"

# Mac:
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_dev"

# Linux:
google-chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_dev"
```

### 3️⃣ システムログイン（手動）

1. 起動したChromeで工数管理システムにログイン
2. **勤務実績入力（日次用）画面まで遷移**

### 4️⃣ CSVテンプレート作成（1分）

```bash
# 5日分のテンプレート生成
python work_automation.py --create-template --days 5

# 生成されたファイル: work_template_YYYYMMDD.csv
```

### 5️⃣ データ入力（3分）

生成されたCSVファイルをExcelで開いて実際のデータを入力：

| 日付 | 開始時刻 | 終了時刻 | 在宅/出社区分 | 休憩1_開始 | 休憩1_終了 | プロジェクト1_時間 | プロジェクト1_備考 |
|------|----------|----------|---------------|------------|------------|-------------------|-------------------|
| 2025-07-08 | 09:00 | 18:00 | 在宅 | 12:00 | 13:00 | 6:00 | 開発作業 |
| 2025-07-09 | 09:00 | 18:00 | 在宅 | 12:00 | 13:00 | 7:00 | テスト作業 |

### 6️⃣ 検証実行（1分）

```bash
# データ検証（実際の入力は行わない）
python work_automation.py --csv work_template_YYYYMMDD.csv --dry-run
```

### 7️⃣ 自動実行（実行時間は日数による）

```bash
# 一時保存で実行
python work_automation.py --csv work_template_YYYYMMDD.csv

# 自動提出で実行（注意！）
python work_automation.py --csv work_template_YYYYMMDD.csv --auto-submit
```

## ⚡ ワンライナー実行例

```bash
# テンプレート生成 → 検証 → 実行 の流れ
python work_automation.py --create-template --days 3 && \
echo "CSVファイルを編集してください" && \
read -p "編集完了後 Enter を押してください" && \
python work_automation.py --csv work_template_$(date +%Y%m%d).csv --dry-run && \
python work_automation.py --csv work_template_$(date +%Y%m%d).csv
```

## 🔧 トラブル時の確認項目

### Chrome接続エラー
```bash
# ポート確認
netstat -an | grep 9222

# プロセス確認
ps aux | grep chrome
```

### データエラー
```bash
# ログ確認
tail -f logs/work_automation_*.log

# エラー詳細確認
python work_automation.py --csv your_file.csv --dry-run
```

### 完了確認
```bash
# 処理結果確認
ls -la logs/work_result_*.csv
```

## 📞 よくある質問

**Q: 途中で失敗した場合は？**
A: ログファイルで失敗箇所を確認し、該当日から再実行

**Q: プロジェクト時間の計算が合わない？**
A: 休憩時間を除いた実働時間とプロジェクト時間の合計を一致させる

**Q: 在宅/出社区分の選択肢は？**
A: `在宅`, `出社（通勤費往復）`, `出社（通勤費片道）`, `出社（通勤費なし）`, `その他`

**Q: 複数のプロジェクトがある場合は？**
A: プロジェクト2_時間, プロジェクト3_時間... の列を使用

---

💡 **初回は少ない日数（1-2日）でテストしてから本格運用を推奨します**