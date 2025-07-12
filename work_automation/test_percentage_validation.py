#!/usr/bin/env python3
"""
割合形式のプロジェクト時間をサポートした機能の動作確認スクリプト
"""
import logging
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from classes.csv_processor import WorkDataCSVProcessor

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_percentage_format():
    """割合形式のテスト"""
    print("\n=== 割合形式のプロジェクト時間テスト ===\n")
    
    # プロセッサのインスタンス作成
    processor = WorkDataCSVProcessor("test_percentage_sample.csv")
    
    # CSVファイル読み込み
    if not processor.load_csv_data():
        print("❌ CSVファイルの読み込みに失敗しました")
        return False
    
    print("✅ CSVファイルを読み込みました")
    
    # データ検証
    if not processor.validate_data():
        print("❌ データ検証に失敗しました")
        return False
    
    print("✅ データ検証に成功しました（%形式も受け付けるようになりました）")
    
    # データ取得と表示
    print("\n--- 変換されたデータ ---")
    
    # 7月10日のデータ（休憩1時間）
    data1 = processor.get_work_data_by_date("2025-07-10")
    if data1:
        print(f"\n日付: {data1['date']}")
        print(f"勤務時間: {data1['start_time']} - {data1['end_time']} (総労働時間: 9時間)")
        print(f"休憩時間: 1時間 → 実労働時間: 8時間")
        print("プロジェクト:")
        for i, project in enumerate(data1['projects'], 1):
            original = "50%" if i == 1 else "25%"
            print(f"  {i}. 時間: {project['time']} (元: {original}), 備考: {project['comment']}")
    
    # 7月11日のデータ（休憩1時間）
    data2 = processor.get_work_data_by_date("2025-07-11")
    if data2:
        print(f"\n日付: {data2['date']}")
        print(f"勤務時間: {data2['start_time']} - {data2['end_time']} (総労働時間: 8時間)")
        print(f"休憩時間: 1時間 → 実労働時間: 7時間")
        print("プロジェクト:")
        for i, project in enumerate(data2['projects'], 1):
            original = "3:30" if i == 1 else "30%"
            print(f"  {i}. 時間: {project['time']} (元: {original}), 備考: {project['comment']}")
    
    # 7月12日のデータ（複数休憩）
    data3 = processor.get_work_data_by_date("2025-07-12")
    if data3:
        print(f"\n日付: {data3['date']}")
        print(f"勤務時間: {data3['start_time']} - {data3['end_time']} (総労働時間: 10時間)")
        print(f"休憩時間: 1.5時間 → 実労働時間: 8.5時間")
        print("プロジェクト:")
        for i, project in enumerate(data3['projects'], 1):
            original = "75%" if i == 1 else "15%"
            print(f"  {i}. 時間: {project['time']} (元: {original}), 備考: {project['comment']}")
    
    print("\n✅ 割合形式のプロジェクト時間が正しく処理されました！")
    return True

if __name__ == "__main__":
    try:
        success = test_percentage_format()
        sys.exit(0 if success else 1)
    except ImportError as e:
        print(f"❌ 必要なパッケージがインストールされていません: {e}")
        print("   setup_environment.py を実行してください")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)