#!/usr/bin/env python3
"""終了時間調整機能のテストスクリプト"""
import sys
import tempfile
import os
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from classes.csv_processor import WorkDataCSVProcessor


def test_end_time_adjustment():
    """終了時間調整のテスト"""
    print("=== 終了時間調整機能のテスト ===")
    
    test_cases = [
        ("22:00", "22:00", "調整されない"),
        ("22:15", "22:15", "調整されない"),
        ("21:00", "21:00", "調整されない"),
        ("22:16", "22:00", "22:00に調整される"),
        ("23:00", "22:00", "22:00に調整される"),
        ("23:59", "22:00", "22:00に調整される"),
    ]
    
    for input_time, expected_time, description in test_cases:
        # テスト用CSVデータ作成
        csv_content = f"""日付,開始時刻,終了時刻,在宅/出社区分,休憩1_開始,休憩1_終了,プロジェクト1_時間,プロジェクト1_備考
2025-07-01,09:00,{input_time},在宅,12:00,13:00,7:00,テスト作業"""
        
        # 一時ファイル作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            # CSVプロセッサで処理
            processor = WorkDataCSVProcessor(temp_path)
            processor.load_csv_data()
            work_data_list = processor.get_all_data()
            
            # 結果確認
            actual_time = work_data_list[0]['end_time']
            status = "OK" if actual_time == expected_time else "NG"
            
            print(f"{status}: 入力: {input_time} → 出力: {actual_time} (期待値: {expected_time}) - {description}")
            
        finally:
            os.unlink(temp_path)
    
    print("\nテスト完了")


if __name__ == "__main__":
    test_end_time_adjustment()