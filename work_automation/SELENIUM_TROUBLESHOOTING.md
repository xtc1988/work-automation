# 🔧 Seleniumエラー対処ガイド

## 🚨 発生したエラーと対策

### 1. **element not interactable エラー**

**エラーメッセージ:**
```
Message: element not interactable
```

**原因:**
- 要素が画面に表示されていない
- 要素が無効化されている
- 要素が他の要素に隠れている
- ページがまだ読み込み中

**対策実装済み:**
- ✅ 要素へのスクロール機能追加
- ✅ JavaScriptでのクリック代替
- ✅ 待機時間の追加
- ✅ 複数の検索方法（NAME, ID, CSS Selector）

### 2. **no such element エラー**

**エラーメッセージ:**
```
Message: no such element: Unable to locate element
```

**原因:**
- セレクタが間違っている
- 要素がまだ生成されていない
- iframe内の要素
- 動的に変わる要素名

**対策実装済み:**
- ✅ 複数のセレクタ戦略
- ✅ 明示的な待機（WebDriverWait）
- ✅ エラー時のスクリーンショット保存
- ✅ 代替方法（URL遷移）

### 3. **ナビゲーションボタンが見つからない エラー**

**エラーメッセージ:**
```
Message: no such element: Unable to locate element (翌日ボタン)
```

**原因:**
- onclick属性でlocation.hrefを使用するボタン実装
- 従来のbutton/aタグでない独自実装
- JavaScriptベースのナビゲーション

**対策実装済み:**
- ✅ onclick属性からURL抽出機能
- ✅ ToNextDateAction/ToPrevDateAction検索
- ✅ 正規表現でのURL抽出とダイレクト遷移
- ✅ 従来方法との併用フォールバック

## 🔍 デバッグ手順

### 1. **デバッグツールの実行**

```bash
# 現在のページ状態を確認
python debug_selenium.py

# 選択:
# 1 → ページ情報のデバッグ
# 2 → 簡単な入力テスト
# 3 → 両方実行
```

### 2. **スクリーンショット確認**

```bash
# スクリーンショットの保存場所
ls logs/screenshots/

# 最新のスクリーンショットを確認
ls -la logs/screenshots/ | tail -5
```

### 3. **ログファイル確認**

```bash
# 最新のログを確認
tail -f logs/work_automation_*.log
```

## 🛠️ トラブルシューティング

### 📋 チェックリスト

#### 1. **Chrome接続確認**
- [ ] Chromeがデバッグモードで起動している
- [ ] ポート9222で接続可能
- [ ] 正しいページが開いている
- [ ] ログイン済み

#### 2. **ページ状態確認**
- [ ] 勤務実績入力（日次用）画面が表示されている
- [ ] ページが完全に読み込まれている
- [ ] エラーメッセージが表示されていない
- [ ] ポップアップが表示されていない

#### 3. **要素の確認**
- [ ] 入力フィールドが有効
- [ ] セレクトボックスが選択可能
- [ ] ボタンがクリック可能
- [ ] 必須項目がすべて表示されている

### 🔧 手動での要素確認方法

1. **Chrome DevToolsを開く** (F12)

2. **コンソールで要素を確認**
```javascript
// 時間入力フィールド
document.getElementsByName("KNMTMRNGSTH")
document.getElementsByName("KNMTMRNGSTM")

// セレクトボックス
document.getElementsByName("GI_COMBOBOX38_Seq0S")

// ナビゲーション要素（onclick属性）
document.querySelectorAll("*[onclick*='ToNextDateAction']")
document.querySelectorAll("*[onclick*='ToPrevDateAction']")

// 従来のボタン検索
document.querySelectorAll("button[title*='翌日']")
```

3. **onclick属性の確認**
```javascript
// onclick属性を持つ要素を検索
Array.from(document.querySelectorAll("*[onclick]")).filter(elem => 
  elem.getAttribute("onclick").includes("ToNextDateAction")
)

// onclick属性の内容確認
element.getAttribute("onclick")

// onclick属性からURL抽出テスト
onclick_value = element.getAttribute("onclick")
url_match = onclick_value.match(/location\.href\s*=\s*['"]([^'"]+)['"]/);
if (url_match) console.log("抽出URL:", url_match[1]);
```

4. **要素の状態確認**
```javascript
// 要素が表示されているか
element.offsetParent !== null

// 要素が有効か
!element.disabled

// 要素の位置
element.getBoundingClientRect()

// onclick属性の実行テスト（注意：実際に実行される）
// element.click()
```

## 💡 改善提案

### 1. **画面要素の特定**

実際の画面で以下を確認してください：

1. **時間入力フィールドの正確な名前**
   - `name` 属性の値
   - `id` 属性の値
   - 親要素の構造

2. **セレクトボックスの正確な名前**
   - 在宅/出社区分の `name` 属性
   - option要素の value 値

3. **ナビゲーションボタン**
   - 翌日ボタンの実装方法（button/a/input）
   - クラス名やID

### 2. **カスタマイズ箇所**

`work_time_automation.py` の以下の部分をシステムに合わせて調整：

```python
# フィールド名の調整
field_names = {
    "start_hour": "KNMTMRNGSTH",  # 実際の name 属性に変更
    "start_min": "KNMTMRNGSTM",
    # ...
}

# セレクトボックス名の調整
location_select_name = "GI_COMBOBOX38_Seq0S"  # 実際の name 属性に変更

# ナビゲーションボタンのセレクタ
next_day_selectors = [
    "//button[contains(@title, '翌日')]",
    "//a[contains(@href, 'next')]",
    # 実際のセレクタを追加
]
```

## 🚀 実行例

### 基本的な実行
```bash
# 1. デバッグ情報取得
python debug_selenium.py
# → 1 を選択

# 2. スクリーンショット確認
# logs/screenshots/ を確認

# 3. 要素名を修正
# work_time_automation.py のセレクタを修正

# 4. 再実行
python work_automation.py --csv sample.csv --dry-run
```

### エラー時の対応
```bash
# 1. ログ確認
grep ERROR logs/work_automation_*.log | tail -20

# 2. スクリーンショット確認
ls -la logs/screenshots/ | grep error

# 3. デバッグツール実行
python debug_selenium.py

# 4. 手動で要素確認（Chrome DevTools）
```

## 📞 サポート

### よくある質問

**Q: 要素が見つからない**
A: debug_selenium.py を実行して実際の要素名を確認

**Q: クリックできない**
A: JavaScriptでのクリックが実装済み。それでも失敗する場合は要素が無効化されている可能性

**Q: 画面遷移しない**
A: URLパラメータでの遷移も実装済み。実際のURL構造に合わせて調整が必要

**Q: どこを修正すればいい？**
A: work_time_automation.py のフィールド名とセレクタを実際の画面に合わせて修正

---

💡 **重要**: 実際のシステムの画面構造に合わせてセレクタを調整することが最も重要です。debug_selenium.py で現在の画面情報を取得して、適切なセレクタを特定してください。