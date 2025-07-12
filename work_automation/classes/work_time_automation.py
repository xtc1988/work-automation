"""
工数管理システム基本自動化クラス
"""
import time
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException


class WorkTimeAutomation:
    """工数管理システムの自動化を行うクラス"""
    
    def __init__(self, user_data_dir: Optional[str] = None, profile_directory: Optional[str] = None):
        """
        既存のChromeブラウザに接続するための初期化
        
        Args:
            user_data_dir: Chromeのユーザーデータディレクトリ
            profile_directory: 使用するプロファイル名（デフォルトは"Default"）
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        chrome_options = Options()
        
        if user_data_dir:
            # 既存のChromeプロファイルを使用
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            if profile_directory:
                chrome_options.add_argument(f"--profile-directory={profile_directory}")
        else:
            # デバッグモードでChromeに接続（推奨）
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            # 待機時間を延長（従来の10秒から20秒へ）
            self.wait = WebDriverWait(self.driver, 20)
            # より短い待機時間（アクション間の待機用）
            self.short_wait = WebDriverWait(self.driver, 5)
            self.logger.info("Chromeブラウザに接続しました")
            
            # スクリーンショット保存用ディレクトリ
            self.screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "screenshots")
            os.makedirs(self.screenshot_dir, exist_ok=True)
            
        except Exception as e:
            self.logger.error(f"Chrome接続エラー: {e}")
            raise
        
    @classmethod
    def connect_to_existing_chrome(cls):
        """
        デバッグモードで起動済みのChromeに接続
        
        事前にChromeを以下のコマンドで起動しておく:
        chrome.exe --remote-debugging-port=9222 --user-data-dir="C:/temp/chrome_dev"
        """
        return cls()
    
    def get_current_date(self) -> str:
        """現在表示されている日付を取得（改善版）"""
        try:
            # 複数の方法で日付要素を検索
            date_element = None
            
            # 方法1: 既知のCSS Selector
            try:
                date_element = self.driver.find_element(By.CSS_SELECTOR, "#srw_page_navi_date span")
            except NoSuchElementException:
                pass
            
            # 方法2: XPathを使用した検索
            if not date_element:
                xpath_patterns = [
                    "//span[contains(@id, 'date')]",
                    "//span[contains(@class, 'date')]",
                    "//div[contains(@class, 'date')]//span",
                    "//span[contains(text(), '/')]",
                    "//span[contains(text(), '-')]",
                    "//span[contains(text(), '年')]",
                    "//span[contains(text(), '月')]"
                ]
                
                for pattern in xpath_patterns:
                    try:
                        elements = self.driver.find_elements(By.XPATH, pattern)
                        for element in elements:
                            text = element.text.strip()
                            if self._is_date_string(text):
                                date_element = element
                                break
                        if date_element:
                            break
                    except:
                        continue
            
            if date_element:
                date_text = date_element.text.strip()
                self.logger.debug(f"現在の日付: {date_text}")
                return date_text
            else:
                self.logger.warning("日付要素が見つかりません")
                return ""
                
        except Exception as e:
            self.logger.error(f"日付取得エラー: {e}")
            return ""
    
    def _is_date_string(self, text: str) -> bool:
        """文字列が日付かどうかを判定"""
        import re
        # 日付のパターンを定義
        date_patterns = [
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD または YYYY-MM-DD
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',  # MM/DD/YYYY または MM-DD-YYYY
            r'\d{4}年\d{1,2}月\d{1,2}日',     # YYYY年MM月DD日
            r'\d{1,2}月\d{1,2}日'             # MM月DD日
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text):
                return True
        return False

    def _is_weekend_or_holiday(self, date_str: str = None) -> bool:
        """現在または指定日付が土日・祝日かどうかを判定（修正版）"""
        try:
            from datetime import datetime
            import re
            
            if not date_str:
                date_str = self.get_current_date()
            
            if not date_str:
                self.logger.debug("日付文字列が取得できないため、平日として判定")
                return False
            
            self.logger.info(f"土日判定開始: 対象日付='{date_str}'")
            
            # 曜日情報が含まれている場合の直接判定
            if '(土)' in date_str or '(日)' in date_str:
                self.logger.info(f"曜日文字で土日判定: {date_str} -> 土日=True")
                return True
            elif '(月)' in date_str or '(火)' in date_str or '(水)' in date_str or '(木)' in date_str or '(金)' in date_str:
                self.logger.info(f"曜日文字で平日判定: {date_str} -> 土日=False")
                return False
            
            # 日付をパースして曜日を判定
            date_obj = None
            
            # 数値部分のみを抽出
            numbers = re.findall(r'\d+', date_str)
            self.logger.debug(f"抽出した数値: {numbers}")
            
            if len(numbers) >= 3:
                try:
                    # YYYY年MM月DD日 形式を想定
                    year = int(numbers[0])
                    month = int(numbers[1])
                    day = int(numbers[2])
                    
                    # 年が2桁の場合は20xxに変換
                    if year < 100:
                        year += 2000
                    
                    date_obj = datetime(year, month, day)
                    self.logger.debug(f"日付オブジェクト作成成功: {date_obj}")
                    
                except ValueError as e:
                    self.logger.debug(f"日付オブジェクト作成失敗: {e}")
                    pass
            
            if date_obj:
                weekday = date_obj.weekday()  # 0=月曜, 6=日曜
                weekday_names = ['月', '火', '水', '木', '金', '土', '日']
                is_weekend = weekday >= 5  # 土曜(5)、日曜(6)
                
                self.logger.info(f"日付解析結果: {date_str} -> {year}/{month}/{day}({weekday_names[weekday]}) -> 土日={is_weekend}")
                return is_weekend
            
            self.logger.info(f"日付解析失敗のため平日として判定: {date_str}")
            return False
            
        except Exception as e:
            self.logger.error(f"土日判定エラー: {e}")
            return False

    def _detect_available_time_fields(self) -> dict:
        """利用可能な時間入力フィールドを動的に検出"""
        try:
            self.logger.info("利用可能な時間フィールドを検出中...")
            
            available_fields = {
                'start_time': [],
                'end_time': [],
                'other_time': []
            }
            
            # 時間関連の要素パターンを検索
            time_patterns = [
                # 基本パターン
                "//input[contains(@name, 'KNMTM')]",
                "//input[contains(@name, 'time')]",
                "//input[contains(@name, 'TIME')]",
                "//input[contains(@name, '時')]",
                "//input[contains(@name, '開始')]",
                "//input[contains(@name, '終了')]",
                "//input[contains(@name, 'start')]",
                "//input[contains(@name, 'end')]",
                "//input[contains(@name, 'ST')]",
                "//input[contains(@name, 'ET')]",
                
                # 工数システム特有パターン
                "//input[contains(@name, 'RNG')]",
                "//input[contains(@name, 'DI')]",
                "//input[contains(@class, 'time')]",
                "//input[contains(@class, 'direct-time')]",
                "//input[@type='time']",
                
                # より広範囲の検索
                "//input[contains(@placeholder, '時')]",
                "//input[contains(@placeholder, ':')]",
                "//input[contains(@title, '時刻')]",
            ]
            
            for pattern in time_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            field_info = {
                                'element': element,
                                'name': element.get_attribute('name'),
                                'id': element.get_attribute('id'),
                                'class': element.get_attribute('class'),
                                'placeholder': element.get_attribute('placeholder'),
                                'type': element.get_attribute('type')
                            }
                            
                            # フィールドの種類を推定
                            name = field_info['name'] or ''
                            if any(x in name.upper() for x in ['START', 'ST', '開始', 'BEGIN']):
                                available_fields['start_time'].append(field_info)
                            elif any(x in name.upper() for x in ['END', 'ET', '終了', 'FINISH']):
                                available_fields['end_time'].append(field_info)
                            else:
                                available_fields['other_time'].append(field_info)
                                
                except Exception as e:
                    self.logger.debug(f"パターン検索エラー: {pattern} - {e}")
                    continue
            
            # 検出結果をログ出力
            for field_type, fields in available_fields.items():
                self.logger.info(f"{field_type}: {len(fields)}個検出")
                for field in fields:
                    self.logger.debug(f"  - name='{field['name']}', id='{field['id']}'")
            
            return available_fields
            
        except Exception as e:
            self.logger.error(f"時間フィールド検出エラー: {e}")
            return {'start_time': [], 'end_time': [], 'other_time': []}

    def _get_weekend_alternative_fields(self) -> dict:
        """土日用の代替フィールドパターンを取得"""
        try:
            self.logger.info("土日用代替フィールドを検索中...")
            
            # 土日では異なるフィールド名が使用される可能性のパターン
            weekend_patterns = [
                # 土日専用フィールド
                "//input[contains(@name, 'WEEKEND')]",
                "//input[contains(@name, 'HOLIDAY')]",
                "//input[contains(@name, 'REST')]",
                "//input[contains(@name, '休日')]",
                "//input[contains(@name, '非稼働')]",
                
                # 簡略化されたフィールド
                "//input[contains(@name, 'WK')]",
                "//input[contains(@name, 'HD')]",
                
                # ダミーフィールド以外のテキスト入力
                "//input[@type='text' and not(contains(@name, 'dummy'))]",
                "//input[@type='time' and not(contains(@name, 'dummy'))]",
                
                # 非表示だが存在するフィールド
                "//input[contains(@name, 'KNM') and not(@style*='display:none')]",
            ]
            
            alternative_fields = []
            
            for pattern in weekend_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        try:
                            field_info = {
                                'element': element,
                                'name': element.get_attribute('name'),
                                'id': element.get_attribute('id'),
                                'visible': element.is_displayed(),
                                'enabled': element.is_enabled(),
                                'type': element.get_attribute('type')
                            }
                            alternative_fields.append(field_info)
                        except:
                            continue
                except:
                    continue
            
            self.logger.info(f"土日用代替フィールド: {len(alternative_fields)}個検出")
            for field in alternative_fields:
                self.logger.debug(f"  - name='{field['name']}', visible={field['visible']}, enabled={field['enabled']}")
            
            return {'alternative_fields': alternative_fields}
            
        except Exception as e:
            self.logger.error(f"土日代替フィールド検索エラー: {e}")
            return {'alternative_fields': []}

    def _handle_weekend_input_mode(self, start_time: str, end_time: str, location_type: str) -> bool:
        """土日モードでの入力処理（時刻入力スキップ）"""
        try:
            self.logger.info("土日モードでの在宅/出社区分設定のみ実行")
            self.logger.info(f"CSVの勤務時間（{start_time} - {end_time}）は無視します")
            
            # 土日の場合は入力をスキップするオプション
            if hasattr(self, 'skip_weekends') and self.skip_weekends:
                self.logger.info("土日のため入力をスキップします")
                return True
            
            # 画面から現在の終了時間を読み取って22:15チェック
            self._check_and_adjust_end_time()
            
            # 土日用の代替フィールドを検索（在宅/出社区分のみ）
            alternative_fields = self._get_weekend_alternative_fields()
            
            if not alternative_fields['alternative_fields']:
                self.logger.warning("土日用の代替フィールドが見つかりません")
                # 強制的に標準フィールドを試行
                return self._try_standard_weekend_input(start_time, end_time, location_type)
            
            # 代替フィールドを使用した入力
            return self._input_with_alternative_fields(
                alternative_fields['alternative_fields'], 
                start_time, 
                end_time, 
                location_type
            )
            
        except Exception as e:
            self.logger.error(f"土日モード入力エラー: {e}")
            return False

    def _try_standard_weekend_input(self, start_time: str, end_time: str, location_type: str) -> bool:
        """標準フィールドでの土日入力試行"""
        try:
            self.logger.info("標準フィールドで土日入力を試行")
            
            # ページを強制リフレッシュ
            self.driver.refresh()
            self.wait_for_page_load()
            
            # 少し長めに待機
            time.sleep(5)
            
            # 利用可能なフィールドを再検出
            available_fields = self._detect_available_time_fields()
            
            # 検出されたフィールドで入力を試行
            if available_fields['start_time'] and available_fields['end_time']:
                start_field = available_fields['start_time'][0]['element']
                end_field = available_fields['end_time'][0]['element']
                
                # 入力試行
                if self._safe_input_to_element(start_field, start_time):
                    if self._safe_input_to_element(end_field, end_time):
                        self.logger.info("土日での標準フィールド入力成功")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"標準土日入力エラー: {e}")
            return False

    def _input_with_alternative_fields(self, fields: list, start_time: str, end_time: str, location_type: str) -> bool:
        """代替フィールドを使用した入力"""
        try:
            # 使用可能なフィールドを探す
            for field_info in fields:
                element = field_info['element']
                
                if field_info['visible'] and field_info['enabled']:
                    # とりあえず開始時刻を入力してみる
                    if self._safe_input_to_element(element, start_time):
                        self.logger.info(f"代替フィールド入力成功: {field_info['name']}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"代替フィールド入力エラー: {e}")
            return False

    def _safe_input_to_element(self, element, value: str) -> bool:
        """要素への安全な入力（既存値完全クリア付き）"""
        try:
            if not self._verify_element_interactable(element):
                return False
            
            # 既存値をチェック
            current_value = element.get_attribute('value') or ''
            self.logger.debug(f"現在の値: '{current_value}' -> 入力予定値: '{value}'")
            
            # 同じ値が既に入力されている場合はスキップ（時刻正規化比較）
            if self._normalize_time(current_value) == self._normalize_time(value):
                self.logger.info(f"既に正しい値が入力済みのためスキップ: {value}")
                return True
            
            # 現在値をログ出力
            if current_value:
                self.logger.info(f"既存値を完全クリア後に入力: '{current_value}' -> '{value}'")
            
            if not self._safe_click(element):
                return False
            
            # 既存値を完全にクリア（複数の方法で確実に）
            self._clear_element_value(element)
            
            # 新しい値を入力
            element.send_keys(value)
            
            # JavaScriptで直接値をセット（フォールバック）
            self.driver.execute_script("""
                arguments[0].value = arguments[1];
                arguments[0].setAttribute('value', arguments[1]);
                arguments[0].removeAttribute('defaulttime');
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """, element, value)
            self.logger.debug(f"JavaScriptで値を直接設定: {value}")
            
            # Enterキーで入力を確定
            from selenium.webdriver.common.keys import Keys
            element.send_keys(Keys.ENTER)
            self.logger.debug("Enterキーで入力確定")
            
            # フォーカスアウトでも確定（念のため）
            element.send_keys(Keys.TAB)
            self.logger.debug("TABキーでフォーカスアウト")
            
            # 少し待機してから結果確認
            import time
            time.sleep(0.1)
            
            # 入力結果を確認
            actual_value = element.get_attribute('value') or ''
            
            # 時刻の正規化比較
            normalized_expected = self._normalize_time(value)
            normalized_actual = self._normalize_time(actual_value)
            
            if normalized_actual == normalized_expected:
                self.logger.debug(f"入力成功確認: {value}")
                return True
            else:
                self.logger.warning(f"入力値が異なります: 期待={value}, 実際={actual_value}")
                return False
            
        except Exception as e:
            self.logger.error(f"要素入力エラー: {e}")
            return False
    
    def _normalize_time(self, time_str: str) -> str:
        """時刻文字列を正規化（ゼロパディングを削除）"""
        if not time_str:
            return ""
        
        # HH:MM形式を想定
        try:
            if ":" in time_str:
                hours, minutes = time_str.split(":")
                # 先頭の0を削除
                hours = str(int(hours))
                minutes = str(int(minutes)).zfill(2)  # 分は2桁に統一
                return f"{hours}:{minutes}"
            else:
                return time_str
        except:
            return time_str

    def _clear_element_value(self, element):
        """要素の値を完全にクリア（stale element対策付き）"""
        try:
            from selenium.webdriver.common.keys import Keys
            from selenium.common.exceptions import StaleElementReferenceException
            import time
            
            # Stale element対策: 要素が有効かチェック
            try:
                # クリア前の値を記録
                before_value = element.get_attribute('value') or ''
                default_time = element.get_attribute('defaulttime') or ''
                self.logger.info(f"クリア前の値: '{before_value}', defaulttime: '{default_time}'")
            except StaleElementReferenceException:
                self.logger.warning("要素が無効化されています（stale element）")
                return
            
            # 方法1: JavaScriptで完全クリア（最初に実行）
            self.logger.debug("方法1: JavaScriptで属性レベルクリア")
            try:
                self.driver.execute_script("""
                    if (arguments[0] && arguments[0].parentNode) {
                        arguments[0].value = '';
                        arguments[0].setAttribute('value', '');
                        if (arguments[0].hasAttribute('defaulttime')) {
                            arguments[0].removeAttribute('defaulttime');
                        }
                        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                    }
                """, element)
                time.sleep(0.1)  # DOM更新待機
            except StaleElementReferenceException:
                self.logger.warning("JavaScriptクリア中に要素が無効化されました")
                return
            
            # 方法2: フォーカスして全選択削除（stale element確認付き）
            try:
                self.logger.debug("方法2: フォーカス+全選択削除")
                element.click()
                time.sleep(0.05)
                element.send_keys(Keys.CONTROL + "a")
                element.send_keys(Keys.DELETE)
                after_select_delete = element.get_attribute('value') or ''
                self.logger.debug(f"全選択+削除後の値: '{after_select_delete}'")
            except StaleElementReferenceException:
                self.logger.warning("フォーカス+全選択削除中に要素が無効化されました")
                return
            
            # 方法3: 標準のclear()
            self.logger.debug("方法3: element.clear()を実行")
            element.clear()
            after_clear = element.get_attribute('value') or ''
            self.logger.debug(f"clear()後の値: '{after_clear}'")
            
            # 方法4: 値が残っていたらBackSpace
            current_value = element.get_attribute('value') or ''
            if current_value:
                self.logger.debug(f"方法4: BackSpaceで{len(current_value)}文字削除")
                # JavaScriptでフォーカス
                self.driver.execute_script("arguments[0].focus();", element)
                element.send_keys(Keys.END)  # カーソルを最後に移動
                for _ in range(len(current_value) + 5):  # 余分に削除
                    element.send_keys(Keys.BACKSPACE)
                after_backspace = element.get_attribute('value') or ''
                self.logger.debug(f"BackSpace後の値: '{after_backspace}'")
            
            # 最終確認
            time.sleep(0.1)  # 最終的なDOM更新待機
            final_value = element.get_attribute('value') or ''
            self.logger.info(f"クリア完了後の値: '{final_value}'")
            
            # まだ値が残っている場合の最終手段
            if final_value != '':
                self.logger.warning(f"まだ値が残存: '{final_value}' - 最終手段実行")
                
                # 最終手段: 強制的にJavaScriptで空文字を設定
                self.driver.execute_script("""
                    var element = arguments[0];
                    // 全てのイベントリスナーを一時的に無効化
                    var clone = element.cloneNode(true);
                    element.parentNode.replaceChild(clone, element);
                    clone.value = '';
                    clone.setAttribute('value', '');
                    // 要素を再取得
                    return clone;
                """, element)
                
                # 要素の再取得が必要な場合があるため、少し待機
                time.sleep(0.2)
                self.logger.info("最終手段のクリア完了")
            
        except Exception as e:
            self.logger.error(f"要素クリアエラー: {e}")
            # エラーがあっても処理を続行
    
    def input_work_time(self, start_time: str, end_time: str, location_type: str) -> bool:
        """
        勤務時間を入力（土日対応強化版）
        
        Args:
            start_time: 開始時刻 "HH:MM" 形式
            end_time: 終了時刻 "HH:MM" 形式  
            location_type: 在宅/出社区分
            
        Returns:
            bool: 成功時True
        """
        try:
            self.logger.info(f"勤務時間入力開始: {start_time} - {end_time}, {location_type}")
            
            # ページの準備を待つ（高速版）
            self.wait_for_page_load()
            
            # 現在のURLとタイトルをログ
            self.logger.info(f"現在のURL: {self.driver.current_url}")
            self.logger.info(f"ページタイトル: {self.driver.title}")
            
            # 土日判定
            if self._is_weekend_or_holiday():
                self.logger.info("土日・祝日が検出されました")
                return self._handle_weekend_input_mode(start_time, end_time, location_type)
            
            # 平日の標準処理
            return self._handle_weekday_input_mode(start_time, end_time, location_type)
            
        except Exception as e:
            self.logger.error(f"勤務時間入力エラー: {e}")
            self.save_screenshot("work_time_input_error")
            return False

    def _handle_weekday_input_mode(self, start_time: str, end_time: str, location_type: str) -> bool:
        """平日モードでの入力処理（時刻入力スキップ）"""
        try:
            self.logger.info("平日モードでの在宅/出社区分設定のみ実行")
            self.logger.info(f"CSVの勤務時間（{start_time} - {end_time}）は無視します")
            
            # 画面から現在の終了時間を読み取って22:15チェック
            self._check_and_adjust_end_time()
            
            # 在宅/出社区分選択（必須）
            try:
                # 複数の方法でセレクト要素を探す
                select_element = None
                
                # 方法1: NAME属性
                try:
                    select_element = self.wait_for_element(By.NAME, "GI_COMBOBOX38_Seq0S", timeout=5)
                except:
                    pass
                
                # 方法2: CSS Selector
                if not select_element:
                    try:
                        select_element = self.wait_for_element(By.CSS_SELECTOR, "select[name='GI_COMBOBOX38_Seq0S']", timeout=5)
                    except:
                        pass
                
                # 方法3: XPath
                if not select_element:
                    try:
                        select_element = self.wait_for_element(By.XPATH, "//select[contains(@name, 'COMBOBOX38')]", timeout=5)
                    except:
                        pass
                
                if not select_element:
                    self.logger.error("在宅/出社区分のセレクトボックスが見つかりません")
                    self.save_screenshot("location_select_not_found")
                    return False
                
                # スクロールして表示
                self.driver.execute_script("arguments[0].scrollIntoView(true);", select_element)
                time.sleep(0.5)
                
                location_select = Select(select_element)
                location_map = {
                    "在宅": "2",
                    "出社（通勤費往復）": "5",
                    "出社（通勤費片道）": "6", 
                    "出社（通勤費なし）": "7",
                    "その他": "4"
                }
                
                if location_type in location_map:
                    location_select.select_by_value(location_map[location_type])
                    self.logger.info(f"在宅/出社区分を設定: {location_type}")
                else:
                    self.logger.error(f"不正な在宅/出社区分: {location_type}")
                    return False
                
            except Exception as e:
                self.logger.error(f"在宅/出社区分の選択エラー: {e}")
                self.save_screenshot("location_select_error")
                return False
            
            self.logger.info("在宅/出社区分設定完了")
            return True
            
        except Exception as e:
            self.logger.error(f"在宅/出社区分設定エラー: {e}")
            self.save_screenshot("location_select_error")
            return False
    
    def save_screenshot(self, name: str = ""):
        """デバッグ用スクリーンショットを保存（強化版）"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{name}_{timestamp}.png" if name else f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # スクリーンショット保存
            self.driver.save_screenshot(filepath)
            
            # 追加のデバッグ情報をログに記録
            try:
                current_url = self.driver.current_url
                page_title = self.driver.title
                window_size = self.driver.get_window_size()
                
                self.logger.info(f"スクリーンショット保存: {filepath}")
                self.logger.info(f"  - URL: {current_url}")
                self.logger.info(f"  - タイトル: {page_title}")
                self.logger.info(f"  - ウィンドウサイズ: {window_size['width']}x{window_size['height']}")
                
                # プロジェクトグリッドに関する情報も記録（該当する場合）
                if "project" in name.lower():
                    try:
                        grid_rows = self.driver.find_elements(By.CSS_SELECTOR, ".slick-row")
                        self.logger.info(f"  - SlickGridの行数: {len(grid_rows)}")
                        
                        active_cells = self.driver.find_elements(By.CSS_SELECTOR, ".slick-cell.active")
                        self.logger.info(f"  - アクティブなセル数: {len(active_cells)}")
                        
                    except Exception:
                        pass
                        
            except Exception as debug_e:
                self.logger.warning(f"追加デバッグ情報取得エラー: {debug_e}")
            
            return filepath
        except Exception as e:
            self.logger.error(f"スクリーンショット保存エラー: {e}")
            return None
    
    def wait_for_element(self, by: By, value: str, timeout: int = 10) -> Optional:
        """要素が利用可能になるまで待機（高速化版）"""
        try:
            # 即座に要素を検索
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            
            # 要素が見つかったら即座に可視性とクリック可能性を確認
            if element.is_displayed() and element.is_enabled():
                self.logger.debug(f"要素の準備完了（高速版）: {by}={value}")
                return element
            
            # 見つからない場合のみ追加待機
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((by, value))
            )
            
            return element
                        
        except TimeoutException:
            self.logger.error(f"要素が見つかりません: {by}={value}")
            self.save_screenshot("element_not_found")
            return None

    def _wait_for_element_with_dom_monitoring(self, by: By, value: str, timeout: int) -> Optional:
        """DOM変更監視付きの要素待機"""
        try:
            # ステップ1: DOM変更が安定するまで待機
            self._wait_for_dom_stability()
            
            # ステップ2: 要素の存在を確認
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            
            # ステップ3: 要素が完全に読み込まれるまで待機
            self._wait_for_element_complete_load(element)
            
            # ステップ4: 要素が可視状態になるまで待機
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            
            # ステップ5: 要素がクリック可能になるまで待機
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            
            # ステップ6: 要素の属性が安定するまで待機
            self._wait_for_element_attributes_stable(element)
            
            self.logger.debug(f"要素の準備完了（強化版）: {by}={value}")
            return element
            
        except Exception as e:
            self.logger.error(f"要素待機エラー: {e}")
            raise

    def _wait_for_dom_stability(self, max_wait: int = 10):
        """DOM変更が安定するまで待機"""
        try:
            stable_count = 0
            required_stable_count = 3
            previous_dom_size = 0
            
            for _ in range(max_wait):
                # DOM要素数を取得
                current_dom_size = self.driver.execute_script(
                    "return document.getElementsByTagName('*').length"
                )
                
                # DOM要素数が安定しているかチェック
                if current_dom_size == previous_dom_size:
                    stable_count += 1
                    if stable_count >= required_stable_count:
                        self.logger.debug(f"DOM安定化完了: 要素数={current_dom_size}")
                        return
                else:
                    stable_count = 0
                
                previous_dom_size = current_dom_size
                time.sleep(0.5)
            
            self.logger.warning("DOM安定化がタイムアウトしました")
            
        except Exception as e:
            self.logger.error(f"DOM安定化監視エラー: {e}")

    def _wait_for_element_complete_load(self, element, max_wait: int = 5):
        """要素の完全読み込み待機"""
        try:
            for _ in range(max_wait):
                # 要素の属性が設定されているかチェック
                if element.get_attribute('name') and element.tag_name:
                    # フォーム要素の場合は追加チェック
                    if element.tag_name.lower() in ['input', 'select', 'textarea']:
                        # disabled状態でないことを確認
                        if not element.get_attribute('disabled'):
                            self.logger.debug("要素の完全読み込み確認完了")
                            return
                    else:
                        self.logger.debug("要素の完全読み込み確認完了")
                        return
                
                time.sleep(0.2)
            
            self.logger.warning("要素の完全読み込み確認がタイムアウト")
            
        except Exception as e:
            self.logger.error(f"要素完全読み込み確認エラー: {e}")

    def _wait_for_element_attributes_stable(self, element, max_wait: int = 3):
        """要素属性の安定化待機"""
        try:
            previous_attributes = {}
            stable_count = 0
            
            for _ in range(max_wait * 5):  # 0.2秒 × 5 = 1秒間隔
                current_attributes = {
                    'name': element.get_attribute('name'),
                    'class': element.get_attribute('class'),
                    'style': element.get_attribute('style'),
                    'disabled': element.get_attribute('disabled')
                }
                
                if current_attributes == previous_attributes:
                    stable_count += 1
                    if stable_count >= 2:  # 2回連続で同じなら安定
                        self.logger.debug("要素属性の安定化完了")
                        return
                else:
                    stable_count = 0
                
                previous_attributes = current_attributes
                time.sleep(0.2)
            
            self.logger.debug("要素属性の安定化確認完了（タイムアウト）")
            
        except Exception as e:
            self.logger.error(f"要素属性安定化確認エラー: {e}")

    def wait_for_page_load(self, timeout: int = 15):
        """ページの読み込み完了を待機（高速版）"""
        try:
            # document.readyStateの確認のみ（高速化）
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            self.logger.debug("ページの読み込み完了確認（高速版）")
            
        except TimeoutException:
            self.logger.warning("ページの読み込み完了待機がタイムアウトしました")
        except Exception as e:
            self.logger.error(f"ページ読み込み待機エラー: {e}")

    def _wait_for_network_idle(self, max_wait: int = 10):
        """ネットワークアクティビティの終了待機"""
        try:
            # Performance APIを使用してネットワーク監視
            for _ in range(max_wait):
                # アクティブなリクエスト数を確認
                network_script = """
                if (window.performance && window.performance.getEntriesByType) {
                    var entries = window.performance.getEntriesByType('resource');
                    var recent = entries.filter(function(entry) {
                        return (Date.now() - entry.responseEnd) < 1000;
                    });
                    return recent.length;
                }
                return 0;
                """
                
                active_requests = self.driver.execute_script(network_script)
                
                if active_requests == 0:
                    self.logger.debug("ネットワークアイドル状態確認完了")
                    return
                
                time.sleep(0.5)
            
            self.logger.debug("ネットワークアイドル確認がタイムアウト")
            
        except Exception as e:
            self.logger.error(f"ネットワークアイドル確認エラー: {e}")
    
    def _input_time_field(self, field_name: str, value: str):
        """時間フィールドに値を入力（堅牢性向上版）"""
        try:
            # 最初にオーバーレイ要素を非表示にする
            self._hide_overlay_elements()
            
            # 複数の方法で要素を探す（XPathを含む）
            field = None
            
            # 方法1: メインドキュメントでNAME属性検索
            try:
                field = self.wait_for_element_stable(By.NAME, field_name, timeout=5)
                if field:
                    self.logger.info(f"メインドキュメントで要素発見: {field_name}")
                    # 要素が見つかったので即座に処理継続
                    return self._safe_input_to_element(field, value)
            except:
                pass
            
            # 方法2: XPathを使用した詳細検索
            if not field:
                field = self._search_by_xpath(field_name)
                if field:
                    self.logger.info(f"XPathで要素発見: {field_name}")
                    return self._safe_input_to_element(field, value)
            
            # 方法3: iframe内の検索
            if not field:
                field = self._search_in_iframes(field_name)
                if field:
                    self.logger.info(f"iframe内で要素発見: {field_name}")
                    return self._safe_input_to_element(field, value)
            
            # 方法4: ID属性
            if not field:
                try:
                    field = self.wait_for_element_stable(By.ID, field_name, timeout=5)
                    if field:
                        return self._safe_input_to_element(field, value)
                except:
                    pass
            
            # 方法5: CSS Selector
            if not field:
                try:
                    field = self.wait_for_element_stable(By.CSS_SELECTOR, f"input[name='{field_name}']", timeout=5)
                    if field:
                        return self._safe_input_to_element(field, value)
                except:
                    pass
            
            # 方法6: 類似name属性の検索
            if not field:
                field = self._search_similar_fields(field_name)
                if field:
                    self.logger.warning(f"類似要素で代替: {field_name} → {field.get_attribute('name')}")
                    return self._safe_input_to_element(field, value)
            
            if not field:
                self.logger.error(f"フィールドが見つかりません: {field_name}")
                self._debug_page_elements()
                self.save_screenshot(f"field_not_found_{field_name}")
                return False
            
            # 要素の可視性とクリック可能性を確認
            if not self._verify_element_interactable(field):
                self.logger.error(f"要素が操作不可能です: {field_name}")
                return False
            
            # 要素にスクロール
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", field)
            time.sleep(0.5)
            
            # クリックして要素をアクティブに
            if not self._safe_click(field):
                self.logger.error(f"要素のクリックに失敗: {field_name}")
                return False
            
            # 既存値をチェック
            current_value = field.get_attribute('value') or ''
            self.logger.debug(f"フィールド '{field_name}' 現在値: '{current_value}' -> 入力予定: '{value}'")
            
            # 同じ値が既に入力されている場合はスキップ
            if current_value == value:
                self.logger.info(f"フィールド '{field_name}' は既に正しい値が入力済みのためスキップ: {value}")
                return True
            
            # 値をクリアして入力
            field.clear()
            field.send_keys(value)
            
            # 入力値の確認
            actual_value = field.get_attribute('value')
            if actual_value != value:
                self.logger.warning(f"入力値が異なります: 期待={value}, 実際={actual_value}")
                return False
            
            self.logger.debug(f"フィールド入力成功: {field_name} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"フィールド入力エラー: {field_name} - {e}")
            self.save_screenshot(f"input_error_{field_name}")
            return False
    
    def input_break_time(self, break_times: List[Tuple[str, str]]) -> bool:
        """
        休憩時間を入力（複数休憩は1レコードに統合）
        
        Args:
            break_times: [(開始時刻, 終了時刻), ...] のリスト
            
        Returns:
            bool: 成功時True
        """
        try:
            if not break_times:
                self.logger.info("休憩時間が設定されていません")
                return True
            
            # 複数の休憩時間を1つに統合
            if len(break_times) == 1:
                # 1つの休憩時間の場合はそのまま使用
                break_start, break_end = break_times[0]
                self.logger.info(f"休憩時間入力: {break_start} - {break_end}")
            else:
                # 複数の休憩時間を統合（最初の開始時刻から最後の終了時刻まで）
                all_starts = [break_time[0] for break_time in break_times]
                all_ends = [break_time[1] for break_time in break_times]
                
                # 最も早い開始時刻と最も遅い終了時刻を使用
                break_start = min(all_starts)
                break_end = max(all_ends)
                
                self.logger.info(f"複数休憩を統合: {len(break_times)}個の休憩 → {break_start} - {break_end}")
                for i, (start, end) in enumerate(break_times, 1):
                    self.logger.info(f"  休憩{i}: {start} - {end}")
            
            # 休憩時間を1レコード目に入力（行追加なし）
            self._input_time_field("RCSST10_Seq0STDI", break_start)
            self._input_time_field("RCSST10_Seq0ETDI", break_end)
            
            self.logger.info("休憩時間入力完了")
            return True
            
        except Exception as e:
            self.logger.error(f"休憩時間入力エラー: {e}")
            return False
    
    def _add_break_row(self):
        """休憩行を追加（正しいボタンIDを使用）"""
        try:
            add_button = self.driver.find_element(By.ID, "ADDRTRW6")
            # JavaScriptで直接クリック
            self.driver.execute_script("arguments[0].click();", add_button)
            time.sleep(0.5)
            self.logger.info("休憩行を追加しました")
        except NoSuchElementException:
            self.logger.warning("休憩追加ボタンが見つかりません: ADDRTRW6")
    
    def add_project_work(self, project_index: int, work_time: str, comment: str = "") -> bool:
        """
        プロジェクト作業時間を入力
        
        Args:
            project_index: プロジェクト行番号（0から開始）
            work_time: 作業時間 "H:MM" 形式
            comment: 備考
            
        Returns:
            bool: 成功時True
        """
        try:
            self.logger.info(f"プロジェクト{project_index + 1}入力: {work_time}, {comment}")
            
            # SlickGridの時間入力セルを複数のパターンで検索
            work_time_cell = self._find_project_time_cell(project_index)
            if not work_time_cell:
                self.logger.error(f"プロジェクト{project_index + 1}の時間入力セルが見つかりません")
                self.save_screenshot(f"project_time_cell_not_found_{project_index}")
                return False
            
            # 固定フッターを一時的に非表示にしてからクリック
            if not self._safe_click(work_time_cell):
                return False
            
            # SlickGrid編集モードの確認と入力処理
            if not self._handle_slick_grid_input(work_time):
                return False
            
            # 備考の入力はスキップ
            if comment:
                self.logger.info(f"備考入力をスキップ: {comment}")
            
            self.logger.info(f"プロジェクト{project_index + 1}入力完了")
            return True
            
        except Exception as e:
            self.logger.error(f"プロジェクト入力エラー: {e}")
            return False
    
    def calculate(self) -> bool:
        """計算ボタンを押下"""
        try:
            calc_btn = self.driver.find_element(By.ID, "btnCalc0")
            
            # JavaScriptで直接クリック（座標の問題を回避）
            self.driver.execute_script("arguments[0].click();", calc_btn)
            self.logger.info("計算実行中...")
            time.sleep(3)  # 計算完了を待機
            return True
            
        except Exception as e:
            self.logger.error(f"計算エラー: {e}")
            return False
    
    def check_errors(self) -> List[str]:
        """エラーメッセージの確認"""
        try:
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error")
            errors = []
            
            for error in error_elements:
                error_text = error.text.strip()
                if error_text:
                    errors.append(error_text)
                    self.logger.error(f"エラー検出: {error_text}")
            
            return errors
            
        except Exception as e:
            self.logger.error(f"エラーチェック失敗: {e}")
            return []
    
    def should_skip_date_for_errors(self, errors: List[str]) -> bool:
        """エラーに基づいて日付をスキップするかどうか判定"""
        if not errors:
            return False
        
        # 許可されるエラー（処理を継続）
        allowed_errors = [
            "在宅/出社区分が入力されていません",
            "在宅/出社区分が入力されていません。"
        ]
        
        # 全てのエラーが許可されたエラーかチェック
        for error in errors:
            if not any(allowed_error in error for allowed_error in allowed_errors):
                self.logger.warning(f"スキップ対象のエラー: {error}")
                return True
        
        return False
    
    def save_and_next(self) -> bool:
        """次へボタンを押下して確認画面に遷移"""
        try:
            next_btn = self.driver.find_element(By.ID, "btnNext0")
            # JavaScriptで直接クリック
            self.driver.execute_script("arguments[0].click();", next_btn)
            self.logger.info("確認画面に遷移中...")
            time.sleep(5)  # 画面遷移を待機
            return True
            
        except Exception as e:
            self.logger.error(f"画面遷移エラー: {e}")
            return False
    
    def get_actual_work_hours(self) -> Optional[str]:
        """実労働時間を取得"""
        try:
            # 実労働時間の要素を探す（複数パターン）
            patterns = [
                # パターン1: ID指定
                (By.ID, "WORKTIME"),
                (By.ID, "KNMJISSUTTM"),
                (By.ID, "JISSUTTM"),
                # パターン2: name属性
                (By.NAME, "WORKTIME"),
                (By.NAME, "KNMJISSUTTM"),
                (By.NAME, "JISSUTTM"),
                # パターン3: クラス名
                (By.CLASS_NAME, "actual-work-time"),
                (By.CLASS_NAME, "work-time"),
                # パターン4: XPath
                (By.XPATH, "//td[contains(text(), '実労働時間')]/following-sibling::td"),
                (By.XPATH, "//span[contains(@id, 'WORKTIME')]"),
                (By.XPATH, "//input[@readonly and contains(@name, 'JISSUTTM')]"),
            ]
            
            for by, value in patterns:
                try:
                    element = self.driver.find_element(by, value)
                    if element:
                        # inputタグの場合はvalue属性、それ以外はtext
                        if element.tag_name.lower() == 'input':
                            work_hours = element.get_attribute('value')
                        else:
                            work_hours = element.text
                        
                        if work_hours:
                            self.logger.info(f"実労働時間取得成功: {work_hours}")
                            return work_hours
                except:
                    continue
            
            self.logger.warning("実労働時間の要素が見つかりません")
            return None
            
        except Exception as e:
            self.logger.error(f"実労働時間取得エラー: {e}")
            return None
    
    def submit_confirmation(self) -> bool:
        """確認画面でdSubmission0ボタンをクリックして提出"""
        try:
            self.logger.info("確認画面で提出ボタンを探しています...")
            
            # dSubmission0ボタンを探してクリック
            submit_button = self.driver.find_element(By.ID, "dSubmission0")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            time.sleep(1)
            
            # JavaScriptで直接クリック
            self.driver.execute_script("arguments[0].click();", submit_button)
            self.logger.info("提出ボタン(dSubmission0)をクリックしました")
            
            time.sleep(3)
            return True
            
        except Exception as e:
            self.logger.error(f"提出ボタンクリックエラー: {e}")
            return False
    
    def confirm_and_submit(self) -> bool:
        """確認画面で最終提出"""
        try:
            # 確認画面で「入力完了」ボタンを押下
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '入力完了')]")
            # JavaScriptで直接クリック
            self.driver.execute_script("arguments[0].click();", submit_btn)
            self.logger.info("最終提出実行中...")
            time.sleep(5)
            return True
            
        except Exception as e:
            self.logger.error(f"最終提出エラー: {e}")
            return False
    
    
    def go_back_to_edit(self) -> bool:
        """確認画面から入力画面に戻る"""
        try:
            back_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '戻る')]")
            # JavaScriptで直接クリック
            self.driver.execute_script("arguments[0].click();", back_btn)
            self.logger.info("入力画面に戻ります...")
            time.sleep(3)
            return True
            
        except Exception as e:
            self.logger.error(f"戻るエラー: {e}")
            return False
    
    def navigate_to_next_day(self) -> bool:
        """翌日に遷移（土日スキップ対応版）"""
        try:
            self.logger.info("翌日への遷移を開始")
            
            # 現在の日付を取得
            current_date = self.get_current_date()
            if not current_date:
                self.logger.warning("現在の日付が取得できません")
                return self._try_traditional_navigation()
            
            # 日付をパースして次の営業日を計算
            next_business_date = self._get_next_business_date(current_date)
            
            if next_business_date:
                self.logger.info(f"現在の日付: {current_date}")
                self.logger.info(f"次の営業日: {next_business_date}")
                
                # 土日をスキップする必要があるかチェック
                if self._should_skip_weekends(current_date, next_business_date):
                    self.logger.info("土日をスキップして遷移します")
                    return self._navigate_to_specific_date(next_business_date)
                else:
                    # 通常の翌日遷移
                    return self._navigate_to_next_day_standard()
            else:
                self.logger.warning("次の営業日を計算できませんでした")
                return self._navigate_to_next_day_standard()
            
        except Exception as e:
            self.logger.error(f"日付遷移エラー: {e}")
            self.save_screenshot("navigation_error")
            return False
    
    def _get_next_business_date(self, current_date_str: str) -> str:
        """現在の日付から次の営業日を計算"""
        try:
            from datetime import datetime, timedelta
            import re
            
            # 日付文字列をパース
            date_obj = None
            
            # 複数の日付フォーマットを試す
            date_formats = [
                "%Y/%m/%d",
                "%Y-%m-%d",
                "%Y年%m月%d日",
                "%m/%d/%Y",
                "%m-%d-%Y"
            ]
            
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(current_date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if not date_obj:
                # 正規表現で数値を抽出
                numbers = re.findall(r'\d+', current_date_str)
                if len(numbers) >= 3:
                    year = int(numbers[0]) if len(numbers[0]) == 4 else int(numbers[2])
                    month = int(numbers[1]) if len(numbers[0]) == 4 else int(numbers[0])
                    day = int(numbers[2]) if len(numbers[0]) == 4 else int(numbers[1])
                    date_obj = datetime(year, month, day)
            
            if not date_obj:
                self.logger.error(f"日付のパースに失敗: {current_date_str}")
                return ""
            
            # 次の営業日を計算
            next_date = date_obj + timedelta(days=1)
            
            # 土日をスキップ
            while next_date.weekday() >= 5:  # 5=土曜, 6=日曜
                next_date += timedelta(days=1)
            
            return next_date.strftime("%Y/%m/%d")
            
        except Exception as e:
            self.logger.error(f"次の営業日計算エラー: {e}")
            return ""
    
    def _should_skip_weekends(self, current_date: str, next_business_date: str) -> bool:
        """土日をスキップする必要があるかチェック"""
        try:
            from datetime import datetime, timedelta
            
            # 現在の日付をパース
            current_obj = datetime.strptime(current_date.split()[0], "%Y/%m/%d")
            next_obj = datetime.strptime(next_business_date, "%Y/%m/%d")
            
            # 日付の差を計算
            diff = (next_obj - current_obj).days
            
            # 1日以上の差がある場合は土日をスキップ
            return diff > 1
            
        except Exception as e:
            self.logger.error(f"土日スキップ判定エラー: {e}")
            return False
    
    def _navigate_to_specific_date(self, target_date: str) -> bool:
        """指定の日付に直接遷移"""
        try:
            self.logger.info(f"指定日付へ遷移: {target_date}")
            
            # URLパラメータを使用して日付を指定
            current_url = self.driver.current_url
            
            # URLに日付パラメータを追加/更新
            if "?" in current_url:
                base_url = current_url.split("?")[0]
            else:
                base_url = current_url
            
            # 日付パラメータを追加（システムに応じて調整が必要）
            target_url = f"{base_url}?date={target_date.replace('/', '-')}"
            
            self.logger.info(f"遷移先URL: {target_url}")
            self.driver.get(target_url)
            
            # ページ読み込み完了を待機
            self.wait_for_page_load()
            time.sleep(2)
            
            # 日付が正しく更新されたかを確認
            new_date = self.get_current_date()
            if target_date in new_date:
                self.logger.info(f"日付遷移成功: {new_date}")
                return True
            else:
                self.logger.warning(f"日付遷移後の確認失敗: 期待={target_date}, 実際={new_date}")
                return self._navigate_to_next_day_standard()
                
        except Exception as e:
            self.logger.error(f"指定日付遷移エラー: {e}")
            return self._navigate_to_next_day_standard()
    
    def _navigate_to_next_day_standard(self) -> bool:
        """標準的な翌日遷移"""
        try:
            self.logger.info("標準的な翌日遷移を実行")
            
            # onclick属性を持つ要素を検索
            navigation_elements = []
            
            # 方法1: onclick属性にToNextDateActionを含む要素を検索
            try:
                elements = self.driver.find_elements(By.XPATH, "//*[contains(@onclick, 'ToNextDateAction')]")
                navigation_elements.extend(elements)
                self.logger.info(f"ToNextDateAction要素: {len(elements)}個見つかりました")
            except:
                pass
            
            # 方法2: onclick属性に翌日関連のテキストを含む要素
            try:
                elements = self.driver.find_elements(By.XPATH, "//*[contains(@onclick, '翌日') or contains(@onclick, 'next')]")
                navigation_elements.extend(elements)
                self.logger.info(f"翌日/next要素: {len(elements)}個見つかりました")
            except:
                pass
            
            # 方法3: title属性に翌日を含む要素のonclick
            try:
                elements = self.driver.find_elements(By.XPATH, "//*[contains(@title, '翌日') and @onclick]")
                navigation_elements.extend(elements)
                self.logger.info(f"title=翌日かつonclick要素: {len(elements)}個見つかりました")
            except:
                pass
            
            if not navigation_elements:
                self.logger.warning("onclick属性を持つナビゲーション要素が見つかりません")
                # 従来の方法を試す
                return self._try_traditional_navigation()
            
            # 最初の要素からonclick属性を取得
            nav_element = navigation_elements[0]
            onclick_value = nav_element.get_attribute("onclick")
            self.logger.info(f"onclick属性: {onclick_value}")
            
            if onclick_value:
                # onclick属性からURLを抽出して直接遷移
                return self._extract_and_navigate(onclick_value)
            else:
                self.logger.warning("onclick属性が空です")
                return self._try_traditional_navigation()
                
        except Exception as e:
            self.logger.error(f"標準翌日遷移エラー: {e}")
            return False
    
    def _extract_and_navigate(self, onclick_value: str) -> bool:
        """onclick属性からURLを抽出して遷移"""
        try:
            # location.href='URL' パターンを抽出
            import re
            url_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", onclick_value)
            
            if url_match:
                target_url = url_match.group(1)
                self.logger.info(f"抽出したURL: {target_url}")
                
                # 相対パスの場合は現在のベースURLと結合
                if target_url.startswith('/'):
                    base_url = self.driver.current_url.split('/')[0:3]  # protocol://host:port
                    full_url = '/'.join(base_url) + target_url
                elif not target_url.startswith('http'):
                    current_url = self.driver.current_url
                    base_url = '/'.join(current_url.split('/')[:-1])
                    full_url = base_url + '/' + target_url
                else:
                    full_url = target_url
                
                self.logger.info(f"遷移先URL: {full_url}")
                self.driver.get(full_url)
                time.sleep(3)  # ページ読み込み待機
                
                # 日付が変わったことを確認
                new_date = self.get_current_date()
                self.logger.info(f"遷移後の日付: {new_date}")
                
                return True
            else:
                self.logger.error(f"onclick属性からURLを抽出できません: {onclick_value}")
                return self._try_traditional_navigation()
                
        except Exception as e:
            self.logger.error(f"URL抽出・遷移エラー: {e}")
            return False
    
    def _try_traditional_navigation(self) -> bool:
        """従来の方法でナビゲーションを試行"""
        try:
            self.logger.info("従来の方法でナビゲーションを試行")
            
            # 複数の方法で翌日ボタンを探す
            next_day_btn = None
            
            # 方法1: title属性で検索
            try:
                next_day_btn = self.wait_for_element(By.XPATH, "//button[contains(@title, '翌日')]", timeout=5)
            except:
                pass
            
            # 方法2: テキストで検索
            if not next_day_btn:
                try:
                    next_day_btn = self.wait_for_element(By.XPATH, "//button[contains(text(), '翌日')]", timeout=5)
                except:
                    pass
            
            # 方法3: リンクとして実装されている場合
            if not next_day_btn:
                try:
                    next_day_btn = self.wait_for_element(By.XPATH, "//a[contains(@title, '翌日') or contains(text(), '翌日')]", timeout=5)
                except:
                    pass
            
            if not next_day_btn:
                self.logger.error("翌日ボタンが見つかりません")
                self.save_screenshot("next_day_button_not_found")
                return self._navigate_by_url_parameter()
            
            # ボタンが見つかった場合
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_day_btn)
            time.sleep(0.5)
            
            # JavaScriptで直接クリック
            self.driver.execute_script("arguments[0].click();", next_day_btn)
            
            self.logger.info("翌日ボタンをクリックしました")
            time.sleep(3)  # ページ遷移を待つ
            
            # 日付が変わったことを確認
            new_date = self.get_current_date()
            self.logger.info(f"遷移後の日付: {new_date}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"従来ナビゲーションエラー: {e}")
            return False
    
    def _navigate_by_url_parameter(self) -> bool:
        """URLパラメータを使用した日付遷移の代替方法"""
        try:
            current_url = self.driver.current_url
            self.logger.info(f"現在のURL: {current_url}")
            
            # URLから日付パラメータを解析して翌日のURLを生成
            # （実際のURLパターンに応じて調整が必要）
            
            # とりあえずページをリロードして続行
            self.driver.refresh()
            time.sleep(3)
            
            return True
            
        except Exception as e:
            self.logger.error(f"URL遷移エラー: {e}")
            return False
    
    def navigate_to_previous_day(self) -> bool:
        """前日に遷移"""
        try:
            prev_day_btn = self.driver.find_element(By.XPATH, "//button[contains(@title, '前日')]")
            # JavaScriptで直接クリック
            self.driver.execute_script("arguments[0].click();", prev_day_btn)
            self.logger.info("前日に遷移中...")
            time.sleep(3)
            return True
            
        except Exception as e:
            self.logger.error(f"日付遷移エラー: {e}")
            return False
    
    def _search_in_iframes(self, field_name: str):
        """iframe内で要素を検索"""
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            self.logger.info(f"iframe数: {len(iframes)}個")
            
            for i, iframe in enumerate(iframes):
                try:
                    # iframeに切り替え
                    self.driver.switch_to.frame(iframe)
                    self.logger.debug(f"iframe{i}に切り替え")
                    
                    # iframe内で要素を検索
                    elements = self.driver.find_elements(By.NAME, field_name)
                    if elements:
                        self.logger.info(f"iframe{i}内で{field_name}を発見: {len(elements)}個")
                        return elements[0]
                    
                except Exception as e:
                    self.logger.debug(f"iframe{i}のアクセス失敗: {e}")
                finally:
                    # メインドキュメントに戻る
                    self.driver.switch_to.default_content()
            
            return None
            
        except Exception as e:
            self.logger.error(f"iframe検索エラー: {e}")
            self.driver.switch_to.default_content()
            return None
    
    def _search_similar_fields(self, field_name: str):
        """類似するname属性の要素を検索"""
        try:
            # field_nameの部分文字列で検索
            if "KNMTMRNGSTDI" in field_name:
                # 開始時刻の類似パターン
                patterns = [
                    "*[name*='start'][name*='time']",
                    "*[name*='BEGIN'][name*='DI']",
                    "*[name*='ST'][name*='DI']",
                    "*[name*='KNM'][name*='STDI']",
                    "*[name*='TMRNG'][name*='ST']"
                ]
            elif "KNMTMRNGETDI" in field_name:
                # 終了時刻の類似パターン
                patterns = [
                    "*[name*='end'][name*='time']",
                    "*[name*='END'][name*='DI']",
                    "*[name*='ET'][name*='DI']",
                    "*[name*='KNM'][name*='ETDI']",
                    "*[name*='TMRNG'][name*='ET']"
                ]
            else:
                return None
            
            for pattern in patterns:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, pattern)
                    if elements:
                        self.logger.info(f"類似要素発見: {pattern} → {elements[0].get_attribute('name')}")
                        return elements[0]
                except:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"類似要素検索エラー: {e}")
            return None
    
    def _debug_page_elements(self):
        """デバッグ用：ページ内の要素情報を出力"""
        try:
            self.logger.info("=== デバッグ情報 ===")
            self.logger.info(f"URL: {self.driver.current_url}")
            self.logger.info(f"Title: {self.driver.title}")
            
            # 全てのinput[type=text]を一覧
            text_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type=text]")
            self.logger.info(f"テキスト入力要素: {len(text_inputs)}個")
            
            for i, input_elem in enumerate(text_inputs[:10]):  # 最初の10個まで
                name = input_elem.get_attribute("name") or "名前なし"
                value = input_elem.get_attribute("value") or ""
                self.logger.info(f"  {i+1}: name='{name}' value='{value}'")
            
            # KNM含む要素
            knm_elements = self.driver.find_elements(By.CSS_SELECTOR, "*[name*='KNM']")
            self.logger.info(f"KNM含む要素: {len(knm_elements)}個")
            for elem in knm_elements[:5]:
                name = elem.get_attribute("name")
                tag = elem.tag_name
                self.logger.info(f"  KNM要素: <{tag}> name='{name}'")
            
            # フォーム確認
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            self.logger.info(f"フォーム数: {len(forms)}個")
            for form in forms:
                form_name = form.get_attribute("name") or "名前なし"
                self.logger.info(f"  フォーム: name='{form_name}'")
            
        except Exception as e:
            self.logger.error(f"デバッグ情報取得エラー: {e}")

    def wait_for_page_load(self, timeout: int = 30):
        """ページの読み込み完了を待機"""
        try:
            # document.readyStateがcompleteになるまで待機
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # jQuery が存在する場合、jQueryの処理完了も待機
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: driver.execute_script("return typeof jQuery === 'undefined' || jQuery.active == 0")
                )
            except:
                pass  # jQueryが存在しない場合は無視
            
            self.logger.debug("ページの読み込みが完了しました")
            
        except TimeoutException:
            self.logger.warning("ページの読み込み完了待機がタイムアウトしました")
        except Exception as e:
            self.logger.error(f"ページ読み込み待機エラー: {e}")

    def wait_for_element_stable(self, by: By, value: str, timeout: int = 10) -> Optional:
        """要素が安定するまで待機（位置やサイズの変化を監視）"""
        try:
            element = self.wait_for_element(by, value, timeout)
            if not element:
                return None
            
            # 要素の位置が安定するまで待機
            previous_location = None
            stable_count = 0
            max_checks = 10
            
            for _ in range(max_checks):
                current_location = element.location
                if previous_location == current_location:
                    stable_count += 1
                    if stable_count >= 3:  # 3回連続で同じ位置なら安定とみなす
                        break
                else:
                    stable_count = 0
                
                previous_location = current_location
                time.sleep(0.1)
            
            self.logger.debug(f"要素が安定しました: {by}={value}")
            return element
            
        except Exception as e:
            self.logger.error(f"要素安定待機エラー: {e}")
            return None

    def _search_by_xpath(self, field_name: str):
        """XPathを使用した詳細な要素検索"""
        try:
            # XPathパターンの定義（正確な検索を優先）
            xpath_patterns = [
                # 完全一致検索（最優先）
                f"//input[@name='{field_name}']",
                
                # 時間フィールド固有のパターン（完全一致）
                f"//input[@name='{field_name}' and (@type='text' or @type='time')]",
                
                # より具体的なパターン（完全一致）
                f"//input[@name='{field_name}' and contains(@placeholder, '時')]",
                f"//input[@name='{field_name}' and contains(@placeholder, '分')]",
                
                # フォーム・テーブル内の完全一致検索
                f"//form//input[@name='{field_name}']",
                f"//table//input[@name='{field_name}']",
                
                # 周辺要素からの推定（完全一致）
                f"//td[contains(text(), '時刻')]//input[@name='{field_name}']",
                f"//label[contains(text(), '時刻')]//input[@name='{field_name}']",
                
                # 最後のフォールバック：部分一致検索
                f"//input[contains(@name, '{field_name}') and contains(@class, 'time')]",
                f"//input[contains(@name, '{field_name}')]",
                
                # 部分一致での検索（最後の手段）
                f"//input[contains(@name, '{field_name[:10]}')]",  # 前半部分
                f"//input[contains(@name, '{field_name[-10:]}')]",  # 後半部分
                
                # 部分的な名前での検索（開始時刻用）
                "//input[contains(@name, 'KNMTM') and contains(@name, 'STDI')]",
                "//input[contains(@name, 'KNMTM') and contains(@name, 'ETDI')]",
                
                # より広い範囲での検索（最後の手段）
                f"//input[contains(@name, 'KNM') and contains(@name, 'TM')]",
                f"//input[contains(@name, 'RNG') and contains(@name, 'DI')]"
            ]
            
            for pattern in xpath_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    if elements:
                        for element in elements:
                            # 要素の可視性を確認
                            if element.is_displayed() and element.is_enabled():
                                self.logger.info(f"XPath検索成功: {pattern}")
                                return element
                except Exception as e:
                    self.logger.debug(f"XPath検索失敗: {pattern} - {e}")
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"XPath検索エラー: {e}")
            return None

    def _verify_element_interactable(self, element) -> bool:
        """要素の可視性とクリック可能性を確認"""
        try:
            # 基本的な確認
            if not element.is_displayed():
                self.logger.debug("要素が非表示です")
                return False
            
            if not element.is_enabled():
                self.logger.debug("要素が無効です")
                return False
            
            # 要素のサイズを確認
            size = element.size
            if size['width'] == 0 or size['height'] == 0:
                self.logger.debug("要素のサイズが0です")
                return False
            
            # 要素の位置を確認
            location = element.location
            if location['x'] < 0 or location['y'] < 0:
                self.logger.debug("要素が画面外にあります")
                return False
            
            # 要素が他の要素に隠れていないかを確認
            try:
                # 要素の中心点を取得
                center_x = location['x'] + size['width'] / 2
                center_y = location['y'] + size['height'] / 2
                
                # 中心点にある要素を取得
                element_at_point = self.driver.execute_script(
                    "return document.elementFromPoint(arguments[0], arguments[1]);",
                    center_x, center_y
                )
                
                # 要素が自身または子要素でない場合は隠れている
                if element_at_point != element:
                    # 親要素を確認
                    parent = element
                    while parent:
                        if parent == element_at_point:
                            break
                        parent = parent.find_element(By.XPATH, "..")
                    else:
                        self.logger.debug("要素が他の要素に隠れています")
                        return False
            except:
                pass  # この確認は失敗しても続行
            
            # CSSスタイルの確認
            try:
                visibility = element.value_of_css_property('visibility')
                display = element.value_of_css_property('display')
                opacity = element.value_of_css_property('opacity')
                
                if visibility == 'hidden' or display == 'none' or opacity == '0':
                    self.logger.debug(f"CSS非表示: visibility={visibility}, display={display}, opacity={opacity}")
                    return False
            except:
                pass  # この確認は失敗しても続行
            
            self.logger.debug("要素は操作可能です")
            return True
            
        except Exception as e:
            self.logger.error(f"要素確認エラー: {e}")
            return False

    def _safe_click(self, element) -> bool:
        """要素の安全なクリック（UI障害対策強化版）"""
        try:
            # 方法1: JavaScriptで直接クリック（座標の問題を回避）
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            self.logger.warning(f"JavaScriptクリックが失敗、代替方法を試行: {e}")
            return self._handle_click_intercepted(element)

    def _handle_click_intercepted(self, element) -> bool:
        """クリック障害への対処（複数フォールバック）"""
        try:
            # 方法1: オーバーレイ要素を一時的に非表示
            if self._hide_overlay_elements():
                try:
                    element.click()
                    self.logger.info("オーバーレイ非表示後のクリック成功")
                    return True
                except:
                    pass
                finally:
                    self._restore_overlay_elements()
            
            # 方法2: スクロール位置を最適化してクリック
            if self._optimize_scroll_for_click(element):
                try:
                    element.click()
                    self.logger.info("スクロール最適化後のクリック成功")
                    return True
                except:
                    pass
            
            # 方法3: ActionChainsを使用（要素ベース）
            try:
                ActionChains(self.driver).click(element).perform()
                self.logger.info("ActionChainsクリック成功")
                return True
            except:
                pass
            
            # 方法4: 強制的なJavaScriptクリック（複数イベント）
            try:
                self.driver.execute_script("""
                    arguments[0].focus();
                    arguments[0].click();
                    arguments[0].dispatchEvent(new Event('click', {bubbles: true}));
                """, element)
                self.logger.info("強制JavaScriptクリック成功")
                return True
            except:
                pass
            
            # 方法5: 要素を前面に移動してクリック
            try:
                self.driver.execute_script("""
                    arguments[0].style.zIndex = '9999';
                    arguments[0].style.position = 'relative';
                    arguments[0].click();
                """, element)
                self.logger.info("Z-index調整クリック成功")
                return True
            except:
                pass
            
            self.logger.error("全てのクリック方法が失敗しました")
            return False
            
        except Exception as e:
            self.logger.error(f"クリック障害対処エラー: {e}")
            return False

    def _hide_overlay_elements(self) -> bool:
        """オーバーレイ要素を一時的に非表示（強化版）"""
        try:
            # 固定フッターボタンエリアの強制非表示（最優先）
            footer_script = """
            // 特定のIDで固定フッターを強制非表示
            var mainFooter = document.getElementById('srw_fixed_footer_button_area');
            if (mainFooter) {
                mainFooter.style.display = 'none !important';
                mainFooter.style.visibility = 'hidden !important';
                mainFooter.style.zIndex = '-9999';
                mainFooter.setAttribute('data-hidden-by-automation', 'true');
            }
            
            // その他のフッター要素も非表示
            var footers = document.querySelectorAll('[id*="footer"], [class*="footer"], [class*="fixed-footer"]');
            var hiddenCount = 0;
            for (var i = 0; i < footers.length; i++) {
                if (footers[i].style.position === 'fixed' || footers[i].style.position === 'sticky') {
                    footers[i].style.display = 'none !important';
                    footers[i].style.visibility = 'hidden !important';
                    footers[i].style.zIndex = '-9999';
                    footers[i].setAttribute('data-hidden-by-automation', 'true');
                    hiddenCount++;
                }
            }
            return hiddenCount + (mainFooter ? 1 : 0);
            """
            footer_hidden_count = self.driver.execute_script(footer_script)
            
            # company ロゴの非表示
            logo_script = """
            var logos = document.querySelectorAll('#srw_global_logo_img, [id*="logo"], [class*="logo"]');
            var hiddenCount = 0;
            for (var i = 0; i < logos.length; i++) {
                logos[i].style.display = 'none !important';
                logos[i].style.visibility = 'hidden !important';
                logos[i].setAttribute('data-hidden-by-automation', 'true');
                hiddenCount++;
            }
            return hiddenCount;
            """
            logo_hidden_count = self.driver.execute_script(logo_script)
            
            # 高z-indexオーバーレイ要素の非表示
            overlay_script = """
            var overlays = document.querySelectorAll('*');
            var hiddenCount = 0;
            for (var i = 0; i < overlays.length; i++) {
                var overlay = overlays[i];
                var computedStyle = window.getComputedStyle(overlay);
                var zIndex = parseInt(computedStyle.zIndex);
                var position = computedStyle.position;
                
                // 高z-indexかつfixed/absoluteの要素を非表示
                if ((position === 'fixed' || position === 'absolute') && zIndex > 900) {
                    overlay.style.display = 'none !important';
                    overlay.style.visibility = 'hidden !important';
                    overlay.setAttribute('data-hidden-by-automation', 'true');
                    hiddenCount++;
                }
            }
            return hiddenCount;
            """
            overlay_count = self.driver.execute_script(overlay_script)
            
            # ボディのパディング底部を一時的に増加（フッター分のスペース確保）
            self.driver.execute_script("""
                document.body.style.paddingBottom = '200px';
                document.body.setAttribute('data-padding-adjusted', 'true');
            """)
            
            self.logger.debug(f"オーバーレイ要素を非表示: フッター={footer_hidden_count}, ロゴ={logo_hidden_count}, その他={overlay_count}")
            return footer_hidden_count > 0 or logo_hidden_count > 0 or overlay_count > 0
            
        except Exception as e:
            self.logger.error(f"オーバーレイ非表示エラー: {e}")
            return False

    def _restore_overlay_elements(self):
        """非表示にしたオーバーレイ要素を復元"""
        try:
            restore_script = """
            var hiddenElements = document.querySelectorAll('[data-hidden-by-automation="true"]');
            for (var i = 0; i < hiddenElements.length; i++) {
                hiddenElements[i].style.display = '';
                hiddenElements[i].removeAttribute('data-hidden-by-automation');
            }
            return hiddenElements.length;
            """
            restored_count = self.driver.execute_script(restore_script)
            self.logger.debug(f"オーバーレイ要素を復元: {restored_count}個")
            
        except Exception as e:
            self.logger.error(f"オーバーレイ復元エラー: {e}")

    def _optimize_scroll_for_click(self, element) -> bool:
        """クリック用のスクロール位置最適化"""
        try:
            # 要素を画面中央に配置
            self.driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });
            """, element)
            time.sleep(0.5)
            
            # ヘッダー分を考慮してさらに調整
            self.driver.execute_script("""
                window.scrollBy(0, -100);
            """)
            time.sleep(0.3)
            
            # 要素が画面内に表示されているかを確認
            is_visible = self.driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                return rect.top >= 0 && rect.left >= 0 && 
                       rect.bottom <= window.innerHeight && 
                       rect.right <= window.innerWidth;
            """, element)
            
            self.logger.debug(f"スクロール最適化: 要素可視={is_visible}")
            return is_visible
            
        except Exception as e:
            self.logger.error(f"スクロール最適化エラー: {e}")
            return False

    def _handle_slick_grid_input(self, value: str) -> bool:
        """SlickGrid編集モードの確認と入力処理（クリック→待機→入力方式）"""
        try:
            self.logger.info("セルクリック後に待機してから入力を試行")
            
            # 最後にクリックしたアクティブセルを取得
            active_cell = None
            for selector in [".slick-cell.active", ".slick-cell.selected", ".slick-cell:focus"]:
                try:
                    active_cell = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if active_cell:
                        # セルの詳細情報をログ出力
                        cell_text = active_cell.text or "（空）"
                        cell_class = active_cell.get_attribute("class") or "（クラスなし）"
                        cell_tag = active_cell.tag_name
                        cell_location = active_cell.location
                        cell_size = active_cell.size
                        
                        self.logger.info(f"アクティブセル発見: {selector}")
                        self.logger.info(f"  - テキスト: '{cell_text}'")
                        self.logger.info(f"  - クラス: {cell_class}")
                        self.logger.info(f"  - タグ: {cell_tag}")
                        self.logger.info(f"  - 位置: x={cell_location['x']}, y={cell_location['y']}")
                        self.logger.info(f"  - サイズ: w={cell_size['width']}, h={cell_size['height']}")
                        break
                except:
                    continue
            
            # 最大3回リトライでダブルクリック処理を実行
            for retry_count in range(3):
                self.logger.info(f"ダブルクリック試行 {retry_count + 1}/3")
                
                if active_cell:
                    # セルをダブルクリック
                    self.logger.info(f"セルをダブルクリック（試行 {retry_count + 1}）")
                    from selenium.webdriver.common.action_chains import ActionChains
                    ActionChains(self.driver).double_click(active_cell).perform()
                    
                    # 1秒待機（編集モードになるまで）
                    self.logger.info("編集モードになるまで1秒待機")
                    time.sleep(1)
                    
                    # ダブルクリック後、セル内のinput要素を探す
                    self.logger.info("編集モード後のinput要素を検索")
                    input_element = None
                    input_selectors = [
                        ".slick-cell.active input",
                        ".slick-cell.selected input", 
                        ".slick-cell.editing input",
                        ".slick-editor input",
                        ".slick-editor-text input"
                    ]
                    
                    for selector in input_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                if element.is_displayed() and element.is_enabled():
                                    input_element = element
                                    self.logger.info(f"input要素発見: {selector}")
                                    break
                            if input_element:
                                break
                        except:
                            continue
                    
                    if input_element:
                        # input要素に文字を入力
                        self.logger.info(f"input要素に値を入力: {value}")
                        
                        # 既存の値をクリア
                        try:
                            input_element.clear()
                        except:
                            pass
                        
                        # 新しい値を入力
                        input_element.send_keys(value)
                        
                        # Enterキーで確定
                        self.logger.info("input要素でEnterキーで確定")
                        input_element.send_keys("\n")
                        time.sleep(0.3)
                        
                        self.logger.info(f"SlickGrid入力完了: {value}")
                        return True
                    else:
                        self.logger.warning(f"ダブルクリック後もinput要素が見つかりません（試行 {retry_count + 1}）")
                        if retry_count < 2:  # 最後の試行でない場合
                            self.logger.info("少し待機してから次の試行を実行")
                            time.sleep(1)
                            continue
                else:
                    self.logger.warning(f"アクティブセルが見つかりません（試行 {retry_count + 1}）")
                    if retry_count < 2:  # 最後の試行でない場合
                        time.sleep(1)
                        continue
            
            # 3回すべて失敗した場合
            self.logger.error("3回の試行すべてが失敗しました")
            
            # アクティブセルが見つからない場合のフォールバック
            self.logger.warning("アクティブセルが見つからない、従来の方法を試行")
            active_input = self._wait_for_slick_grid_input()
            
            if not active_input:
                self.logger.error("SlickGrid編集モードのアクティブ入力が見つかりません")
                return False
            
            # 入力値をクリアして新しい値を設定
            self._clear_element_value(active_input)
            
            # 値を入力
            active_input.send_keys(value)
            
            # Enterキーで確定
            active_input.send_keys("\n")
            
            # 入力が完了したかを確認
            time.sleep(0.3)
            
            self.logger.info(f"SlickGrid従来方式入力完了: {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"SlickGrid入力エラー: {e}")
            return False

    def _wait_for_slick_grid_input(self, timeout: int = 10):
        """SlickGrid編集モードの入力要素を待機"""
        try:
            # 複数のセレクターパターンを定義
            selectors = [
                ".slick-cell.active input",
                ".slick-cell.selected input", 
                ".slick-cell.editing input",
                ".slick-editor-text input",
                ".slick-editor input",
                ".slick-cell input:focus",
                ".slick-cell input[type='text']",
                ".slick-row .slick-cell input:not([readonly])"
            ]
            
            end_time = time.time() + timeout
            
            while time.time() < end_time:
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                self.logger.info(f"SlickGrid入力要素発見: {selector}")
                                return element
                    except:
                        continue
                
                # 短時間待機してリトライ
                time.sleep(0.1)
            
            # フォールバック: 強制的にダブルクリックして編集モードを有効化
            self.logger.warning("通常の方法で入力要素が見つからない、フォールバック処理を実行")
            return self._force_slick_grid_edit_mode()
            
        except Exception as e:
            self.logger.error(f"SlickGrid入力要素待機エラー: {e}")
            return None

    def _force_slick_grid_edit_mode(self):
        """SlickGrid編集モードを強制的に有効化（改善版）"""
        try:
            # 最後にクリックしたセルを検索
            active_cell = None
            for selector in [".slick-cell.active", ".slick-cell.selected", ".slick-cell:focus"]:
                try:
                    active_cell = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if active_cell:
                        break
                except:
                    continue
            
            if not active_cell:
                self.logger.error("アクティブなセルが見つかりません")
                return None
            
            # ダブルクリックで編集モードを有効化（SlickGridの標準方法）
            self.logger.info("ダブルクリックで編集モードを有効化")
            ActionChains(self.driver).double_click(active_cell).perform()
            time.sleep(0.5)
            
            # 編集モードの入力要素を検索
            edit_selectors = [
                ".slick-cell.active input",
                ".slick-cell.selected input",
                ".slick-cell input:focus",
                ".editor-text",
                "input.editor-text"
            ]
            
            for selector in edit_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.logger.info(f"強制編集モードで入力要素発見: {selector}")
                            return element
                except:
                    continue
            
            # F2キーで編集モード（SlickGridの別の方法）
            self.logger.info("F2キーで編集モードを試行")
            from selenium.webdriver.common.keys import Keys
            active_cell.send_keys(Keys.F2)
            time.sleep(0.3)
            
            # 再度入力要素を検索
            for selector in edit_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.logger.info(f"F2編集モードで入力要素発見: {selector}")
                            return element
                except:
                    continue
            
            # 最終手段：SlickGridの編集APIを直接呼び出し
            self.logger.warning("SlickGrid編集APIを直接呼び出し")
            edit_result = self.driver.execute_script("""
                // SlickGridインスタンスを探す
                var grid = null;
                var possibleGrids = [window.grid, window.slickGrid, window._grid];
                for (var i = 0; i < possibleGrids.length; i++) {
                    if (possibleGrids[i] && possibleGrids[i].getActiveCell) {
                        grid = possibleGrids[i];
                        break;
                    }
                }
                
                if (grid) {
                    var activeCell = grid.getActiveCell();
                    if (activeCell) {
                        grid.editActiveCell();
                        return true;
                    }
                }
                return false;
            """)
            
            if edit_result:
                time.sleep(0.3)
                # 編集モードになったか再確認
                for selector in edit_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                self.logger.info(f"API編集モードで入力要素発見: {selector}")
                                return element
                    except:
                        continue
            
            self.logger.error("全ての編集モード有効化方法が失敗しました")
            return None
            
        except Exception as e:
            self.logger.error(f"SlickGrid強制編集モードエラー: {e}")
            return None

    def verify_connection(self) -> bool:
        """接続確認とページアクセス可能性の確認"""
        try:
            self.logger.info("接続確認を開始します")
            
            # 現在のURLを取得
            current_url = self.driver.current_url
            self.logger.info(f"現在のURL: {current_url}")
            
            # ページタイトルを確認
            title = self.driver.title
            self.logger.info(f"ページタイトル: {title}")
            
            # ページが完全に読み込まれているかを確認
            self.wait_for_page_load()
            
            # 基本要素の存在確認
            try:
                # 日付要素の確認
                date_element = self.get_current_date()
                if date_element:
                    self.logger.info(f"日付要素確認OK: {date_element}")
                else:
                    self.logger.warning("日付要素が見つかりません")
                
                # フォーム要素の確認
                forms = self.driver.find_elements(By.TAG_NAME, "form")
                self.logger.info(f"フォーム要素数: {len(forms)}")
                
                # 入力要素の確認
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                self.logger.info(f"入力要素数: {len(inputs)}")
                
                # テーブル要素の確認
                tables = self.driver.find_elements(By.TAG_NAME, "table")
                self.logger.info(f"テーブル要素数: {len(tables)}")
                
            except Exception as e:
                self.logger.warning(f"要素確認中にエラー: {e}")
            
            # スクリーンショットを保存
            screenshot_path = self.save_screenshot("connection_verify")
            if screenshot_path:
                self.logger.info(f"接続確認スクリーンショット保存: {screenshot_path}")
            
            # 接続確認結果をログに記録
            self.logger.info("接続確認完了")
            return True
            
        except Exception as e:
            self.logger.error(f"接続確認エラー: {e}")
            return False
    
    def health_check(self) -> dict:
        """システムの健全性チェック"""
        try:
            self.logger.info("健全性チェックを開始します")
            
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'driver_status': False,
                'page_loaded': False,
                'page_title': '',
                'current_url': '',
                'form_elements': 0,
                'input_elements': 0,
                'errors': []
            }
            
            # ドライバーの状態確認
            if hasattr(self, 'driver') and self.driver:
                health_status['driver_status'] = True
                
                try:
                    # ページ情報の取得
                    health_status['current_url'] = self.driver.current_url
                    health_status['page_title'] = self.driver.title
                    
                    # ページ読み込み状態の確認
                    ready_state = self.driver.execute_script("return document.readyState")
                    health_status['page_loaded'] = (ready_state == 'complete')
                    
                    # 要素数の確認
                    health_status['form_elements'] = len(self.driver.find_elements(By.TAG_NAME, "form"))
                    health_status['input_elements'] = len(self.driver.find_elements(By.TAG_NAME, "input"))
                    
                except Exception as e:
                    health_status['errors'].append(f"ページ情報取得エラー: {e}")
            else:
                health_status['errors'].append("ドライバーが初期化されていません")
            
            # 健全性チェック結果のログ出力
            self.logger.info(f"健全性チェック結果: {health_status}")
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"健全性チェックエラー: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'driver_status': False,
                'page_loaded': False,
                'errors': [f"健全性チェック実行エラー: {e}"]
            }
    
    def test_connection_with_curl(self, url: str = None) -> bool:
        """curlを使用した接続テスト"""
        try:
            import subprocess
            
            if not url:
                url = self.driver.current_url if hasattr(self, 'driver') else "https://www.google.com"
            
            self.logger.info(f"curl接続テストを実行: {url}")
            
            # curlコマンドを実行
            result = subprocess.run(
                ['curl', '-I', '-s', '-o', '/dev/null', '-w', '%{http_code}', url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                status_code = result.stdout.strip()
                self.logger.info(f"curl接続テスト成功: HTTP {status_code}")
                return status_code.startswith('2') or status_code.startswith('3')
            else:
                self.logger.error(f"curl接続テスト失敗: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("curl接続テストがタイムアウトしました")
            return False
        except FileNotFoundError:
            self.logger.warning("curlコマンドが見つかりません")
            return False
        except Exception as e:
            self.logger.error(f"curl接続テストエラー: {e}")
            return False
    
    def test_connection_with_wget(self, url: str = None) -> bool:
        """wgetを使用した接続テスト"""
        try:
            import subprocess
            
            if not url:
                url = self.driver.current_url if hasattr(self, 'driver') else "https://www.google.com"
            
            self.logger.info(f"wget接続テストを実行: {url}")
            
            # wgetコマンドを実行
            result = subprocess.run(
                ['wget', '--spider', '--quiet', url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info("wget接続テスト成功")
                return True
            else:
                self.logger.error(f"wget接続テスト失敗: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("wget接続テストがタイムアウトしました")
            return False
        except FileNotFoundError:
            self.logger.warning("wgetコマンドが見つかりません")
            return False
        except Exception as e:
            self.logger.error(f"wget接続テストエラー: {e}")
            return False
    
    def comprehensive_connection_test(self) -> dict:
        """包括的な接続テスト"""
        try:
            self.logger.info("包括的な接続テストを開始します")
            
            test_results = {
                'timestamp': datetime.now().isoformat(),
                'browser_connection': False,
                'curl_test': False,
                'wget_test': False,
                'health_check': {},
                'overall_status': 'FAILED'
            }
            
            # 1. ブラウザ接続確認
            test_results['browser_connection'] = self.verify_connection()
            
            # 2. 健全性チェック
            test_results['health_check'] = self.health_check()
            
            # 3. curl接続テスト
            test_results['curl_test'] = self.test_connection_with_curl()
            
            # 4. wget接続テスト
            test_results['wget_test'] = self.test_connection_with_wget()
            
            # 総合結果の判定
            if test_results['browser_connection'] and (test_results['curl_test'] or test_results['wget_test']):
                test_results['overall_status'] = 'PASSED'
            elif test_results['browser_connection']:
                test_results['overall_status'] = 'PARTIAL'
            else:
                test_results['overall_status'] = 'FAILED'
            
            # 結果をログに記録
            self.logger.info(f"包括的な接続テスト完了: {test_results['overall_status']}")
            
            return test_results
            
        except Exception as e:
            self.logger.error(f"包括的な接続テストエラー: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'browser_connection': False,
                'curl_test': False,
                'wget_test': False,
                'health_check': {},
                'overall_status': 'ERROR',
                'error': str(e)
            }
    
    def _check_and_adjust_end_time(self) -> bool:
        """画面の終了時間を読み取って22:00より大きい場合は22:00に調整（深夜勤務申請エラー対策）"""
        try:
            self.logger.info("画面の終了時間をチェックして必要に応じて調整します（深夜勤務申請エラー対策）")
            
            # 終了時間フィールドを取得
            end_time_element = self._get_end_time_element()
            if not end_time_element:
                self.logger.warning("終了時間フィールドが見つかりません")
                return False
            
            # 現在の値を取得
            current_end_time = end_time_element.get_attribute('value')
            if not current_end_time:
                self.logger.warning("終了時間の値が空です")
                return False
            
            self.logger.info(f"画面の現在の終了時間: {current_end_time}")
            
            # 22:00チェック（深夜勤務申請エラー対策）
            if self._is_time_greater_than_threshold(current_end_time, "22:00"):
                self.logger.info(f"終了時間 {current_end_time} が22:00より大きいため深夜勤務申請エラー対策として22:00に調整します")
                
                # 22:00に変更
                try:
                    end_time_element.clear()
                    end_time_element.send_keys("22:00")
                except Exception as clear_e:
                    self.logger.warning(f"clear()失敗、代替方法を使用: {clear_e}")
                    # 全選択して削除
                    from selenium.webdriver.common.keys import Keys
                    end_time_element.send_keys(Keys.CONTROL + "a")
                    end_time_element.send_keys("22:00")
                
                # 変更後の値を確認
                new_value = end_time_element.get_attribute('value')
                self.logger.info(f"深夜勤務申請エラー対策で終了時間を修正: {current_end_time} → {new_value}")
                return True
            else:
                self.logger.info(f"終了時間 {current_end_time} は22:00以下のため調整不要")
                return True
                
        except Exception as e:
            self.logger.error(f"終了時間チェック・調整エラー: {e}")
            self.save_screenshot("end_time_adjustment_error")
            return False
    
    def _get_end_time_element(self):
        """終了時間入力フィールドを取得"""
        try:
            # 複数のパターンで終了時間フィールドを検索
            field_patterns = [
                ("name", "KNMTMRNGETDI"),
                ("name", "end_time"),
                ("css", "input[name*='ETDI']"),
                ("css", "input[name*='end']"),
                ("xpath", "//input[contains(@name, 'ETDI')]"),
                ("xpath", "//input[contains(@name, 'end')]")
            ]
            
            for pattern_type, pattern_value in field_patterns:
                try:
                    if pattern_type == "name":
                        element = self.driver.find_element(By.NAME, pattern_value)
                    elif pattern_type == "css":
                        element = self.driver.find_element(By.CSS_SELECTOR, pattern_value)
                    elif pattern_type == "xpath":
                        element = self.driver.find_element(By.XPATH, pattern_value)
                    
                    if element and element.is_displayed():
                        self.logger.info(f"終了時間フィールドを発見: {pattern_type}='{pattern_value}'")
                        return element
                        
                except Exception:
                    continue
            
            self.logger.error("終了時間フィールドが見つかりませんでした")
            return None
            
        except Exception as e:
            self.logger.error(f"終了時間フィールド取得エラー: {e}")
            return None
    
    def _is_time_greater_than_threshold(self, time_str: str, threshold: str) -> bool:
        """時刻文字列が閾値より大きいかをチェック"""
        try:
            def time_to_minutes(time_str):
                parts = time_str.split(':')
                if len(parts) != 2:
                    return 0
                hour = int(parts[0])
                minute = int(parts[1])
                return hour * 60 + minute
            
            time_minutes = time_to_minutes(time_str)
            threshold_minutes = time_to_minutes(threshold)
            
            return time_minutes > threshold_minutes
            
        except Exception as e:
            self.logger.error(f"時刻比較エラー: {e}")
            return False
    
    def _find_project_time_cell(self, project_index: int):
        """プロジェクト時間入力セルを複数のパターンで検索"""
        try:
            row_number = project_index + 1
            self.logger.info(f"プロジェクト行{row_number}の時間入力セルを検索中")
            
            # 複数のセレクタパターンを試行
            cell_selectors = [
                # 従来のパターン
                f".slick-row:nth-child({row_number}) .l2.r2",
                # 時間列を直接指定
                f".slick-row:nth-child({row_number}) .slick-cell.l2",
                f".slick-row:nth-child({row_number}) .slick-cell.r2",
                # 時間入力の一般的なパターン
                f".slick-row:nth-child({row_number}) .time-cell",
                f".slick-row:nth-child({row_number}) .work-time",
                # データ列インデックスベース（カラム2が時間列と仮定）
                f".slick-row:nth-child({row_number}) [data-column='2']",
                f".slick-row:nth-child({row_number}) .c2",
                # その他のパターン
                f".slick-row:nth-child({row_number}) .slick-cell:nth-child(3)",
            ]
            
            for selector in cell_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.logger.info(f"時間入力セル発見: {selector}")
                            self.logger.info(f"セル内容: '{element.text}'")
                            self.logger.info(f"セルクラス: {element.get_attribute('class')}")
                            return element
                except Exception as e:
                    self.logger.debug(f"セレクタ {selector} での検索失敗: {e}")
                    continue
            
            # 最後の手段: プロジェクトグリッド内の全セルを調査
            self.logger.warning("標準セレクタで見つからない場合の詳細調査")
            try:
                row_element = self.driver.find_element(By.CSS_SELECTOR, f".slick-row:nth-child({row_number})")
                cells = row_element.find_elements(By.CSS_SELECTOR, ".slick-cell")
                
                self.logger.info(f"行{row_number}のセル情報:")
                for i, cell in enumerate(cells):
                    cell_text = cell.text or "（空）"
                    cell_class = cell.get_attribute("class") or "（クラスなし）"
                    self.logger.info(f"  セル{i}: '{cell_text}' | クラス: {cell_class}")
                
                # 時間らしいセルを探す（例：数字:数字のパターンや空のセル）
                for i, cell in enumerate(cells):
                    cell_text = cell.text.strip()
                    # 時間パターンまたは空のセルを時間入力候補とする
                    if (not cell_text or 
                        ":" in cell_text or 
                        cell_text.replace(":", "").replace(".", "").isdigit()):
                        self.logger.info(f"時間入力候補セルを発見（セル{i}）: '{cell_text}'")
                        return cell
                        
            except Exception as e:
                self.logger.error(f"詳細調査でもエラー: {e}")
            
            self.logger.error(f"プロジェクト行{row_number}の時間入力セルが見つかりませんでした")
            return None
            
        except Exception as e:
            self.logger.error(f"時間入力セル検索エラー: {e}")
            return None
    
    def get_actual_work_time_from_screen(self) -> dict:
        """画面から実際の就業時間を取得して実働時間を計算"""
        try:
            self.logger.info("画面から就業時間を読み取って実働時間を計算します")
            
            # 開始時間と終了時間を取得
            start_time = self._get_start_time_from_screen()
            end_time = self._get_end_time_from_screen()
            
            if not start_time or not end_time:
                self.logger.error("開始時間または終了時間の取得に失敗")
                return {'success': False, 'actual_work_minutes': 480}  # デフォルト8時間
            
            self.logger.info(f"画面から取得した勤務時間: {start_time} - {end_time}")
            
            # 総労働時間を計算
            total_work_minutes = self._calculate_work_duration(start_time, end_time)
            
            # 休憩時間を取得
            break_minutes = self._get_break_time_from_screen()
            
            # 実働時間を計算
            actual_work_minutes = total_work_minutes - break_minutes
            
            self.logger.info(f"総労働時間: {total_work_minutes}分 ({total_work_minutes//60}:{total_work_minutes%60:02d})")
            self.logger.info(f"休憩時間: {break_minutes}分 ({break_minutes//60}:{break_minutes%60:02d})")
            self.logger.info(f"実働時間: {actual_work_minutes}分 ({actual_work_minutes//60}:{actual_work_minutes%60:02d})")
            
            return {
                'success': True,
                'start_time': start_time,
                'end_time': end_time,
                'total_work_minutes': total_work_minutes,
                'break_minutes': break_minutes,
                'actual_work_minutes': actual_work_minutes
            }
            
        except Exception as e:
            self.logger.error(f"画面からの就業時間取得エラー: {e}")
            return {'success': False, 'actual_work_minutes': 480}  # デフォルト8時間
    
    def _get_start_time_from_screen(self) -> str:
        """画面から開始時間を取得"""
        try:
            # 開始時間フィールドを検索
            start_time_patterns = [
                ("name", "KNMTMRNGSTDI"),
                ("name", "start_time"),
                ("css", "input[name*='STDI']"),
                ("css", "input[name*='start']"),
                ("xpath", "//input[contains(@name, 'STDI')]"),
                ("xpath", "//input[contains(@name, 'start')]")
            ]
            
            for pattern_type, pattern_value in start_time_patterns:
                try:
                    if pattern_type == "name":
                        element = self.driver.find_element(By.NAME, pattern_value)
                    elif pattern_type == "css":
                        element = self.driver.find_element(By.CSS_SELECTOR, pattern_value)
                    elif pattern_type == "xpath":
                        element = self.driver.find_element(By.XPATH, pattern_value)
                    
                    if element and element.is_displayed():
                        start_time = element.get_attribute('value')
                        if start_time:
                            self.logger.info(f"開始時間フィールド発見: {pattern_type}='{pattern_value}', 値='{start_time}'")
                            return start_time
                        
                except Exception:
                    continue
            
            self.logger.error("開始時間フィールドが見つかりませんでした")
            return None
            
        except Exception as e:
            self.logger.error(f"開始時間取得エラー: {e}")
            return None
    
    def _get_end_time_from_screen(self) -> str:
        """画面から終了時間を取得（既存の_get_end_time_elementを活用）"""
        try:
            element = self._get_end_time_element()
            if element:
                end_time = element.get_attribute('value')
                if end_time:
                    self.logger.info(f"終了時間取得成功: '{end_time}'")
                    return end_time
            
            self.logger.error("終了時間の取得に失敗")
            return None
            
        except Exception as e:
            self.logger.error(f"終了時間取得エラー: {e}")
            return None
    
    def _calculate_work_duration(self, start_time: str, end_time: str) -> int:
        """開始時間と終了時間から総労働時間（分）を計算"""
        try:
            def time_to_minutes(time_str):
                parts = time_str.split(':')
                if len(parts) != 2:
                    return 0
                hour = int(parts[0])
                minute = int(parts[1])
                return hour * 60 + minute
            
            start_minutes = time_to_minutes(start_time)
            end_minutes = time_to_minutes(end_time)
            
            # 終了時間が開始時間より小さい場合（日をまたぐ場合）は24時間加算
            if end_minutes < start_minutes:
                end_minutes += 24 * 60
            
            duration = end_minutes - start_minutes
            return duration
            
        except Exception as e:
            self.logger.error(f"労働時間計算エラー: {e}")
            return 480  # デフォルト8時間
    
    def _get_break_time_from_screen(self) -> int:
        """画面から休憩時間を取得して合計分数を計算"""
        try:
            total_break_minutes = 0
            
            # 複数の休憩時間パターンを検索
            for i in range(1, 6):  # 最大5つの休憩を検索
                try:
                    # 休憩開始時間
                    start_patterns = [
                        f"RCSST10_Seq{i-1}STH",  # 時
                        f"RCSST10_Seq{i-1}STM",  # 分
                        f"break{i}_start_hour",
                        f"break{i}_start_minute"
                    ]
                    
                    # 休憩終了時間
                    end_patterns = [
                        f"RCSST10_Seq{i-1}ETH",  # 時
                        f"RCSST10_Seq{i-1}ETM",  # 分
                        f"break{i}_end_hour",
                        f"break{i}_end_minute"
                    ]
                    
                    # 開始時・分を取得
                    start_hour_element = None
                    start_minute_element = None
                    for pattern in start_patterns:
                        try:
                            if "STH" in pattern or "hour" in pattern:
                                start_hour_element = self.driver.find_element(By.NAME, pattern)
                            elif "STM" in pattern or "minute" in pattern:
                                start_minute_element = self.driver.find_element(By.NAME, pattern)
                        except:
                            continue
                    
                    # 終了時・分を取得
                    end_hour_element = None
                    end_minute_element = None
                    for pattern in end_patterns:
                        try:
                            if "ETH" in pattern or "hour" in pattern:
                                end_hour_element = self.driver.find_element(By.NAME, pattern)
                            elif "ETM" in pattern or "minute" in pattern:
                                end_minute_element = self.driver.find_element(By.NAME, pattern)
                        except:
                            continue
                    
                    # 休憩時間を計算
                    if (start_hour_element and start_minute_element and 
                        end_hour_element and end_minute_element):
                        
                        start_hour = start_hour_element.get_attribute('value') or "0"
                        start_minute = start_minute_element.get_attribute('value') or "0"
                        end_hour = end_hour_element.get_attribute('value') or "0"
                        end_minute = end_minute_element.get_attribute('value') or "0"
                        
                        if (start_hour.isdigit() and start_minute.isdigit() and 
                            end_hour.isdigit() and end_minute.isdigit() and
                            (int(start_hour) > 0 or int(start_minute) > 0 or 
                             int(end_hour) > 0 or int(end_minute) > 0)):
                            
                            start_total = int(start_hour) * 60 + int(start_minute)
                            end_total = int(end_hour) * 60 + int(end_minute)
                            break_duration = end_total - start_total
                            
                            if break_duration > 0:
                                total_break_minutes += break_duration
                                self.logger.info(f"休憩{i}: {start_hour}:{start_minute:>02s} - {end_hour}:{end_minute:>02s} = {break_duration}分")
                    
                except Exception:
                    continue
            
            self.logger.info(f"総休憩時間: {total_break_minutes}分")
            return total_break_minutes
            
        except Exception as e:
            self.logger.error(f"休憩時間取得エラー: {e}")
            return 60  # デフォルト1時間
    
    def check_and_handle_night_work_error(self) -> bool:
        """深夜勤務申請エラーをチェックして自動修正"""
        try:
            self.logger.info("深夜勤務申請エラーをチェック中")
            
            # エラーメッセージを検索
            night_work_error = self._detect_night_work_error()
            
            if night_work_error:
                self.logger.warning("深夜勤務申請エラーが検出されました。終了時間を22:00に自動調整します")
                
                # 終了時間を22:00に強制修正
                success = self._force_adjust_end_time_to_22_00()
                
                if success:
                    self.logger.info("深夜勤務申請エラー対策として終了時間を22:00に調整完了")
                    return True
                else:
                    self.logger.error("終了時間の調整に失敗")
                    return False
            else:
                self.logger.info("深夜勤務申請エラーは検出されませんでした")
                return True
                
        except Exception as e:
            self.logger.error(f"深夜勤務申請エラーチェック中にエラー: {e}")
            return False
    
    def _detect_night_work_error(self) -> bool:
        """深夜勤務申請エラーメッセージを検出"""
        try:
            # エラーメッセージのパターン
            error_patterns = [
                "深夜勤務申請が提出されていません",
                "深夜勤務申請",
                "業務上やむを得ない理由で勤務する場合",
                "night work application",
                "late night work"
            ]
            
            # エラーメッセージを含む可能性のある要素を検索
            error_selectors = [
                ".error",
                ".alert",
                ".warning", 
                ".message",
                ".notification",
                "[class*='error']",
                "[class*='alert']",
                "span[style*='color: red']",
                "div[style*='color: red']"
            ]
            
            for selector in error_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            element_text = element.text.strip()
                            if element_text:
                                # エラーパターンとマッチするかチェック
                                for pattern in error_patterns:
                                    if pattern in element_text:
                                        self.logger.warning(f"深夜勤務申請エラー検出: '{element_text}'")
                                        self.save_screenshot("night_work_error_detected")
                                        return True
                except Exception:
                    continue
            
            # ページ全体のテキストもチェック
            try:
                page_source = self.driver.page_source
                for pattern in error_patterns:
                    if pattern in page_source:
                        self.logger.warning(f"ページソースで深夜勤務申請エラー検出: パターン '{pattern}'")
                        return True
            except Exception:
                pass
            
            return False
            
        except Exception as e:
            self.logger.error(f"深夜勤務申請エラー検出中にエラー: {e}")
            return False
    
    def _force_adjust_end_time_to_22_00(self) -> bool:
        """終了時間を強制的に22:00に調整"""
        try:
            self.logger.info("終了時間を強制的に22:00に調整中")
            
            # 終了時間フィールドを取得
            end_time_element = self._get_end_time_element()
            if not end_time_element:
                self.logger.error("終了時間フィールドが見つかりません")
                return False
            
            # 現在の値を記録
            current_value = end_time_element.get_attribute('value') or "不明"
            
            # 22:00に強制変更
            try:
                end_time_element.clear()
                end_time_element.send_keys("22:00")
                success = True
                self.logger.info("終了時間を22:00に変更完了")
            except Exception as input_e:
                self.logger.warning(f"clear()失敗、代替方法を使用: {input_e}")
                try:
                    # 全選択して削除
                    from selenium.webdriver.common.keys import Keys
                    end_time_element.send_keys(Keys.CONTROL + "a")
                    end_time_element.send_keys("22:00")
                    success = True
                    self.logger.info("代替方法で終了時間を22:00に変更完了")
                except Exception as alt_e:
                    self.logger.error(f"代替方法も失敗: {alt_e}")
                    success = False
            
            if success:
                # 変更後の値を確認
                new_value = end_time_element.get_attribute('value')
                self.logger.info(f"深夜勤務申請エラー対策完了: {current_value} → {new_value}")
                
                # 再計算を実行（必要に応じて）
                try:
                    self.calculate()
                except Exception as calc_e:
                    self.logger.warning(f"再計算でエラー: {calc_e}")
                
                return True
            else:
                self.logger.error("終了時間の変更に失敗")
                return False
                
        except Exception as e:
            self.logger.error(f"終了時間強制調整中にエラー: {e}")
            self.save_screenshot("force_adjust_end_time_error")
            return False

    def close(self):
        """ブラウザを閉じる"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.logger.info("ブラウザを閉じました")