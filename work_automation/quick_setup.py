#!/usr/bin/env python3
"""
クイックセットアップスクリプト（最小限）
requirements.txt が見つからない場合の緊急対応
"""
import sys
import subprocess
from pathlib import Path

def quick_install():
    """必要最小限のパッケージを緊急インストール"""
    print("🚨 クイックセットアップ - 緊急パッケージインストール")
    print("=" * 50)
    
    packages = [
        "selenium",
        "pandas", 
        "python-dateutil",
        "openpyxl"
    ]
    
    print(f"📦 {len(packages)}個のパッケージをインストールします...")
    
    for package in packages:
        print(f"  📥 {package} をインストール中...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✅ {package} - 成功")
            else:
                print(f"  ❌ {package} - 失敗: {result.stderr.strip()}")
                
        except Exception as e:
            print(f"  ❌ {package} - エラー: {e}")
    
    print("\n🔍 インストール確認...")
    
    # インポートテスト
    test_modules = [
        ("selenium", "Selenium WebDriver"),
        ("pandas", "Pandas データ処理"),
        ("dateutil", "Python-dateutil 日付処理"),
        ("openpyxl", "OpenPyXL Excel処理")
    ]
    
    success_count = 0
    
    for module, description in test_modules:
        try:
            __import__(module)
            print(f"  ✅ {description}")
            success_count += 1
        except ImportError:
            print(f"  ❌ {description} - インポート失敗")
    
    print(f"\n📊 結果: {success_count}/{len(test_modules)} パッケージが利用可能")
    
    if success_count == len(test_modules):
        print("🎉 全パッケージのインストールが完了しました！")
        print("\n📋 次のステップ:")
        print("1. python work_automation.py --help でヘルプを確認")
        print("2. QUICKSTART.md を参照して操作を開始")
        return True
    else:
        print("⚠️  一部のパッケージが利用できません")
        print("手動で以下のコマンドを実行してください:")
        for module, description in test_modules:
            try:
                __import__(module)
            except ImportError:
                print(f"  pip install {module}")
        return False

def create_requirements_file():
    """requirements.txt を作成"""
    requirements_content = """selenium==4.23.0
pandas==2.2.2
python-dateutil==2.9.0
openpyxl==3.1.5"""
    
    requirements_file = Path("requirements.txt")
    
    with open(requirements_file, 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    
    print(f"📄 requirements.txt を作成しました: {requirements_file.absolute()}")

def main():
    """メイン処理"""
    print("🚀 クイックセットアップ（緊急対応版）")
    
    # requirements.txt がない場合は作成
    if not Path("requirements.txt").exists():
        print("📄 requirements.txt が見つかりません。作成します...")
        create_requirements_file()
    
    # パッケージインストール
    success = quick_install()
    
    if success:
        print("\n✅ セットアップ完了！")
        print("通常の setup_environment.py も使用できるようになりました。")
    else:
        print("\n⚠️  一部のパッケージで問題があります。")
        print("詳細なセットアップは setup_environment.py を使用してください。")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)