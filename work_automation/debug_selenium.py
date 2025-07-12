#!/usr/bin/env python3
"""
Seleniumデバッグスクリプト
エラーの詳細情報を取得して問題を特定
"""
import sys
import time
import logging
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from classes.work_time_automation import WorkTimeAutomation

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_page_info():
    """現在のページ情報をデバッグ"""
    print("🔍 Seleniumデバッグツール")
    print("=" * 60)
    
    try:
        # Chrome接続
        print("📌 Chromeブラウザに接続中...")
        automation = WorkTimeAutomation.connect_to_existing_chrome()
        print("✅ 接続成功")
        
        # ページ情報取得
        print("\n📄 ページ情報:")
        print(f"URL: {automation.driver.current_url}")
        print(f"タイトル: {automation.driver.title}")
        
        # スクリーンショット保存
        screenshot_path = automation.save_screenshot("debug_current_page")
        print(f"📸 スクリーンショット: {screenshot_path}")
        
        # フォーム要素の確認
        print("\n🔍 フォーム要素の検索:")
        
        # 時間入力フィールド
        time_fields = [
            ("KNMTMRNGSTH", "開始時刻（時）"),
            ("KNMTMRNGSTM", "開始時刻（分）"),
            ("KNMTMRNGETH", "終了時刻（時）"),
            ("KNMTMRNGETM", "終了時刻（分）")
        ]
        
        for field_name, description in time_fields:
            try:
                # NAME属性で検索
                elements = automation.driver.find_elements("name", field_name)
                if elements:
                    print(f"✅ {description} (name={field_name}): {len(elements)}個見つかりました")
                    for i, elem in enumerate(elements):
                        print(f"   要素{i+1}: タグ={elem.tag_name}, 表示={elem.is_displayed()}, 有効={elem.is_enabled()}")
                else:
                    print(f"❌ {description} (name={field_name}): 見つかりません")
                    
                # ID属性でも検索
                elements = automation.driver.find_elements("id", field_name)
                if elements:
                    print(f"   → ID属性で{len(elements)}個見つかりました")
                    
            except Exception as e:
                print(f"❌ {description}: エラー - {e}")
        
        # セレクトボックスの確認
        print("\n🔍 在宅/出社区分セレクトボックス:")
        try:
            selects = automation.driver.find_elements("tag name", "select")
            print(f"セレクトボックス総数: {len(selects)}個")
            
            for i, select in enumerate(selects[:5]):  # 最初の5個まで
                name = select.get_attribute("name") or "名前なし"
                id_attr = select.get_attribute("id") or "IDなし"
                print(f"  Select{i+1}: name={name}, id={id_attr}")
                
        except Exception as e:
            print(f"❌ セレクトボックス検索エラー: {e}")
        
        # ボタンの確認
        print("\n🔍 ナビゲーションボタン:")
        try:
            buttons = automation.driver.find_elements("tag name", "button")
            print(f"ボタン総数: {len(buttons)}個")
            
            # 翌日・前日ボタンを探す
            for button in buttons:
                title = button.get_attribute("title") or ""
                text = button.text or ""
                onclick = button.get_attribute("onclick") or ""
                if "翌日" in title or "翌日" in text or "次" in title or "次" in text:
                    print(f"  ✅ 翌日ボタン候補: title='{title}', text='{text}', onclick='{onclick[:50]}...'")
                elif "前日" in title or "前日" in text or "前" in title or "前" in text:
                    print(f"  ✅ 前日ボタン候補: title='{title}', text='{text}', onclick='{onclick[:50]}...'")
                    
        except Exception as e:
            print(f"❌ ボタン検索エラー: {e}")
        
        # onclick属性を持つ要素の確認
        print("\n🔍 onclick属性を持つナビゲーション要素:")
        try:
            # ToNextDateActionを含む要素
            next_elements = automation.driver.find_elements("xpath", "//*[contains(@onclick, 'ToNextDateAction')]")
            print(f"ToNextDateAction要素: {len(next_elements)}個")
            for i, elem in enumerate(next_elements[:3]):  # 最初の3個まで
                onclick = elem.get_attribute("onclick") or ""
                tag = elem.tag_name
                title = elem.get_attribute("title") or ""
                print(f"  要素{i+1}: <{tag}> title='{title}' onclick='{onclick[:60]}...'")
            
            # ToPrevDateActionを含む要素
            prev_elements = automation.driver.find_elements("xpath", "//*[contains(@onclick, 'ToPrevDateAction')]")
            print(f"ToPrevDateAction要素: {len(prev_elements)}個")
            for i, elem in enumerate(prev_elements[:3]):  # 最初の3個まで
                onclick = elem.get_attribute("onclick") or ""
                tag = elem.tag_name
                title = elem.get_attribute("title") or ""
                print(f"  要素{i+1}: <{tag}> title='{title}' onclick='{onclick[:60]}...'")
                
        except Exception as e:
            print(f"❌ onclick要素検索エラー: {e}")
        
        # リンクの確認
        print("\n🔍 ナビゲーションリンク:")
        try:
            links = automation.driver.find_elements("tag name", "a")
            nav_links = []
            
            for link in links:
                href = link.get_attribute("href") or ""
                text = link.text or ""
                title = link.get_attribute("title") or ""
                
                if any(word in text + title for word in ["翌日", "前日", "次", "前"]):
                    nav_links.append(f"  Link: href='{href[:50]}...', text='{text}', title='{title}'")
            
            if nav_links:
                print(f"ナビゲーションリンク候補: {len(nav_links)}個")
                for link in nav_links[:5]:
                    print(link)
            else:
                print("ナビゲーションリンクが見つかりません")
                
        except Exception as e:
            print(f"❌ リンク検索エラー: {e}")
        
        # JavaScript変数の確認
        print("\n🔍 JavaScript環境:")
        try:
            # jQuery の存在確認
            jquery_exists = automation.driver.execute_script("return typeof jQuery !== 'undefined'")
            print(f"jQuery: {'✅ 利用可能' if jquery_exists else '❌ 利用不可'}")
            
            # グローバル変数の確認
            window_keys = automation.driver.execute_script("return Object.keys(window).slice(0, 20)")
            print(f"Windowオブジェクトのキー（最初の20個）: {window_keys}")
            
        except Exception as e:
            print(f"❌ JavaScript確認エラー: {e}")
        
        print("\n✅ デバッグ完了")
        
    except Exception as e:
        print(f"❌ デバッグ中にエラー: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n💡 ヒント:")
        print("1. スクリーンショットを確認して画面の状態を把握")
        print("2. 要素が見つからない場合は、iframeやShadow DOMを確認")
        print("3. 動的に生成される要素の場合は、待機時間を増やす")
        print("4. JavaScriptでの要素操作も検討")

def test_simple_input():
    """簡単な入力テスト"""
    print("\n🧪 簡単な入力テスト")
    print("=" * 60)
    
    try:
        automation = WorkTimeAutomation.connect_to_existing_chrome()
        
        # テスト用のデータ
        test_data = {
            "start_time": "09:00",
            "end_time": "18:00",
            "location_type": "在宅"
        }
        
        print(f"テストデータ: {test_data}")
        
        # 入力実行
        result = automation.input_work_time(
            test_data["start_time"],
            test_data["end_time"],
            test_data["location_type"]
        )
        
        if result:
            print("✅ 入力成功！")
        else:
            print("❌ 入力失敗")
            print("logs/screenshots/ ディレクトリのスクリーンショットを確認してください")
            
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    """メイン処理"""
    print("Seleniumデバッグツール")
    print("1. ページ情報をデバッグ")
    print("2. 簡単な入力テスト")
    print("3. 両方実行")
    
    choice = input("\n選択してください (1-3): ")
    
    if choice == "1":
        debug_page_info()
    elif choice == "2":
        test_simple_input()
    elif choice == "3":
        debug_page_info()
        test_simple_input()
    else:
        print("無効な選択です")

if __name__ == "__main__":
    main()