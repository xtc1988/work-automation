#!/usr/bin/env python3
"""
統合テストスクリプト
"""
import sys
import subprocess
from pathlib import Path

def run_test_script(script_path):
    """テストスクリプトを実行"""
    try:
        result = subprocess.run([sys.executable, str(script_path)], 
                              capture_output=True, text=True, encoding='utf-8')
        
        print(f"\n=== {script_path.name} ===")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"テスト実行エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("🧪 工数管理システム自動化ツール - 統合テスト")
    print("=" * 60)
    
    project_root = Path(__file__).parent
    tests_dir = project_root / "tests"
    
    # 実行するテストスクリプト
    test_scripts = [
        project_root / "test_logging.py",
        tests_dir / "test_basic_functionality.py",
        tests_dir / "test_csv_processor.py"
    ]
    
    results = []
    
    for script in test_scripts:
        if script.exists():
            success = run_test_script(script)
            results.append((script.name, success))
        else:
            print(f"⚠️  テストスクリプトが見つかりません: {script}")
            results.append((script.name, False))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 統合テスト結果")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n📈 テスト合格率: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
    
    if passed == len(results):
        print("\n🎉 すべてのテストが成功しました！")
        print("\n📋 実装完了項目:")
        print("  ✓ プロジェクト構造")
        print("  ✓ 基本ファイル (requirements.txt, README.md)")
        print("  ✓ メインスクリプト (work_automation.py)")
        print("  ✓ 自動化クラス (WorkTimeAutomation)")
        print("  ✓ CSV処理クラス (WorkDataCSVProcessor)")
        print("  ✓ 一括処理クラス (BulkWorkAutomation)")
        print("  ✓ サンプルCSVファイル")
        print("  ✓ ログ機能")
        print("  ✓ 基本テスト")
        
        print("\n🚀 使用準備:")
        print("1. 仮想環境を作成: python -m venv venv")
        print("2. 仮想環境をアクティベート:")
        print("   - Windows: venv\\Scripts\\activate")
        print("   - Linux/Mac: source venv/bin/activate")
        print("3. 依存関係をインストール: pip install -r requirements.txt")
        print("4. Chromeをデバッグモードで起動")
        print("5. システムにログインして入力画面まで遷移")
        print("6. ツールを実行: python work_automation.py --help")
        
        return True
    else:
        print("\n⚠️  一部のテストが失敗しています。")
        print("   失敗したテストを確認して修正してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)