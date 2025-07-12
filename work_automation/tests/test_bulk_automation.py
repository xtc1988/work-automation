#!/usr/bin/env python3
"""
BulkWorkAutomation クラスのテストコード
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from classes.bulk_automation import BulkWorkAutomation


class TestBulkWorkAutomation(unittest.TestCase):
    """BulkWorkAutomationクラスのテストクラス"""

    def setUp(self):
        """テストセットアップ"""
        # モックオブジェクトを作成
        self.mock_automation = Mock()
        self.mock_csv_processor = Mock()
        
        # BulkWorkAutomationのインスタンスを作成
        self.bulk_automation = BulkWorkAutomation(
            self.mock_automation,
            self.mock_csv_processor
        )

    def test_init(self):
        """初期化テスト"""
        self.assertEqual(self.bulk_automation.automation, self.mock_automation)
        self.assertEqual(self.bulk_automation.csv_processor, self.mock_csv_processor)
        self.assertEqual(self.bulk_automation.results, [])
        self.assertFalse(self.bulk_automation.auto_submit)
        self.assertEqual(self.bulk_automation.wait_between_days, 2)
        self.assertEqual(self.bulk_automation.max_retries, 3)

    def test_record_success(self):
        """成功記録テスト"""
        date = "2024/01/15"
        message = "提出完了"
        start_time = datetime.now()
        
        self.bulk_automation._record_success(date, message, start_time)
        
        self.assertEqual(len(self.bulk_automation.results), 1)
        result = self.bulk_automation.results[0]
        self.assertEqual(result['date'], date)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['message'], message)
        self.assertIn('processing_time', result)
        self.assertIn('timestamp', result)

    def test_record_failure(self):
        """失敗記録テスト"""
        date = "2024/01/15"
        message = "エラーが発生しました"
        
        self.bulk_automation._record_failure(date, message)
        
        self.assertEqual(len(self.bulk_automation.results), 1)
        result = self.bulk_automation.results[0]
        self.assertEqual(result['date'], date)
        self.assertEqual(result['status'], 'failure')
        self.assertEqual(result['message'], message)
        self.assertIn('timestamp', result)

    def test_get_failed_dates(self):
        """失敗した日付の取得テスト"""
        # テストデータを追加
        self.bulk_automation._record_success("2024/01/15", "成功", datetime.now())
        self.bulk_automation._record_failure("2024/01/16", "失敗1")
        self.bulk_automation._record_failure("2024/01/17", "失敗2")
        
        failed_dates = self.bulk_automation.get_failed_dates()
        
        self.assertEqual(len(failed_dates), 2)
        self.assertIn("2024/01/16", failed_dates)
        self.assertIn("2024/01/17", failed_dates)

    def test_process_single_day_success(self):
        """単日処理成功テスト"""
        work_data = {
            'date': '2024/01/15',
            'start_time': '09:00',
            'end_time': '18:00',
            'location_type': '在宅',
            'break_times': [('12:00', '13:00')],
            'projects': [{'time': '8:00', 'comment': 'プロジェクトA'}]
        }
        
        # モックの設定
        self.mock_automation.input_work_time.return_value = True
        self.mock_automation.input_break_time.return_value = True
        self.mock_automation.add_project_work.return_value = True
        self.mock_automation.calculate.return_value = True
        self.mock_automation.check_errors.return_value = []
        self.mock_automation.save_and_next.return_value = True
        self.mock_automation.verify_confirmation_data.return_value = {'date': '2024/01/15'}
        self.mock_automation.save_as_draft.return_value = True
        
        result = self.bulk_automation.process_single_day(work_data)
        
        self.assertTrue(result)
        self.assertEqual(len(self.bulk_automation.results), 1)
        self.assertEqual(self.bulk_automation.results[0]['status'], 'success')
        
        # メソッドが呼ばれたことを確認
        self.mock_automation.input_work_time.assert_called_once_with('09:00', '18:00', '在宅')
        self.mock_automation.input_break_time.assert_called_once_with([('12:00', '13:00')])
        self.mock_automation.add_project_work.assert_called_once_with(0, '8:00', 'プロジェクトA')
        self.mock_automation.calculate.assert_called_once()
        self.mock_automation.check_errors.assert_called_once()
        self.mock_automation.save_and_next.assert_called_once()
        self.mock_automation.verify_confirmation_data.assert_called_once()
        self.mock_automation.save_as_draft.assert_called_once()

    def test_process_single_day_failure(self):
        """単日処理失敗テスト"""
        work_data = {
            'date': '2024/01/15',
            'start_time': '09:00',
            'end_time': '18:00',
            'location_type': '在宅',
            'break_times': [],
            'projects': []
        }
        
        # モックの設定（勤務時間入力で失敗）
        self.mock_automation.input_work_time.return_value = False
        
        result = self.bulk_automation.process_single_day(work_data)
        
        self.assertFalse(result)
        self.assertEqual(len(self.bulk_automation.results), 1)
        self.assertEqual(self.bulk_automation.results[0]['status'], 'failure')
        self.assertIn('勤務時間入力に失敗', self.bulk_automation.results[0]['message'])

    def test_process_single_day_with_errors(self):
        """単日処理エラー検出テスト"""
        work_data = {
            'date': '2024/01/15',
            'start_time': '09:00',
            'end_time': '18:00',
            'location_type': '在宅',
            'break_times': [],
            'projects': []
        }
        
        # モックの設定（エラーが検出される）
        self.mock_automation.input_work_time.return_value = True
        self.mock_automation.calculate.return_value = True
        self.mock_automation.check_errors.return_value = ['エラー1', 'エラー2']
        
        result = self.bulk_automation.process_single_day(work_data)
        
        self.assertFalse(result)
        self.assertEqual(len(self.bulk_automation.results), 1)
        self.assertEqual(self.bulk_automation.results[0]['status'], 'failure')
        self.assertIn('エラー検出', self.bulk_automation.results[0]['message'])

    def test_process_single_day_auto_submit(self):
        """単日処理自動提出テスト"""
        work_data = {
            'date': '2024/01/15',
            'start_time': '09:00',
            'end_time': '18:00',
            'location_type': '在宅',
            'break_times': [],
            'projects': []
        }
        
        # 自動提出フラグを設定
        self.bulk_automation.auto_submit = True
        
        # モックの設定
        self.mock_automation.input_work_time.return_value = True
        self.mock_automation.calculate.return_value = True
        self.mock_automation.check_errors.return_value = []
        self.mock_automation.save_and_next.return_value = True
        self.mock_automation.verify_confirmation_data.return_value = {'date': '2024/01/15'}
        self.mock_automation.confirm_and_submit.return_value = True
        
        result = self.bulk_automation.process_single_day(work_data)
        
        self.assertTrue(result)
        self.mock_automation.confirm_and_submit.assert_called_once()
        self.assertEqual(self.bulk_automation.results[0]['message'], '提出完了')

    @patch('classes.bulk_automation.time.sleep')
    def test_process_all_data_success(self, mock_sleep):
        """全データ処理成功テスト"""
        test_data = [
            {
                'date': '2024/01/15',
                'start_time': '09:00',
                'end_time': '18:00',
                'location_type': '在宅',
                'break_times': [],
                'projects': []
            },
            {
                'date': '2024/01/16',
                'start_time': '09:00',
                'end_time': '18:00',
                'location_type': '在宅',
                'break_times': [],
                'projects': []
            }
        ]
        
        self.mock_csv_processor.get_all_data.return_value = test_data
        
        # process_single_day をモック
        with patch.object(self.bulk_automation, 'process_single_day') as mock_process:
            mock_process.return_value = True
            
            result = self.bulk_automation.process_all_data()
            
            self.assertTrue(result)
            self.assertEqual(mock_process.call_count, 2)
            self.mock_automation.navigate_to_next_day.assert_called_once()

    def test_process_all_data_dry_run(self):
        """全データ処理ドライランテスト"""
        test_data = [
            {
                'date': '2024/01/15',
                'start_time': '09:00',
                'end_time': '18:00',
                'location_type': '在宅',
                'break_times': [],
                'projects': []
            }
        ]
        
        self.mock_csv_processor.get_all_data.return_value = test_data
        
        result = self.bulk_automation.process_all_data(dry_run=True)
        
        self.assertTrue(result)
        self.assertEqual(len(self.bulk_automation.results), 1)
        self.assertEqual(self.bulk_automation.results[0]['status'], 'dry_run')

    def test_process_all_data_no_data(self):
        """全データ処理データなしテスト"""
        self.mock_csv_processor.get_all_data.return_value = []
        
        result = self.bulk_automation.process_all_data()
        
        self.assertFalse(result)

    def test_retry_failed_dates(self):
        """失敗した日付のリトライテスト"""
        # 失敗データを追加
        self.bulk_automation._record_failure("2024/01/15", "失敗")
        self.bulk_automation._record_failure("2024/01/16", "失敗")
        
        # モックの設定
        work_data = {
            'date': '2024/01/15',
            'start_time': '09:00',
            'end_time': '18:00',
            'location_type': '在宅',
            'break_times': [],
            'projects': []
        }
        
        self.mock_csv_processor.get_work_data_by_date.return_value = work_data
        
        # process_single_day をモック
        with patch.object(self.bulk_automation, 'process_single_day') as mock_process:
            mock_process.return_value = True
            
            result = self.bulk_automation.retry_failed_dates()
            
            self.assertTrue(result)
            self.assertEqual(mock_process.call_count, 2)

    def test_retry_failed_dates_no_failures(self):
        """失敗した日付のリトライテスト - 失敗なし"""
        result = self.bulk_automation.retry_failed_dates()
        
        self.assertTrue(result)

    @patch('classes.bulk_automation.csv.DictWriter')
    @patch('builtins.open')
    def test_save_results_to_csv(self, mock_open, mock_csv_writer):
        """結果のCSV保存テスト"""
        # テストデータを追加
        self.bulk_automation._record_success("2024/01/15", "成功", datetime.now())
        self.bulk_automation._record_failure("2024/01/16", "失敗")
        
        # モックの設定
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_writer = Mock()
        mock_csv_writer.return_value = mock_writer
        
        result = self.bulk_automation.save_results_to_csv()
        
        self.assertTrue(result.endswith('.csv'))
        mock_open.assert_called_once()
        mock_writer.writeheader.assert_called_once()
        self.assertEqual(mock_writer.writerow.call_count, 2)

    def test_show_results_summary_no_results(self):
        """結果サマリー表示テスト - 結果なし"""
        with patch('builtins.print') as mock_print:
            self.bulk_automation.show_results_summary()
            mock_print.assert_called_with("処理結果がありません")

    def test_show_results_summary_with_results(self):
        """結果サマリー表示テスト - 結果あり"""
        # テストデータを追加
        self.bulk_automation._record_success("2024/01/15", "成功", datetime.now())
        self.bulk_automation._record_failure("2024/01/16", "失敗")
        
        with patch('builtins.print') as mock_print:
            self.bulk_automation.show_results_summary()
            
            # print が呼ばれたことを確認
            mock_print.assert_called()
            
            # 特定の出力内容を確認
            call_args = [str(call) for call in mock_print.call_args_list]
            summary_output = '\n'.join(call_args)
            self.assertIn('総処理件数: 2件', summary_output)
            self.assertIn('成功: 1件', summary_output)
            self.assertIn('失敗: 1件', summary_output)


if __name__ == '__main__':
    # テストの実行
    unittest.main(verbosity=2)