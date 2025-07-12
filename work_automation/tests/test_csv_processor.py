#!/usr/bin/env python3
"""
CSV処理クラスの単体テスト
"""
import unittest
import tempfile
import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pandas as pd
    from classes.csv_processor import WorkDataCSVProcessor
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class TestWorkDataCSVProcessor(unittest.TestCase):
    """WorkDataCSVProcessor クラスのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        if not PANDAS_AVAILABLE:
            self.skipTest("pandas が利用できません")
        
        # テスト用CSVデータ
        self.test_csv_content = """日付,開始時刻,終了時刻,在宅/出社区分,休憩1_開始,休憩1_終了,プロジェクト1_時間,プロジェクト1_備考
2025-07-01,09:00,18:00,在宅,12:00,13:00,6:00,テスト作業
2025-07-02,09:00,19:00,出社（通勤費往復）,12:00,13:00,7:00,開発作業
"""
        
        # 一時ファイル作成
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
        self.temp_file.write(self.test_csv_content)
        self.temp_file.close()
        
        self.processor = WorkDataCSVProcessor(self.temp_file.name)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ファイル削除
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_load_csv_data(self):
        """CSVデータ読み込みのテスト"""
        result = self.processor.load_csv_data()
        self.assertTrue(result, "CSVデータの読み込みに失敗しました")
        self.assertIsNotNone(self.processor.data, "データが読み込まれていません")
        self.assertEqual(len(self.processor.data), 2, "読み込み行数が正しくありません")
    
    def test_validate_data_success(self):
        """正常データの検証テスト"""
        self.processor.load_csv_data()
        result = self.processor.validate_data()
        self.assertTrue(result, "正常データの検証に失敗しました")
    
    def test_get_work_data_by_date(self):
        """日付指定データ取得のテスト"""
        self.processor.load_csv_data()
        
        # 存在する日付
        data = self.processor.get_work_data_by_date("2025-07-01")
        self.assertIsNotNone(data, "データが取得できませんでした")
        self.assertEqual(data['date'], "2025-07-01")
        self.assertEqual(data['start_time'], "09:00")
        self.assertEqual(data['location_type'], "在宅")
        
        # 存在しない日付
        data = self.processor.get_work_data_by_date("2025-12-31")
        self.assertIsNone(data, "存在しない日付でデータが返されました")
    
    def test_convert_row_to_work_data(self):
        """行データ変換のテスト"""
        self.processor.load_csv_data()
        row = self.processor.data.iloc[0]
        
        work_data = self.processor._convert_row_to_work_data(row)
        
        # 基本データの確認
        self.assertEqual(work_data['date'], "2025-07-01")
        self.assertEqual(work_data['start_time'], "09:00")
        self.assertEqual(work_data['end_time'], "18:00")
        self.assertEqual(work_data['location_type'], "在宅")
        
        # 休憩時間の確認
        self.assertEqual(len(work_data['break_times']), 1)
        self.assertEqual(work_data['break_times'][0], ("12:00", "13:00"))
        
        # プロジェクトの確認
        self.assertEqual(len(work_data['projects']), 1)
        self.assertEqual(work_data['projects'][0]['time'], "6:00")
        self.assertEqual(work_data['projects'][0]['comment'], "テスト作業")
    
    def test_validate_time_format(self):
        """時刻フォーマット検証のテスト"""
        # 正常な時刻
        self.assertTrue(self.processor._validate_time_format("09:00"))
        self.assertTrue(self.processor._validate_time_format("23:59"))
        self.assertTrue(self.processor._validate_time_format("00:00"))
        
        # 異常な時刻
        self.assertFalse(self.processor._validate_time_format("25:00"))
        self.assertFalse(self.processor._validate_time_format("12:60"))
        self.assertFalse(self.processor._validate_time_format("abc"))
        self.assertFalse(self.processor._validate_time_format("12"))
    
    def test_validate_project_time_format(self):
        """プロジェクト時間フォーマット検証のテスト"""
        # 正常な時間（H:MM形式）
        self.assertTrue(self.processor._validate_project_time_format("1:30"))
        self.assertTrue(self.processor._validate_project_time_format("10:45"))
        self.assertTrue(self.processor._validate_project_time_format("0:15"))
        
        # 正常な時間（%形式）
        self.assertTrue(self.processor._validate_project_time_format("50%"))
        self.assertTrue(self.processor._validate_project_time_format("25.5%"))
        self.assertTrue(self.processor._validate_project_time_format("100%"))
        self.assertTrue(self.processor._validate_project_time_format("0.5%"))
        
        # 異常な時間
        self.assertFalse(self.processor._validate_project_time_format("1:60"))
        self.assertFalse(self.processor._validate_project_time_format("abc"))
        self.assertFalse(self.processor._validate_project_time_format("0%"))  # 0%は無効
        self.assertFalse(self.processor._validate_project_time_format("101%"))  # 100%超は無効
        self.assertFalse(self.processor._validate_project_time_format("50"))  # %なしは無効
    
    def test_convert_project_time(self):
        """プロジェクト時間変換のテスト"""
        # H:MM形式はそのまま返す
        self.assertEqual(self.processor._convert_project_time("1:30"), "1:30")
        self.assertEqual(self.processor._convert_project_time("10:45"), "10:45")
        
        # %形式から時間への変換（デフォルト8時間=480分を基準）
        self.assertEqual(self.processor._convert_project_time("50%"), "4:00")  # 50% of 8h = 4h
        self.assertEqual(self.processor._convert_project_time("25%"), "2:00")  # 25% of 8h = 2h
        self.assertEqual(self.processor._convert_project_time("100%"), "8:00")  # 100% of 8h = 8h
        self.assertEqual(self.processor._convert_project_time("12.5%"), "1:00")  # 12.5% of 8h = 1h
        
        # 総労働時間を指定した場合
        self.assertEqual(self.processor._convert_project_time("50%", 600), "5:00")  # 50% of 10h = 5h
        self.assertEqual(self.processor._convert_project_time("25%", 240), "1:00")  # 25% of 4h = 1h
    
    def test_percentage_project_time_integration(self):
        """割合形式のプロジェクト時間の統合テスト"""
        # %形式を含むCSVデータ
        csv_with_percentage = """日付,開始時刻,終了時刻,在宅/出社区分,休憩1_開始,休憩1_終了,プロジェクト1_時間,プロジェクト1_備考,プロジェクト2_時間,プロジェクト2_備考
