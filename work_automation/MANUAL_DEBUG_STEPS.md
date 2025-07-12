# 🔍 手動デバッグ手順書

## ⚠️ KNMTMRNGSTH要素が見つからないエラーの調査

現在 `name=KNMTMRNGSTH` の要素が見つからないエラーが発生しています。  
定義書では確実に存在するはずの要素なので、以下の手順で原因を特定してください。

## 📋 Chrome DevTools での確認手順

### 1️⃣ **基本的な要素確認**

1. **Chrome で勤務実績入力画面を開く**
2. **F12 でDevToolsを開く**
3. **Consoleタブを選択**
4. **以下のコマンドを順番に実行**

```javascript
// 1. ページの基本情報確認
console.log("URL:", location.href);
console.log("Title:", document.title);

// 2. 時間入力フィールドの直接検索
console.log("=== 時間フィールド検索 ===");
console.log("KNMTMRNGSTH:", document.getElementsByName("KNMTMRNGSTH"));
console.log("KNMTMRNGSTM:", document.getElementsByName("KNMTMRNGSTM"));
console.log("KNMTMRNGETH:", document.getElementsByName("KNMTMRNGETH"));
console.log("KNMTMRNGETM:", document.getElementsByName("KNMTMRNGETM"));

// 3. 結果の詳細確認
let startHour = document.getElementsByName("KNMTMRNGSTH")[0];
if (startHour) {
    console.log("✅ 要素発見:");
    console.log("  タグ:", startHour.tagName);
    console.log("  タイプ:", startHour.type);
    console.log("  値:", startHour.value);
    console.log("  表示:", startHour.offsetParent !== null);
    console.log("  有効:", !startHour.disabled);
} else {
    console.log("❌ KNMTMRNGSTH が見つかりません");
}
```

### 2️⃣ **iframe の確認**

```javascript
// iframe内に要素がある可能性を確認
console.log("=== iframe確認 ===");
console.log("iframe数:", document.querySelectorAll("iframe").length);

// 各iframeを確認
document.querySelectorAll("iframe").forEach((iframe, index) => {
    console.log(`iframe${index}:`, iframe.src || iframe.name || "無名");
    
    try {
        let iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        let elements = iframeDoc.getElementsByName("KNMTMRNGSTH");
        console.log(`  iframe${index}内のKNMTMRNGSTH:`, elements.length, "個");
    } catch(e) {
        console.log(`  iframe${index}: アクセス不可 (${e.message})`);
    }
});
```

### 3️⃣ **フォームの確認**

```javascript
// フォーム構造の確認
console.log("=== フォーム確認 ===");
console.log("フォーム数:", document.forms.length);

// FormSingleAttendanceService の確認
let targetForm = document.forms["FormSingleAttendanceService"];
if (targetForm) {
    console.log("✅ FormSingleAttendanceService 発見");
    console.log("  要素数:", targetForm.elements.length);
    
    // フォーム内の input[type=text] を全検索
    let textInputs = targetForm.querySelectorAll("input[type=text]");
    console.log("  テキスト入力フィールド:", textInputs.length, "個");
    
    textInputs.forEach((input, i) => {
        console.log(`    ${i+1}: name="${input.name}" value="${input.value}"`);
    });
} else {
    console.log("❌ FormSingleAttendanceService が見つかりません");
    
    // 全フォームを確認
    Array.from(document.forms).forEach((form, i) => {
        console.log(`  フォーム${i}: name="${form.name}" action="${form.action}"`);
    });
}
```

### 4️⃣ **動的読み込みの確認**

```javascript
// ページが完全に読み込まれているか確認
console.log("=== 読み込み状態確認 ===");
console.log("readyState:", document.readyState);
console.log("DOMContentLoaded:", document.readyState === "complete");

// JavaScriptで動的に生成される要素の確認
setTimeout(() => {
    console.log("=== 3秒後の再確認 ===");
    console.log("KNMTMRNGSTH:", document.getElementsByName("KNMTMRNGSTH").length, "個");
}, 3000);
```

### 5️⃣ **類似要素の検索**

```javascript
// 類似する名前の要素を検索
console.log("=== 類似要素検索 ===");

// name属性にKNMを含む要素
let knmElements = document.querySelectorAll("*[name*='KNM']");
console.log("KNM を含む要素:", knmElements.length, "個");
knmElements.forEach(elem => {
    console.log(`  name="${elem.name}" tag="${elem.tagName}"`);
});

// name属性にTMRを含む要素
let tmrElements = document.querySelectorAll("*[name*='TMR']");
console.log("TMR を含む要素:", tmrElements.length, "個");
tmrElements.forEach(elem => {
    console.log(`  name="${elem.name}" tag="${elem.tagName}"`);
});

// name属性にSTHを含む要素
let sthElements = document.querySelectorAll("*[name*='STH']");
console.log("STH を含む要素:", sthElements.length, "個");
sthElements.forEach(elem => {
    console.log(`  name="${elem.name}" tag="${elem.tagName}"`);
});
```

## 📊 結果の判定

### ✅ **要素が見つかった場合**
- Seleniumの待機時間不足の可能性
- iframe内の要素をSeleniumが検索できていない
- 要素が無効化されている

### ❌ **要素が見つからない場合**
- ページが正しく読み込まれていない
- 実際のHTMLが定義書と異なる
- JavaScriptで動的に生成される要素
- 別のフレームやウィンドウに存在

## 🚨 緊急時の対応

要素が全く見つからない場合は、以下を実行：

```javascript
// 全ての input[type=text] を一覧表示
console.log("=== 全テキスト入力要素 ===");
document.querySelectorAll("input[type=text]").forEach((input, i) => {
    console.log(`${i+1}: name="${input.name}" id="${input.id}" value="${input.value}"`);
});

// 時間関連と思われる要素を検索
console.log("=== 時間関連要素候補 ===");
document.querySelectorAll("input[type=text]").forEach(input => {
    let name = input.name.toLowerCase();
    if (name.includes("time") || name.includes("hour") || name.includes("min") || 
        name.includes("tm") || name.includes("hr") || name.includes("st") || name.includes("et")) {
        console.log(`候補: name="${input.name}" value="${input.value}"`);
    }
});
```

## 📞 次のステップ

この手順を実行した結果を教えてください：

1. **要素が見つかった** → iframe対応やセレクタ修正を実施
2. **要素が見つからない** → 実際のHTML構造の再調査
3. **類似要素が見つかった** → 正しいname属性に修正
4. **全く違う構造だった** → 新しい実装方針を検討

---

💡 **重要**: この調査結果に基づいて、Seleniumコードの修正方針を決定します。