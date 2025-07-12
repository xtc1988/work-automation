#!/usr/bin/env python3
"""
環境セットアップスクリプト
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
        print("⚠️  仮想環境が無効です")
        return False

def install_packages():
    """パッケージのインストール"""
    print("📦 必要なパッケージをインストールしています...")
    
    # requirements.txt の存在確認
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"❌ requirements.txt が見つかりません: {requirements_file}")
        print("💡 手動でパッケージをインストールします...")
        return install_packages_manually()
    
    try:
        # requirements.txt からインストール
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ パッケージのインストールが完了しました")
            return True
        else:
            print(f"❌ パッケージインストールエラー:\n{result.stderr}")
            print("💡 手動インストールに切り替えます...")
            return install_packages_manually()
            
    except Exception as e:
        print(f"❌ インストール中にエラー: {e}")
        print("💡 手動インストールに切り替えます...")
        return install_packages_manually()

def install_packages_manually():
    """パッケージの手動インストール"""
    required_packages = [
        "selenium==4.23.0",
        "pandas==2.2.2", 
        "python-dateutil==2.9.0",
        "openpyxl==3.1.5"
    ]
    
    print("📦 必要なパッケージを個別にインストールします...")
    
    failed_packages = []
    
    for package in required_packages:
        print(f"  インストール中: {package}")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✅ {package}")
            else:
                print(f"  ❌ {package} - {result.stderr.strip()}")
                failed_packages.append(package)
                
        except Exception as e:
            print(f"  ❌ {package} - エラー: {e}")
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n⚠️  インストールに失敗したパッケージ: {len(failed_packages)}件")
        print("手動でインストールしてください:")
        for package in failed_packages:
            print(f"  pip install {package}")
        return False
    
    print("\n✅ 全パッケージのインストールが完了しました")
    return True

def test_imports():
    """重要なモジュールのインポートテスト"""
    print("🔍 パッケージのインポートテストを実行...")
    
    test_modules = [
        ("selenium", "Selenium WebDriver"),
        ("pandas", "Pandas データ処理"), 
        ("dateutil", "Python-dateutil 日付処理")
    ]
    
    failed_imports = []
    
    for module, description in test_modules:
        try:
            __import__(module)
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description} - インポート失敗")
            failed_imports.append(module)
    
    return len(failed_imports) == 0

def create_environment_info():
    """環境情報ファイルの作成"""
    info = {
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'platform': sys.platform,
        'virtual_env': check_virtual_environment(),
        'project_path': str(Path(__file__).parent.absolute())
    }
    
    info_file = Path(__file__).parent / "environment_info.txt"
    
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write("工数管理システム自動化ツール - 環境情報\n")
        f.write("=" * 50 + "\n\n")
        
        for key, value in info.items():
            f.write(f"{key}: {value}\n")
        
        f.write(f"\nセットアップ日時: {__import__('datetime').datetime.now()}\n")
    
    print(f"📄 環境情報を保存しました: {info_file}")

def check_current_directory():
    """現在のディレクトリが正しいかチェック"""
    current_dir = Path.cwd()
    script_dir = Path(__file__).parent
    
    print(f"📁 現在のディレクトリ: {current_dir}")
    print(f"📁 スクリプトのディレクトリ: {script_dir}")
    
    if current_dir != script_dir:
        print("⚠️  実行ディレクトリが異なります")
        print(f"   以下のコマンドで正しいディレクトリに移動してください:")
        print(f"   cd {script_dir}")
        
        response = input("\n現在のディレクトリで続行しますか？ (y/n): ")
        if response.lower() != 'y':
            return False
    
    return True

def main():
    """メイン処理"""
    print("🔧 工数管理システム自動化ツール - 環境セットアップ")
    print("=" * 60)
    
    # ディレクトリチェック
    if not check_current_directory():
        print("セットアップを中断しました。")
        return False
    
    # Python バージョンチェック
    if not check_python_version():
        return False
    
    # 仮想環境チェック
    in_venv = check_virtual_environment()
    if not in_venv:
        print("\n💡 仮想環境の作成を推奨します:")
        print("   python -m venv venv")
        print("   venv\\Scripts\\activate  # Windows")
        print("   source venv/bin/activate  # Linux/Mac")
        
        response = input("\n仮想環境なしで続行しますか？ (y/n): ")
        if response.lower() != 'y':
            print("セットアップを中断しました。")
            return False
    
    # パッケージインストール
    if not install_packages():
        print("\n❌ パッケージインストールに失敗しました")
        print("以下のコマンドで手動インストールを試してください:")
        print("   pip install selenium pandas python-dateutil openpyxl")
        print("または:")
        print("   pip install -r requirements.txt")
        
        # インストール失敗でも続行するか確認
        response = input("\nパッケージなしで続行しますか？ (y/n): ")
        if response.lower() != 'y':
            return False
    
    # インポートテスト
    if not test_imports():
        print("\n❌ パッケージのインポートに失敗しました")
        print("💡 解決方法:")
        print("1. 仮想環境が有効か確認")
        print("2. パッケージが正しくインストールされているか確認")
        print("3. pip list で確認")
        
        # インポート失敗でも続行するか確認
        response = input("\nインポートエラーを無視して続行しますか？ (y/n): ")
        if response.lower() != 'y':
            return False
    
    # 環境情報保存
    create_environment_info()
    
    print("\n🎉 環境セットアップが完了しました！")
    print("\n📋 次のステップ:")
    print("1. Chrome をデバッグモードで起動")
    print("2. 工数管理システムにログイン")
    print("3. python work_automation.py --help でヘルプを確認")
    print("4. QUICKSTART.md を参照して実際の操作を開始")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)