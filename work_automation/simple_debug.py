#!/usr/bin/env python3
"""
Selenium不要の簡易デバッグスクリプト
Chrome DevToolsのRemote Debugging APIを使用
"""

import json
import urllib.request
import urllib.parse

def check_chrome_connection():
    """Chrome DevTools APIへの接続確認"""
    try:
        response = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
        tabs = json.loads(response.read().decode('utf-8'))
        
        print("🔍 Chrome DevTools API 接続確認")
        print("=" * 50)
        print(f"アクティブなタブ: {len(tabs)}個")
        
        for i, tab in enumerate(tabs):
            if tab.get('type') == 'page':
                print(f"  タブ{i+1}: {tab.get('title', '無題')}")
                print(f"         URL: {tab.get('url', '不明')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Chrome接続エラー: {e}")
        print("\n💡 解決方法:")
        print("1. Chromeをデバッグモードで起動")
        print("   chrome.exe --remote-debugging-port=9222 --user-data-dir=\"C:\\temp\\chrome_dev\"")
        print("2. 工数管理システムにログイン")
        print("3. 勤務実績入力画面まで遷移")
        return False

def execute_js_command(command):
    """JavaScriptコマンドをChrome DevTools APIで実行"""
    try:
        # アクティブなタブを取得
        response = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
        tabs = json.loads(response.read().decode('utf-8'))
        
        active_tab = None
        for tab in tabs:
            if tab.get('type') == 'page' and '工数' in tab.get('title', ''):
                active_tab = tab
                break
        
        if not active_tab:
            # 最初のページタブを使用
            for tab in tabs:
                if tab.get('type') == 'page':
                    active_tab = tab
                    break
        
        if not active_tab:
            print("❌ アクティブなタブが見つかりません")
            return None
        
        print(f"📄 対象タブ: {active_tab.get('title', '無題')}")
        
        # WebSocket接続は複雑なので、簡易版として手動実行を案内
        print(f"📋 以下のJavaScriptコードを Chrome DevTools Console で実行してください:")
        print("-" * 60)
        print(command)
        print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ JavaScript実行エラー: {e}")
        return None

def main():
    """メイン処理"""
    print("🚀 簡易デバッグツール (Selenium不要)")
    print("=" * 60)
    
    if not check_chrome_connection():
        return
    
    print("\n" + "=" * 60)
    print("📋 デバッグコマンド一覧")
    print("=" * 60)
    
    commands = [
        ("1. 基本情報確認", """
console.log("=== 基本情報 ===");
console.log("URL:", location.href);
console.log("Title:", document.title);
console.log("ReadyState:", document.readyState);
"""),
        
        ("2. 時間フィールド検索", """
console.log("=== 時間フィールド検索 ===");
console.log("KNMTMRNGSTH:", document.getElementsByName("KNMTMRNGSTH").length, "個");
console.log("KNMTMRNGSTM:", document.getElementsByName("KNMTMRNGSTM").length, "個");
console.log("KNMTMRNGETH:", document.getElementsByName("KNMTMRNGETH").length, "個");
console.log("KNMTMRNGETM:", document.getElementsByName("KNMTMRNGETM").length, "個");

let startHour = document.getElementsByName("KNMTMRNGSTH")[0];
if (startHour) {
    console.log("✅ KNMTMRNGSTH 詳細:");
    console.log("  タグ:", startHour.tagName);
    console.log("  タイプ:", startHour.type);
    console.log("  値:", startHour.value);
    console.log("  表示:", startHour.offsetParent !== null);
    console.log("  有効:", !startHour.disabled);
} else {
    console.log("❌ KNMTMRNGSTH が見つかりません");
}
"""),
        
        ("3. iframe確認", """
console.log("=== iframe確認 ===");
let iframes = document.querySelectorAll("iframe");
console.log("iframe数:", iframes.length);

iframes.forEach((iframe, index) => {
    console.log(`iframe${index}:`, iframe.src || iframe.name || "無名");
    try {
        let iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        let elements = iframeDoc.getElementsByName("KNMTMRNGSTH");
        console.log(`  iframe${index}内のKNMTMRNGSTH:`, elements.length, "個");
        if (elements.length > 0) {
            console.log("  ✅ iframe内で発見！");
        }
    } catch(e) {
        console.log(`  iframe${index}: アクセス不可 (${e.message})`);
    }
});
"""),
        
        ("4. フォーム確認", """
console.log("=== フォーム確認 ===");
console.log("フォーム数:", document.forms.length);

let targetForm = document.forms["FormSingleAttendanceService"];
if (targetForm) {
    console.log("✅ FormSingleAttendanceService 発見");
    console.log("  要素数:", targetForm.elements.length);
    
    let textInputs = targetForm.querySelectorAll("input[type=text]");
    console.log("  テキスト入力:", textInputs.length, "個");
    
    textInputs.forEach((input, i) => {
        if (input.name.includes("KNM") || input.name.includes("TMR")) {
            console.log(`    ⭐ ${i+1}: name="${input.name}" value="${input.value}"`);
        }
    });
} else {
    console.log("❌ FormSingleAttendanceService なし");
}
"""),
        
        ("5. 類似要素検索", """
console.log("=== 類似要素検索 ===");

// KNM含む要素
let knmElements = document.querySelectorAll("*[name*='KNM']");
console.log("KNM含む要素:", knmElements.length, "個");
knmElements.forEach(elem => {
    console.log(`  name="${elem.name}" tag="${elem.tagName}"`);
});

// TMR含む要素
let tmrElements = document.querySelectorAll("*[name*='TMR']");
console.log("TMR含む要素:", tmrElements.length, "個");
tmrElements.forEach(elem => {
    console.log(`  name="${elem.name}" tag="${elem.tagName}"`);
});

// 全テキスト入力で時間関連を検索
console.log("=== 時間関連候補 ===");
document.querySelectorAll("input[type=text]").forEach(input => {
    let name = input.name.toLowerCase();
    if (name.includes("time") || name.includes("hour") || name.includes("min") || 
        name.includes("tm") || name.includes("hr") || name.includes("st") || name.includes("et")) {
        console.log(`候補: name="${input.name}" value="${input.value}"`);
    }
});
"""),
        
        ("6. 全テキスト入力一覧", """
console.log("=== 全テキスト入力要素 ===");
let allInputs = document.querySelectorAll("input[type=text]");
console.log("総数:", allInputs.length, "個");

allInputs.forEach((input, i) => {
    if (i < 20) {  // 最初の20個まで表示
        console.log(`${i+1}: name="${input.name}" id="${input.id}" value="${input.value}"`);
    }
});

if (allInputs.length > 20) {
    console.log(`... 他 ${allInputs.length - 20} 個`);
}
""")
    ]
    
    for title, command in commands:
        print(f"\n{title}")
        print("-" * 40)
        print("以下をChrome DevTools Consoleにコピー&ペーストして実行:")
        print(command.strip())
        input("\n⏸️  実行完了後、Enterキーを押してください...")
    
    print("\n" + "=" * 60)
    print("📊 結果の報告")
    print("=" * 60)
    print("実行結果をコピーして報告してください。")
    print("特に以下の情報が重要です:")
    print("1. KNMTMRNGSTH の検索結果 (個数)")
    print("2. iframe内での検索結果")
    print("3. 類似要素の発見状況")
    print("4. フォーム内のテキスト入力要素一覧")

if __name__ == "__main__":
    main()