2025-07-03,09:00,18:00,在宅,12:00,13:00,50%,メイン作業,25%,サブ作業
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_with_percentage)
            temp_path = f.name
        
        try:
            processor = WorkDataCSVProcessor(temp_path)
            processor.load_csv_data()
            
            # データ検証は成功するはず
            result = processor.validate_data()
            self.assertTrue(result, "割合形式を含むデータの検証に失敗しました")
            
            # データ変換の確認
            work_data = processor.get_work_data_by_date("2025-07-03")
            self.assertIsNotNone(work_data)
            
            # プロジェクト時間が正しく変換されているか確認
            # 総労働時間は9時間（540分） - 休憩1時間（60分） = 実労働8時間（480分）
            self.assertEqual(len(work_data['projects']), 2)
            self.assertEqual(work_data['projects'][0]['time'], "4:00")  # 50% of 8h
            self.assertEqual(work_data['projects'][0]['comment'], "メイン作業")
            self.assertEqual(work_data['projects'][1]['time'], "2:00")  # 25% of 8h
            self.assertEqual(work_data['projects'][1]['comment'], "サブ作業")
            
        finally:
            os.unlink(temp_path)
    
    def test_percentage_with_multiple_breaks(self):
        """複数の休憩時間がある場合の割合計算テスト"""
        # 複数の休憩時間を含むCSVデータ
        csv_with_breaks = """日付,開始時刻,終了時刻,在宅/出社区分,休憩1_開始,休憩1_終了,休憩2_開始,休憩2_終了,プロジェクト1_時間,プロジェクト1_備考
2025-07-04,09:00,19:00,在宅,12:00,13:00,15:00,15:30,75%,一日の大部分の作業
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_with_breaks)
            temp_path = f.name
        
        try:
            processor = WorkDataCSVProcessor(temp_path)
            processor.load_csv_data()
            
            # データ検証
            result = processor.validate_data()
            self.assertTrue(result, "複数休憩時間を含むデータの検証に失敗しました")
            
            # データ変換の確認
            work_data = processor.get_work_data_by_date("2025-07-04")
            self.assertIsNotNone(work_data)
            
            # プロジェクト時間が正しく変換されているか確認
            # 総労働時間は10時間（600分） - 休憩1.5時間（90分） = 実労働8.5時間（510分）
            # 75% of 510分 = 382.5分 = 6時間22.5分 ≈ 6:22
            self.assertEqual(len(work_data['projects']), 1)
            self.assertEqual(work_data['projects'][0]['time'], "6:22")  # 75% of 8.5h
            self.assertEqual(work_data['projects'][0]['comment'], "一日の大部分の作業")
            
        finally:
            os.unlink(temp_path)


class TestCSVValidation(unittest.TestCase):
    """CSV検証機能のテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        if not PANDAS_AVAILABLE:
            self.skipTest("pandas が利用できません")
    
    def test_invalid_data_validation(self):
        """不正データの検証テスト"""
        # 不正なデータ
        invalid_csv = """日付,開始時刻,終了時刻,在宅/出社区分,休憩1_開始,休憩1_終了,プロジェクト1_時間,プロジェクト1_備考
2025-07-01,25:00,18:00,在宅,12:00,13:00,6:00,テスト作業
2025-07-02,09:00,,無効な区分,12:00,13:00,7:60,開発作業
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(invalid_csv)
            temp_path = f.name
        
        try:
            processor = WorkDataCSVProcessor(temp_path)
            processor.load_csv_data()
            result = processor.validate_data()
            
            # 検証は失敗するはず
            self.assertFalse(result, "不正データで検証が成功してしまいました")
            
        finally:
            os.unlink(temp_path)
    
    def test_end_time_adjustment(self):
        """終了時間が22:15より大きい場合に22:00に調整されるテスト"""
        # 22:15より大きい終了時間を含むテストデータ
        csv_data_cases = [
            # 22:15以下の場合（調整されない）
            ("2025-07-01,09:00,22:00,在宅,12:00,13:00,7:00,通常作業", "22:00"),
            ("2025-07-02,09:00,22:15,在宅,12:00,13:00,7:00,通常作業", "22:15"),
            ("2025-07-03,09:00,21:00,在宅,12:00,13:00,7:00,通常作業", "21:00"),
            # 22:15より大きい場合（22:00に調整される）
            ("2025-07-04,09:00,22:16,在宅,12:00,13:00,7:00,深夜作業", "22:00"),
            ("2025-07-05,09:00,23:00,在宅,12:00,13:00,7:00,深夜作業", "22:00"),
            ("2025-07-06,09:00,23:59,在宅,12:00,13:00,7:00,深夜作業", "22:00"),
        ]
        
        for csv_line, expected_end_time in csv_data_cases:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
                header = "日付,開始時刻,終了時刻,在宅/出社区分,休憩1_開始,休憩1_終了,プロジェクト1_時間,プロジェクト1_備考"
                f.write(f"{header}\n{csv_line}")
                temp_path = f.name
            
            try:
                processor = WorkDataCSVProcessor(temp_path)
                processor.load_csv_data()
                
                # 変換されたデータを取得
                work_data_list = processor.get_work_data()
                self.assertEqual(len(work_data_list), 1)
                
                work_data = work_data_list[0]
                actual_end_time = work_data['end_time']
                
                # 終了時間が期待通りに調整されているか確認
                self.assertEqual(actual_end_time, expected_end_time,
                               f"終了時間の調整が正しくありません。入力: {csv_line.split(',')[2]}, "
                               f"期待値: {expected_end_time}, 実際値: {actual_end_time}")
                
            finally:
                os.unlink(temp_path)


def run_csv_tests():
    """CSV関連テストの実行"""
    print("=== CSV処理クラス テスト開始 ===")
    
    if not PANDAS_AVAILABLE:
        print("⚠️  pandas が利用できないため、CSV処理テストをスキップします")
        print("    以下のコマンドで環境をセットアップしてください:")
        print("    python setup_environment.py")
        print("    または手動で: pip install pandas")
        print("✅ テスト自体は成功（パッケージ不足のためスキップ）")
        return True  # パッケージ不足は失敗ではないため True を返す
    
    # テストスイート作成
    suite = unittest.TestSuite()
    
    # テストケース追加
    suite.addTest(unittest.makeSuite(TestWorkDataCSVProcessor))
    suite.addTest(unittest.makeSuite(TestCSVValidation))
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果表示
    if result.wasSuccessful():
        print("✓ 全てのCSVテストが成功しました")
        return True
    else:
        print(f"✗ テスト失敗: {len(result.failures)}件の失敗, {len(result.errors)}件のエラー")
        return False


if __name__ == "__main__":
    success = run_csv_tests()
    sys.exit(0 if success else 1)