#!/usr/bin/env python3
"""
WorkTimeAutomation クラスのテストコード
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from classes.work_time_automation import WorkTimeAutomation


class TestWorkTimeAutomation(unittest.TestCase):
    """WorkTimeAutomationクラスのテストクラス"""

    def setUp(self):
        """テストセットアップ"""
        # モックドライバーを作成
        self.mock_driver = Mock()
        self.mock_wait = Mock()
        
        # WorkTimeAutomationのインスタンスを作成（モック使用）
        with patch('classes.work_time_automation.webdriver.Chrome') as mock_chrome:
            mock_chrome.return_value = self.mock_driver
            with patch('classes.work_time_automation.WebDriverWait') as mock_webdriverwait:
                mock_webdriverwait.return_value = self.mock_wait
                self.automation = WorkTimeAutomation()
                self.automation.driver = self.mock_driver
                self.automation.wait = self.mock_wait

    def test_is_date_string_valid_formats(self):
        """日付文字列の判定テスト - 有効な形式"""
        test_cases = [
            "2024/01/15",
            "2024-01-15",
            "2024年1月15日",
            "1月15日",
            "01/15/2024",
            "01-15-2024"
        ]
        
        for date_str in test_cases:
            with self.subTest(date_str=date_str):
                result = self.automation._is_date_string(date_str)
                self.assertTrue(result, f"日付文字列として認識されるべき: {date_str}")

    def test_is_date_string_invalid_formats(self):
        """日付文字列の判定テスト - 無効な形式"""
        test_cases = [
            "テスト",
            "abc123",
            "2024/13/01",  # 無効な月
            "時刻: 09:00",
            "合計時間"
        ]
        
        for date_str in test_cases:
            with self.subTest(date_str=date_str):
                result = self.automation._is_date_string(date_str)
                self.assertFalse(result, f"日付文字列として認識されるべきでない: {date_str}")

    def test_get_next_business_date_weekday(self):
        """次の営業日計算テスト - 平日"""
        # 2024/01/15（月曜日）の場合
        current_date = "2024/01/15"
        expected = "2024/01/16"
        
        result = self.automation._get_next_business_date(current_date)
        self.assertEqual(result, expected)

    def test_get_next_business_date_friday(self):
        """次の営業日計算テスト - 金曜日（土日をスキップ）"""
        # 2024/01/19（金曜日）の場合
        current_date = "2024/01/19"
        expected = "2024/01/22"  # 月曜日
        
        result = self.automation._get_next_business_date(current_date)
        self.assertEqual(result, expected)

    def test_get_next_business_date_saturday(self):
        """次の営業日計算テスト - 土曜日"""
        # 2024/01/20（土曜日）の場合
        current_date = "2024/01/20"
        expected = "2024/01/22"  # 月曜日
        
        result = self.automation._get_next_business_date(current_date)
        self.assertEqual(result, expected)

    def test_should_skip_weekends_true(self):
        """土日スキップ判定テスト - スキップが必要な場合"""
        current_date = "2024/01/19"  # 金曜日
        next_business_date = "2024/01/22"  # 月曜日
        
        result = self.automation._should_skip_weekends(current_date, next_business_date)
        self.assertTrue(result)

    def test_should_skip_weekends_false(self):
        """土日スキップ判定テスト - スキップが不要な場合"""
        current_date = "2024/01/15"  # 月曜日
        next_business_date = "2024/01/16"  # 火曜日
        
        result = self.automation._should_skip_weekends(current_date, next_business_date)
        self.assertFalse(result)

    def test_verify_element_interactable_valid(self):
        """要素の操作可能性テスト - 有効な要素"""
        # モック要素を作成
        mock_element = Mock()
        mock_element.is_displayed.return_value = True
        mock_element.is_enabled.return_value = True
        mock_element.size = {'width': 100, 'height': 20}
        mock_element.location = {'x': 10, 'y': 10}
        mock_element.value_of_css_property.side_effect = lambda prop: {
            'visibility': 'visible',
            'display': 'block',
            'opacity': '1'
        }.get(prop, '')
        
        result = self.automation._verify_element_interactable(mock_element)
        self.assertTrue(result)

    def test_verify_element_interactable_hidden(self):
        """要素の操作可能性テスト - 非表示の要素"""
        # モック要素を作成
        mock_element = Mock()
        mock_element.is_displayed.return_value = False
        mock_element.is_enabled.return_value = True
        
        result = self.automation._verify_element_interactable(mock_element)
        self.assertFalse(result)

    def test_verify_element_interactable_disabled(self):
        """要素の操作可能性テスト - 無効な要素"""
        # モック要素を作成
        mock_element = Mock()
        mock_element.is_displayed.return_value = True
        mock_element.is_enabled.return_value = False
        
        result = self.automation._verify_element_interactable(mock_element)
        self.assertFalse(result)

    def test_safe_click_normal(self):
        """安全なクリックテスト - 通常のクリック"""
        mock_element = Mock()
        
        result = self.automation._safe_click(mock_element)
        
        self.assertTrue(result)
        mock_element.click.assert_called_once()

    def test_safe_click_with_exception(self):
        """安全なクリックテスト - 例外発生時"""
        from selenium.common.exceptions import ElementNotInteractableException
        
        mock_element = Mock()
        mock_element.click.side_effect = ElementNotInteractableException("Element not interactable")
        
        # ActionChainsのモック
        with patch('classes.work_time_automation.ActionChains') as mock_action_chains:
            mock_action = Mock()
            mock_action_chains.return_value = mock_action
            mock_action.move_to_element.return_value = mock_action
            mock_action.click.return_value = mock_action
            
            result = self.automation._safe_click(mock_element)
            
            self.assertTrue(result)
            mock_action.perform.assert_called_once()

    @patch('classes.work_time_automation.time.sleep')
    def test_wait_for_page_load(self, mock_sleep):
        """ページ読み込み待機テスト"""
        # document.readyState が 'complete' を返すようにモック
        self.mock_driver.execute_script.return_value = "complete"
        
        # WebDriverWaitのモック
        with patch('classes.work_time_automation.WebDriverWait') as mock_webdriver_wait:
            mock_wait_instance = Mock()
            mock_webdriver_wait.return_value = mock_wait_instance
            
            # テスト実行
            self.automation.wait_for_page_load()
            
            # WebDriverWaitが呼ばれたことを確認
            mock_webdriver_wait.assert_called()

    def test_search_by_xpath_found(self):
        """XPath検索テスト - 要素が見つかった場合"""
        field_name = "KNMTMRNGSTDI"
        mock_element = Mock()
        mock_element.is_displayed.return_value = True
        mock_element.is_enabled.return_value = True
        
        self.mock_driver.find_elements.return_value = [mock_element]
        
        result = self.automation._search_by_xpath(field_name)
        
        self.assertEqual(result, mock_element)

    def test_search_by_xpath_not_found(self):
        """XPath検索テスト - 要素が見つからない場合"""
        field_name = "NONEXISTENT"
        self.mock_driver.find_elements.return_value = []
        
        result = self.automation._search_by_xpath(field_name)
        
        self.assertIsNone(result)


class TestWorkTimeAutomationIntegration(unittest.TestCase):
    """WorkTimeAutomationの統合テストクラス"""

    def setUp(self):
        """統合テストセットアップ"""
        # 実際のブラウザは使用せず、モックで統合テストを行う
        self.mock_driver = Mock()
        self.mock_wait = Mock()

    def test_input_work_time_flow(self):
        """勤務時間入力フローの統合テスト"""
        with patch('classes.work_time_automation.webdriver.Chrome') as mock_chrome:
            mock_chrome.return_value = self.mock_driver
            with patch('classes.work_time_automation.WebDriverWait') as mock_webdriverwait:
                mock_webdriverwait.return_value = self.mock_wait
                
                automation = WorkTimeAutomation()
                automation.driver = self.mock_driver
                automation.wait = self.mock_wait
                
                # モック要素を設定
                mock_element = Mock()
                mock_element.is_displayed.return_value = True
                mock_element.is_enabled.return_value = True
                mock_element.size = {'width': 100, 'height': 20}
                mock_element.location = {'x': 10, 'y': 10}
                mock_element.get_attribute.return_value = "09:00"
                
                # wait_for_element_stable をモック
                with patch.object(automation, 'wait_for_element_stable') as mock_wait_stable:
                    mock_wait_stable.return_value = mock_element
                    
                    # wait_for_page_load をモック
                    with patch.object(automation, 'wait_for_page_load'):
                        # _verify_element_interactable をモック
                        with patch.object(automation, '_verify_element_interactable') as mock_verify:
                            mock_verify.return_value = True
                            
                            # _safe_click をモック
                            with patch.object(automation, '_safe_click') as mock_safe_click:
                                mock_safe_click.return_value = True
                                
                                # セレクトボックスの設定
                                with patch('classes.work_time_automation.Select') as mock_select:
                                    mock_select_instance = Mock()
                                    mock_select.return_value = mock_select_instance
                                    
                                    # テスト実行
                                    result = automation.input_work_time("09:00", "18:00", "在宅")
                                    
                                    # 結果の確認
                                    self.assertTrue(result)
                                    mock_wait_stable.assert_called()
                                    mock_verify.assert_called()
                                    mock_safe_click.assert_called()


if __name__ == '__main__':
    # テストの実行
    unittest.main(verbosity=2)