#!/usr/bin/env python3
"""
自動セットアップスクリプト（対話なし）
"""
import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Python バージョンチェック"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8以上が必要です。現在のバージョン: {version.major}.{version.minor}")
        return False
    
    print(f"✅ Python バージョン: {version.major}.{version.minor}.{version.micro}")
    return True

def check_virtual_environment():
    """仮想環境の確認"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 仮想環境が有効です")
        return True
    else:
        print("⚠️  仮想環境が無効です（続行します）")
        return False

def install_packages_auto():
    """パッケージの自動インストール"""
    print("📦 必要なパッケージを自動インストールします...")
    
    # requirements.txt の存在確認・作成
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("📄 requirements.txt を作成します...")
        requirements_content = """selenium==4.23.0
pandas==2.2.2
python-dateutil==2.9.0
openpyxl==3.1.5"""
        
        with open(requirements_file, 'w', encoding='utf-8') as f:
            f.write(requirements_content)
        print(f"✅ requirements.txt を作成しました")
    
    # パッケージインストール
    try:
        print("📥 requirements.txt からインストール中...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ requirements.txt からのインストール完了")
            return True
        else:
            print(f"⚠️  requirements.txt でエラー: {result.stderr.strip()}")
            print("💡 個別インストールに切り替えます...")
            
    except Exception as e:
        print(f"⚠️  requirements.txt インストール失敗: {e}")
        print("💡 個別インストールに切り替えます...")
    
    # 個別インストール
    packages = [
        "selenium==4.23.0",
        "pandas==2.2.2", 
        "python-dateutil==2.9.0",
        "openpyxl==3.1.5"
    ]
    
    success_count = 0
    
    for package in packages:
        print(f"📥 {package} をインストール中...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✅ {package}")
                success_count += 1
            else:
                print(f"  ❌ {package} - {result.stderr.strip()}")
                
        except Exception as e:
            print(f"  ❌ {package} - エラー: {e}")
    
    if success_count == len(packages):
        print("✅ 全パッケージのインストール完了")
        return True
    else:
        print(f"⚠️  {success_count}/{len(packages)} パッケージがインストール完了")
        return success_count > 0  # 一部でも成功していれば続行

def test_imports():
    """重要なモジュールのインポートテスト"""
    print("🔍 パッケージのインポートテストを実行...")
    
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
            print(f"✅ {description}")
            success_count += 1
        except ImportError:
            print(f"❌ {description} - インポート失敗")
    
    print(f"📊 インポート結果: {success_count}/{len(test_modules)} 成功")
    return success_count >= 3  # 最低3つ成功していれば OK

def create_environment_info():
    """環境情報ファイルの作成"""
    info = {
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'platform': sys.platform,
        'virtual_env': check_virtual_environment(),
        'project_path': str(Path(__file__).parent.absolute()),
        'setup_type': 'auto_setup'
    }
    
    info_file = Path(__file__).parent / "environment_info.txt"
    
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write("工数管理システム自動化ツール - 環境情報（自動セットアップ）\n")
        f.write("=" * 60 + "\n\n")
        
        for key, value in info.items():
            f.write(f"{key}: {value}\n")
        
        # pip list の結果も追加
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                f.write(f"\n--- インストール済みパッケージ ---\n")
                f.write(result.stdout)
        except:
            pass
        
        f.write(f"\nセットアップ日時: {__import__('datetime').datetime.now()}\n")
    
    print(f"📄 環境情報を保存しました: {info_file}")

def main():
    """メイン処理"""
    print("🚀 工数管理システム自動化ツール - 自動セットアップ")
    print("=" * 60)
    print("（対話なしで自動実行します）")
    
    # 現在のディレクトリ表示
    current_dir = Path.cwd()
    script_dir = Path(__file__).parent
    print(f"📁 実行ディレクトリ: {current_dir}")
    print(f"📁 スクリプトディレクトリ: {script_dir}")
    
    if current_dir != script_dir:
        print("⚠️  実行ディレクトリが異なりますが、続行します")
    
    # Python バージョンチェック
    if not check_python_version():
        print("❌ Python バージョンが不適切です")
        return False
    
    # 仮想環境チェック（警告のみ）
    check_virtual_environment()
    
    # パッケージインストール
    if not install_packages_auto():
        print("❌ パッケージインストールに重大な問題があります")
        print("💡 手動で以下を実行してください:")
        print("   pip install selenium pandas python-dateutil openpyxl")
        # ただし続行する
    
    # インポートテスト
    if not test_imports():
        print("⚠️  一部パッケージのインポートに失敗しましたが続行します")
    
    # 環境情報保存
    create_environment_info()
    
    print("\n🎉 自動セットアップが完了しました！")
    print("\n📋 次のステップ:")
    print("1. Chrome をデバッグモードで起動:")
    print("   Windows: \"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" --remote-debugging-port=9222 --user-data-dir=\"C:\\temp\\chrome_dev\"")
    print("   Linux: google-chrome --remote-debugging-port=9222 --user-data-dir=\"/tmp/chrome_dev\"")
    print("2. 工数管理システムにログインして入力画面まで遷移")
    print("3. python work_automation.py --help でヘルプを確認")
    print("4. QUICKSTART.md を参照して実際の操作を開始")
    
    print("\n💡 問題がある場合:")
    print("   python quick_setup.py で緊急セットアップを試してください")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)