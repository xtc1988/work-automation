# 工数管理システム自動化定義書

**更新日**: 2025年1月12日  
**バージョン**: 2.0

## 1. システム概要

**対象システム**: 勤務実績入力（日次用）  
**URL**: `cws` (相対パス)  
**認証方式**: セッション認証  
**文字コード**: Shift_JIS  
**対応ブラウザ**: Google Chrome (デバッグモード接続推奨)  

## 2. フォーム構造

### メインフォーム
```html
<form method="POST" action="cws" name="FormSingleAttendanceService">
```

### 必須隠しフィールド
```javascript
const hiddenFields = {
    "@SID": "", // セッションID
    "@SQ": "6",
    "@SN": "root.cws.shuro.personal.term_kinmu_input_day",
    "@FN": "1553890976",
    "@FS": "I",
    "@SRACT": "NONE", // アクション制御
    "@SRSNDF": "NONE"
};
```

## 3. 自動化システムアーキテクチャ

### 主要コンポーネント

1. **WorkTimeAutomation**: 基本自動化クラス
   - Seleniumを使用したブラウザ操作
   - エラーハンドリングとリトライ機能
   - スクリーンショット自動保存機能

2. **BulkWorkAutomation**: 一括処理クラス
   - 複数日の一括入力
   - CSVファイルからのデータ読み込み
   - 処理結果のCSV出力

3. **WorkDataCSVProcessor**: CSV処理クラス
   - CSVデータの検証
   - テンプレート生成機能
   - エンコーディング自動判定

## 4. 画面遷移フロー

### フェーズ1: 入力画面
- **画面**: 勤務実績入力（日次用）
- **主要操作**: 時間入力、プロジェクト選択、計算、次へ→

### フェーズ2: 確認画面 
- **画面**: 提出内容の確認
- **表示内容**: 入力データの確認表示
- **主要操作**: 入力完了、一時保存、戻る、修正

### 確認画面の構造
```html
<h2>提出内容の確認</h2>
<span>2025年07月01日 (火)</span>
<span class="status">未提出</span>

<!-- 勤務情報表示 -->
<table>
    <tr>
        <td>勤務名称</td><td>就業時間</td><td>打刻時間</td><td>実働時間数</td><td>在社時間数</td><td>在宅/出社</td>
    </tr>
    <tr>
        <td>出勤</td>
        <td>08:03 ～ 21:46</td>
        <td>08:03 -- 21:46</td>
        <td>10:43</td>
        <td>13:43</td>
        <td>在宅</td>
    </tr>
</table>

<!-- 休憩情報表示 -->
<table>
    <tr>
        <td>休憩ID</td><td>休憩時間帯</td><td>休憩時間数</td>
    </tr>
    <tr>
        <td>出勤休憩1</td><td>13:00 -- 14:00</td><td>1:00</td>
    </tr>
    <tr>
        <td>出勤休憩1</td><td>18:00 -- 20:00</td><td>2:00</td>
    </tr>
</table>

<!-- アクションボタン -->
<button>一時保存</button>
<button>入力完了</button>
<select>完了画面へ</select>
```

## 4. 入力要素の詳細

### 4.1 日付管理
- **表示**: `2025年07月01日 (火)`
- **セレクタ**: `#srw_page_navi_date span`
- **日付変更**: 前日/翌日ボタンによる遷移

#### 就業時間（開始）
```html
<input type="text" name="KNMTMRNGSTDI" value="08:03" maxlength="5">
```

#### 就業時間（終了）
```html
<input type="text" name="KNMTMRNGETDI" value="21:46" maxlength="5">
```

⚠️ **重要**: 実際のシステムでは時分が統合されたフィールドを使用（HH:MM形式）

### 4.2 在宅/出社区分 ⚠️**必須項目**
```html
<select name="GI_COMBOBOX38_Seq0S">
    <option value="1" selected>--</option>
    <option value="2">在宅</option>
    <option value="5">出社（通勤費往復）</option>
    <option value="6">出社（通勤費片道）</option>
    <option value="7">出社（通勤費なし）</option>
    <option value="4">その他</option>
</select>
```

### 4.3 休憩時間

#### 休憩開始時刻
```html
<input type="text" name="RCSST10_Seq0STH" value="13" size="2" maxlength="2">
<input type="text" name="RCSST10_Seq0STM" value="0" size="2" maxlength="2">
```

#### 休憩終了時刻
```html
<input type="text" name="RCSST10_Seq0ETH" value="14" size="2" maxlength="2">
<input type="text" name="RCSST10_Seq0ETM" value="0" size="2" maxlength="2">
```

### 4.4 プロジェクト報告（SlickGrid）
- **グリッドID**: `project-grid`
- **JSONデータ**: `gridJsonArray` hidden input
- **利用可能プロジェクト**:
  - `HI002-D004`: CJK 給与 > 不具合修正
  - `HI002-D005`: CJK 給与 > 顧客対応/問い合わせ対応
  - `HI019-C001`: プロダクト共通 > 全社/Div/Dept全体MTG
  - `HI019-C012`: プロダクト共通 > 1on1

## 5. エラーハンドリング

### 必須チェック項目
1. **在宅/出社区分**: 未選択の場合エラー
2. **プロジェクト実績**: 未入力の場合警告
3. **実働時間との差異**: 差異がある場合警告表示

### エラーメッセージ例
```html
<span class="error">2025年07月01日 (火)：エラー：在宅/出社区分が入力されていません。</span>
```

