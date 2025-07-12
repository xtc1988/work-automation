#!/usr/bin/env python3
"""
基本機能のテスト（selenium なし）
"""
import unittest
import tempfile
import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_project_structure():
    """プロジェクト構造のテスト"""
    print("=== プロジェクト構造テスト ===")
    
    project_root = Path(__file__).parent.parent
    
    # 必須ファイルの確認
    required_files = [
        "requirements.txt",
        "README.md", 
        "work_automation.py",
        "definition.md",
        "classes/__init__.py",
        "classes/work_time_automation.py",
        "classes/csv_processor.py",
        "classes/bulk_automation.py",
        "templates/sample_work_data.csv"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"✓ {file_path}")
    
    # 必須ディレクトリの確認
    required_dirs = [
        "classes",
        "templates", 
        "logs",
        "tests"
    ]
    
    missing_dirs = []
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
        else:
            print(f"✓ {dir_path}/")
    
    if missing_files or missing_dirs:
        print("\n❌ 不足ファイル・ディレクトリ:")
        for item in missing_files + missing_dirs:
            print(f"  - {item}")
        return False
    
    print("\n✅ プロジェクト構造は正常です")
    return True


def test_file_syntax():
    """Pythonファイルの構文チェック"""
    print("\n=== 構文チェック ===")
    
    project_root = Path(__file__).parent.parent
    
    python_files = [
        "work_automation.py",
        "classes/__init__.py",
        "classes/work_time_automation.py",
        "classes/csv_processor.py", 
        "classes/bulk_automation.py"
    ]
    
    syntax_errors = []
    
    for file_path in python_files:
        full_path = project_root / file_path
        
        if not full_path.exists():
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # 構文チェック
            compile(source, str(full_path), 'exec')
            print(f"✓ {file_path} - 構文OK")
            
        except SyntaxError as e:
            syntax_errors.append(f"{file_path}: {e}")
            print(f"✗ {file_path} - 構文エラー: {e}")
        except Exception as e:
            print(f"⚠️  {file_path} - チェック中にエラー: {e}")
    
    if syntax_errors:
        print("\n❌ 構文エラーがあります:")
        for error in syntax_errors:
            print(f"  - {error}")
        return False
    
    print("\n✅ 全ファイルの構文は正常です")
    return True


def test_csv_template():
    """CSVテンプレートの検証"""
    print("\n=== CSVテンプレート検証 ===")
    
    project_root = Path(__file__).parent.parent
    csv_file = project_root / "templates" / "sample_work_data.csv"
    
    if not csv_file.exists():
        print("❌ sample_work_data.csv が見つかりません")
        return False
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print("❌ CSVファイルが空です")
            return False
        
        # ヘッダー行の確認
        header = lines[0].strip()
        required_columns = [
            "日付", "開始時刻", "終了時刻", "在宅/出社区分",
            "休憩1_開始", "休憩1_終了", 
            "プロジェクト1_時間", "プロジェクト1_備考"
        ]
        
        for column in required_columns:
            if column not in header:
                print(f"❌ 必須列が見つかりません: {column}")
                return False
        
        print(f"✓ ヘッダー行: {len(header.split(','))}列")
        print(f"✓ データ行: {len(lines) - 1}行")
        
        # データ行の基本チェック
        for i, line in enumerate(lines[1:], 2):
            columns = line.strip().split(',')
            if len(columns) < len(required_columns):
                print(f"⚠️  行{i}: 列数が不足 ({len(columns)} < {len(required_columns)})")
        
        print("✅ CSVテンプレートは正常です")
        return True
        
    except Exception as e:
        print(f"❌ CSVファイル読み込みエラー: {e}")
        return False


def test_documentation():
    """ドキュメントの基本チェック"""
    print("\n=== ドキュメントチェック ===")
    
    project_root = Path(__file__).parent.parent
    
    # README.md の確認
    readme_file = project_root / "README.md"
    if readme_file.exists():
        with open(readme_file, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        required_sections = [
            "## 機能",
            "## 必要要件", 
            "## インストール",
            "## 使用方法"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in readme_content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"⚠️  README.md に不足セクション: {missing_sections}")
        else:
            print("✓ README.md - 必要セクションあり")
    
    # definition.md の確認
    def_file = project_root / "definition.md"
    if def_file.exists():
        print("✓ definition.md - 存在")
    else:
        print("⚠️  definition.md が見つかりません")
    
    print("✅ ドキュメント確認完了")
    return True


def run_all_tests():
    """全テストの実行"""
    print("🔧 工数管理システム自動化ツール - 基本機能テスト")
    print("=" * 50)
    
    tests = [
        ("プロジェクト構造", test_project_structure),
        ("構文チェック", test_file_syntax),
        ("CSVテンプレート", test_csv_template),
        ("ドキュメント", test_documentation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}テスト中にエラー: {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 テスト結果サマリー")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 合格率: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
    
    if passed == len(results):
        print("🎉 全テストが成功しました！")
        print("\n次のステップ:")
        print("1. 仮想環境を作成し、requirements.txt からパッケージをインストール")
        print("2. Chrome をデバッグモードで起動")
        print("3. 工数管理システムにログインして入力画面まで遷移")
        print("4. python work_automation.py --help でヘルプを確認")
        return True
    else:
        print("⚠️  一部のテストが失敗しました。上記のエラーを確認してください。")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)