## 6. CSV入力フォーマット

### CSVファイル構造
| 列名 | 説明 | 形式 | 必須 |
|------|------|------|------|
| 日付 | 作業日 | YYYY-MM-DD | ○ |
| 開始時刻 | 就業開始時刻 | HH:MM | ○ |
| 終了時刻 | 就業終了時刻 | HH:MM | ○ |
| 在宅/出社区分 | 勤務場所 | 文字列 | ○ |
| 休憩1_開始 | 1つ目の休憩開始 | HH:MM | - |
| 休憩1_終了 | 1つ目の休憩終了 | HH:MM | - |
| 休憩2_開始 | 2つ目の休憩開始 | HH:MM | - |
| 休憩2_終了 | 2つ目の休憩終了 | HH:MM | - |
| プロジェクト1_時間 | 作業時間 | H:MM | - |
| プロジェクト1_備考 | 作業内容 | 文字列 | - |
| プロジェクト2_時間 | 作業時間 | H:MM | - |
| プロジェクト2_備考 | 作業内容 | 文字列 | - |

### サンプルCSV
```csv
日付,開始時刻,終了時刻,在宅/出社区分,休憩1_開始,休憩1_終了,休憩2_開始,休憩2_終了,プロジェクト1_時間,プロジェクト1_備考,プロジェクト2_時間,プロジェクト2_備考
2025-07-01,09:00,18:00,在宅,12:00,13:00,,,6:00,開発作業,2:00,問い合わせ対応
2025-07-02,09:00,19:00,出社（通勤費往復）,12:00,13:00,15:00,15:30,7:30,バグ修正,1:00,会議
```

## 7. エラーハンドリング詳細

### 7.1 自動リトライ機能
- **最大リトライ回数**: 3回
- **リトライ間隔**: 2秒
- **対象操作**: 
  - 要素の検索
  - クリック操作
  - 値の入力
  - ページ遷移

### 7.2 エラー時のスクリーンショット
- **保存先**: `logs/screenshots/`
- **ファイル名形式**: `screenshot_error_recovery_[before|after]_YYYYMMDD_HHMMSS.png`
- **自動保存タイミング**:
  - エラー発生直前
  - エラー回復後
  - 要素が見つからない場合

### 7.3 ログ機能
- **ログファイル**: `logs/work_automation_YYYYMMDD_HHMMSS.log`
- **ログレベル**: INFO, WARNING, ERROR
- **エンコーディング**: UTF-8
- **出力先**: ファイルとコンソール両方

## 8. プロジェクトコード一覧（最新）

### 利用可能なプロジェクトコード
- `HI002-D004`: CJK 給与 > 不具合修正
- `HI002-D005`: CJK 給与 > 顧客対応/問い合わせ対応
- `HI019-C001`: プロダクト共通 > 全社/Div/Dept全体MTG
- `HI019-C012`: プロダクト共通 > 1on1
- `HI019-D011`: プロダクト共通 > プロダクト開発業務（その他）
- `HI019-D015`: プロダクト共通 > 情報収集
- `WH099-Z999`: WH管理共通コード > 一般業務（その他）

## 9. Chrome デバッグモード起動方法

### Windows
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome_dev"
```

### Mac  
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_dev"
```

### Linux
```bash
google-chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_dev"
```

## 10. 実行方法

### 10.1 単日入力
```bash
python work_automation.py --date 2025-07-01 --start 09:00 --end 18:00 --work-type 在宅
```

### 10.2 CSV一括入力
```bash
python work_automation.py --csv input_data.csv
```

### 10.3 CSVテンプレート生成
```bash
python work_automation.py --template 5 --start-date 2025-07-01
```

## 11. トラブルシューティング

### 11.1 要素が見つからないエラー
- **原因**: ページの読み込みが完了していない、要素のセレクタが変更された
- **対策**: 
  - 待機時間の調整（デフォルト20秒）
  - セレクタの更新
  - スクリーンショットで状況確認

### 11.2 認証エラー
- **原因**: セッションタイムアウト、ログインが必要
- **対策**: 
  - ブラウザで手動ログイン後、スクリプト実行
  - デバッグモードでブラウザに接続

### 11.3 文字化け
- **原因**: エンコーディングの不一致
- **対策**: 
  - CSVファイルをShift_JISで保存
  - スクリプトが自動でエンコーディングを判定

## 12. 画面ベースの終了時間自動調整機能

### 12.1 機能概要
- CSVの値を無視し、画面上の既存の終了時間を基準に判断
- 画面の終了時間が22:15より大きい場合のみ22:00に自動調整
- より実際の運用状況に即した処理

### 12.2 処理フロー
1. 画面の終了時間フィールドを検索・取得
2. 現在の値を読み取り（例：17:53、22:30など）
3. 22:15との比較を実行
4. 22:15より大きい場合は22:00に更新
5. 結果をログに記録

### 12.3 フィールド検索パターン
- `name="KNMTMRNGETDI"`（最優先）
- `name="end_time"`
- CSS: `input[name*='ETDI']`
- XPath: `//input[contains(@name, 'ETDI')]`

## 13. 注意事項

1. **必須項目の確認**: 在宅/出社区分は必須項目
2. **プロジェクト時間の合計**: 実働時間と一致させる必要あり
3. **休憩時間**: 法定休憩時間を考慮
4. **提出前の確認**: 自動入力後も目視確認を推奨
5. **終了時間調整**: 画面の値が22:15以下の場合は調整されない