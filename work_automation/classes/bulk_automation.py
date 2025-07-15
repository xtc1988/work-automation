"""
一括処理クラス
"""
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import csv
from pathlib import Path

from .work_time_automation import WorkTimeAutomation
from .csv_processor import WorkDataCSVProcessor


class BulkWorkAutomation:
    """CSV データを使用した一括処理クラス"""
    
    def __init__(self, automation: WorkTimeAutomation, csv_processor: WorkDataCSVProcessor):
        """
        初期化
        
        Args:
            automation: WorkTimeAutomation インスタンス
            csv_processor: WorkDataCSVProcessor インスタンス
        """
        self.automation = automation
        self.csv_processor = csv_processor
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 処理結果を記録
        self.results = []
        
        # 設定
        self.max_retries = 3  # 最大リトライ回数
        
        # セッション安定化設定
        self.session_refresh_interval = 5  # N日毎にセッションリフレッシュ
        self.error_recovery_enabled = True  # エラー自動回復
        self.processed_count = 0  # 処理済み件数のカウンタ
    
    def process_all_data(self, dry_run: bool = False) -> bool:
        """
        全データを一括処理
        
        Args:
            dry_run: True の場合、実際の入力を行わない
            
        Returns:
            bool: 全処理が成功した場合 True
        """
        self.logger.info("一括処理を開始します")
        
        # 全データを取得
        all_data = self.csv_processor.get_all_data()
        
        if not all_data:
            self.logger.error("処理するデータがありません")
            return False
        
        self.logger.info(f"処理対象: {len(all_data)}日分")
        
        success_count = 0
        
        for idx, work_data in enumerate(all_data, 1):
            self.logger.info(f"=== {idx}/{len(all_data)} 日目: {work_data['date']} ===")
            
            if dry_run:
                self.logger.info(f"ドライラン: {work_data['date']} のデータを確認")
                self._log_work_data(work_data)
                
                # ドライラン結果を記録
                self.results.append({
                    'date': work_data['date'],
                    'status': 'dry_run',
                    'message': 'ドライラン実行',
                    'timestamp': datetime.now()
                })
                
                success_count += 1
                continue
            
            # セッション安定化チェック
            if self._should_refresh_session(idx):
                self._refresh_session()
            
            # 単日処理を実行（エラー回復付き）
            success = self._process_single_day_with_recovery(work_data)
            
            if success:
                success_count += 1
                self.processed_count += 1
                self.logger.info(f"✓ {work_data['date']} の処理が完了しました")
            else:
                self.logger.error(f"✗ {work_data['date']} の処理に失敗しました")
                
                # エラー後の回復処理
                if self.error_recovery_enabled:
                    self._perform_error_recovery()
            
            # 最後の日でない場合、次の日に遷移
            if idx < len(all_data):
                self.logger.info("次の日に遷移します")
                
                # 日付遷移は自動化クラスで行う（要素ベース待機）
                if not self._navigate_to_next_day_with_element_wait():
                    self.logger.error("日付遷移に失敗しました")
                    break
        
        # 処理結果のサマリー
        self.logger.info(f"一括処理完了: {success_count}/{len(all_data)} 件成功")
        
        return success_count == len(all_data)
    
    def process_single_day(self, work_data: Dict[str, Any]) -> bool:
        """
        単日の処理
        
        Args:
            work_data: 1日分の工数データ
            
        Returns:
            bool: 処理が成功した場合 True
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"日付 {work_data['date']} の処理を開始")
            
            # 1. 勤務時間入力
            if not self.automation.input_work_time(
                work_data['start_time'],
                work_data['end_time'], 
                work_data['location_type']
            ):
                self._record_failure(work_data['date'], "勤務時間入力に失敗")
                return False
            
            # 2. 休憩時間入力
            if work_data['break_times']:
                if not self.automation.input_break_time(work_data['break_times']):
                    self._record_failure(work_data['date'], "休憩時間入力に失敗")
                    return False
            
            # 3. 計算実行（プロジェクト入力前に実労働時間を計算）
            self.logger.info("プロジェクト入力前に計算を実行")
            if not self.automation.calculate():
                self._record_failure(work_data['date'], "計算処理に失敗")
                return False
            
            # 4. 画面から実労働時間を取得
            work_time_data = self.automation.get_actual_work_time_from_screen()
            if work_time_data['success']:
                actual_work_minutes = work_time_data['actual_work_minutes']
                actual_work_hours = f"{actual_work_minutes//60}:{actual_work_minutes%60:02d}"
                self.logger.info(f"画面から取得した実労働時間: {actual_work_hours}")
                
                # プロジェクト時間の調整が必要な場合
                if work_data['projects']:
                    self._adjust_project_hours(work_data['projects'], actual_work_hours)
            else:
                # フォールバック: 従来の方法
                actual_work_hours = self.automation.get_actual_work_hours()
                if actual_work_hours:
                    self.logger.info(f"フォールバック実労働時間: {actual_work_hours}")
                    
                    # プロジェクト時間の調整が必要な場合
                    if work_data['projects']:
                        self._adjust_project_hours(work_data['projects'], actual_work_hours)
            
            # 5. プロジェクト作業入力
            for idx, project in enumerate(work_data['projects']):
                if not self.automation.add_project_work(
                    idx, 
                    project['time'], 
                    project['comment']
                ):
                    self._record_failure(work_data['date'], f"プロジェクト{idx+1}入力に失敗")
                    return False
            
            # 6. 再度計算実行（プロジェクト入力後）
            if not self.automation.calculate():
                self._record_failure(work_data['date'], "計算処理に失敗")
                return False
            
            # 7. エラーチェックと深夜勤務申請エラー対策
            errors = self.automation.check_errors()
            if errors:
                # 深夜勤務申請エラーの自動修正を試行
                night_work_error_fixed = self.automation.check_and_handle_night_work_error()
                
                if night_work_error_fixed:
                    # 深夜勤務申請エラーが修正された場合、再度エラーチェック
                    self.logger.info("深夜勤務申請エラー修正後、再度エラーチェックを実行")
                    errors = self.automation.check_errors()
                
                if errors:
                    # エラーを記録（申請対象のみ）
                    self.automation.record_error_for_later_application(work_data['date'], errors)
                    
                    # 特定のエラー以外の場合はスキップ
                    if self.automation.should_skip_date_for_errors(errors):
                        error_msg = f"スキップ対象エラー: {', '.join(errors)}"
                        self.logger.warning(f"日付をスキップします: {work_data['date']} - {error_msg}")
                        self._record_failure(work_data['date'], f"スキップ - {error_msg}")
                        return True  # スキップとして成功扱い
                    else:
                        error_msg = f"エラー検出: {', '.join(errors)}"
                        self._record_failure(work_data['date'], error_msg)
                        return False
                else:
                    self.logger.info("深夜勤務申請エラー修正により、すべてのエラーが解決されました")
            else:
                # エラーがない場合でも予防的に深夜勤務申請エラーチェック
                self.automation.check_and_handle_night_work_error()
            
            # 8. 確認画面に遷移
            if not self.automation.save_and_next():
                self._record_failure(work_data['date'], "確認画面遷移に失敗")
                return False
            
            # 9. 確認画面での提出処理（常に提出）
            if not self.automation.submit_confirmation():
                self._record_failure(work_data['date'], "提出ボタンクリックに失敗")
                return False
            action = "提出完了"
            
            # 成功を記録
            self._record_success(work_data['date'], action, start_time)
            return True
            
        except Exception as e:
            self._record_failure(work_data['date'], f"予期しないエラー: {e}")
            return False
    
    def _record_success(self, date: str, message: str, start_time: datetime):
        """成功を記録"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        self.results.append({
            'date': date,
            'status': 'success',
            'message': message,
            'processing_time': processing_time,
            'timestamp': datetime.now()
        })
        
        self.logger.info(f"成功記録: {date} - {message} ({processing_time:.1f}秒)")
    
    def _record_failure(self, date: str, message: str):
        """失敗を記録"""
        self.results.append({
            'date': date,
            'status': 'failure',
            'message': message,
            'timestamp': datetime.now()
        })
        
        self.logger.error(f"失敗記録: {date} - {message}")
    
    def _log_work_data(self, work_data: Dict[str, Any]):
        """工数データの内容をログ出力"""
        self.logger.info(f"  開始時刻: {work_data['start_time']}")
        self.logger.info(f"  終了時刻: {work_data['end_time']}")
        self.logger.info(f"  在宅/出社: {work_data['location_type']}")
        
        if work_data['break_times']:
            self.logger.info(f"  休憩時間: {len(work_data['break_times'])}件")
            for idx, (start, end) in enumerate(work_data['break_times'], 1):
                self.logger.info(f"    休憩{idx}: {start} - {end}")
        
        if work_data['projects']:
            self.logger.info(f"  プロジェクト: {len(work_data['projects'])}件")
            for idx, project in enumerate(work_data['projects'], 1):
                self.logger.info(f"    プロジェクト{idx}: {project['time']} - {project['comment']}")
    
    def show_results_summary(self):
        """処理結果のサマリーを表示"""
        if not self.results:
            print("処理結果がありません")
            return
        
        print("\n=== 処理結果サマリー ===")
        
        # 成功/失敗の集計
        success_count = len([r for r in self.results if r['status'] == 'success'])
        failure_count = len([r for r in self.results if r['status'] == 'failure'])
        dry_run_count = len([r for r in self.results if r['status'] == 'dry_run'])
        
        print(f"総処理件数: {len(self.results)}件")
        print(f"成功: {success_count}件")
        print(f"失敗: {failure_count}件")
        if dry_run_count > 0:
            print(f"ドライラン: {dry_run_count}件")
        
        # 処理時間の統計
        processing_times = [r.get('processing_time', 0) for r in self.results if r.get('processing_time')]
        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            print(f"平均処理時間: {avg_time:.1f}秒")
        
        # 失敗した項目の表示
        failures = [r for r in self.results if r['status'] == 'failure']
        if failures:
            print("\n=== 失敗した項目 ===")
            for failure in failures:
                print(f"  {failure['date']}: {failure['message']}")
        
        print("=" * 30)
    
    def save_results_to_csv(self, output_file: str = None) -> str:
        """処理結果をCSVファイルに保存"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"work_result_{timestamp}.csv"
        
        # logsディレクトリに保存
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        output_path = log_dir / output_file
        
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['date', 'status', 'message', 'processing_time', 'timestamp']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in self.results:
                row = {
                    'date': result['date'],
                    'status': result['status'],
                    'message': result['message'],
                    'processing_time': result.get('processing_time', ''),
                    'timestamp': result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                }
                writer.writerow(row)
        
        self.logger.info(f"処理結果を保存しました: {output_path}")
        return str(output_path)
    
    def resume_from_date(self, resume_date: str) -> bool:
        """
        指定日からの処理を再開
        
        Args:
            resume_date: 再開する日付（YYYY-MM-DD）
            
        Returns:
            bool: 再開処理が成功した場合 True
        """
        self.logger.info(f"処理を再開します: {resume_date}から")
        
        # 既に処理済みの日付を取得
        processed_dates = {r['date'] for r in self.results if r['status'] == 'success'}
        
        # 指定日以降のデータを取得
        all_data = self.csv_processor.get_all_data()
        resume_data = [d for d in all_data if d['date'] >= resume_date and d['date'] not in processed_dates]
        
        if not resume_data:
            self.logger.info("再開するデータがありません")
            return True
        
        self.logger.info(f"再開対象: {len(resume_data)}日分")
        
        # 再開処理を実行
        for work_data in resume_data:
            success = self.process_single_day(work_data)
            
            if not success:
                self.logger.error(f"再開処理失敗: {work_data['date']}")
                return False
        
        self.logger.info("再開処理が完了しました")
        return True
    
    def get_failed_dates(self) -> List[str]:
        """失敗した日付のリストを取得"""
        return [r['date'] for r in self.results if r['status'] == 'failure']
    
    def retry_failed_dates(self) -> bool:
        """失敗した日付のリトライ処理"""
        failed_dates = self.get_failed_dates()
        
        if not failed_dates:
            self.logger.info("リトライする項目がありません")
            return True
        
        self.logger.info(f"リトライ処理開始: {len(failed_dates)}件")
        
        retry_success = 0
        
        for date in failed_dates:
            work_data = self.csv_processor.get_work_data_by_date(date)
            
            if work_data:
                self.logger.info(f"リトライ: {date}")
                
                # 失敗記録を一旦削除
                self.results = [r for r in self.results if not (r['date'] == date and r['status'] == 'failure')]
                
                # 再処理
                if self.process_single_day(work_data):
                    retry_success += 1
        
        self.logger.info(f"リトライ完了: {retry_success}/{len(failed_dates)} 件成功")
        return retry_success == len(failed_dates)
    
    def _adjust_project_hours(self, projects: List[Dict[str, str]], actual_work_hours: str):
        """プロジェクト時間をパーセンテージベースで実労働時間に合わせて調整"""
        try:
            # 画面から実際の実働時間を取得
            work_time_data = self.automation.get_actual_work_time_from_screen()
            
            if work_time_data['success']:
                total_work_minutes = work_time_data['actual_work_minutes']
                self.logger.info(f"画面から取得した実働時間を使用: {total_work_minutes}分 ({total_work_minutes//60}:{total_work_minutes%60:02d})")
            else:
                # フォールバック: CSV値を使用
                self.logger.warning("画面からの実働時間取得に失敗、CSV値を使用")
                if ':' in actual_work_hours:
                    hours, minutes = actual_work_hours.split(':')
                    total_work_minutes = int(hours) * 60 + int(minutes)
                else:
                    # H:MM形式でない場合は時間単位と仮定
                    total_work_minutes = int(float(actual_work_hours) * 60)
                self.logger.info(f"CSV値から計算した実働時間: {total_work_minutes}分")
            
            if total_work_minutes <= 0:
                self.logger.warning("実働時間が0以下です")
                return
            
            # CSVの値をパーセンテージとして扱い、100%を超えた分は0にする
            percentages = []
            cumulative_percentage = 0
            
            for i, project in enumerate(projects):
                if not project['time']:
                    percentages.append(0)
                    continue
                
                # CSVの値をパーセンテージとして解析
                try:
                    if ':' in project['time']:
                        # H:MM形式でもパーセンテージとして扱う（時間部分のみ使用）
                        percentage = float(project['time'].split(':')[0])
                    else:
                        # %記号を除去してから解析
                        percentage = float(project['time'].rstrip('%'))
                    
                    # 累積が100%を超えた場合は0にする
                    if cumulative_percentage + percentage > 100:
                        percentage = 0
                        self.logger.info(f"プロジェクト{i+1}: 累積100%超過のため0%に設定")
                    else:
                        cumulative_percentage += percentage
                        self.logger.info(f"プロジェクト{i+1}: {percentage}% (累積: {cumulative_percentage}%)")
                    
                    percentages.append(percentage)
                    
                except ValueError:
                    self.logger.warning(f"プロジェクト{i+1}の値を解析できません: {project['time']}")
                    percentages.append(0)
            
            # 各プロジェクトの時間を計算
            allocated_times = []
            total_allocated_minutes = 0
            
            for i, percentage in enumerate(percentages):
                if percentage > 0:
                    allocated_minutes = int(total_work_minutes * percentage / 100)
                else:
                    allocated_minutes = 0
                
                allocated_times.append(allocated_minutes)
                total_allocated_minutes += allocated_minutes
                
                self.logger.info(f"プロジェクト{i+1}: {percentage}% → {allocated_minutes}分")
            
            # 余り時間を最後の有効なプロジェクトに加算
            remainder = total_work_minutes - total_allocated_minutes
            if remainder != 0:
                # 最後の0でないプロジェクトを見つける
                last_valid_index = -1
                for i in range(len(allocated_times) - 1, -1, -1):
                    if allocated_times[i] > 0:
                        last_valid_index = i
                        break
                
                if last_valid_index >= 0:
                    allocated_times[last_valid_index] += remainder
                    self.logger.info(f"余り{remainder}分をプロジェクト{last_valid_index+1}に加算")
                elif remainder > 0:
                    # 全プロジェクトが0の場合、最初のプロジェクトに全時間を割り当て
                    if allocated_times:
                        allocated_times[0] = total_work_minutes
                        self.logger.info(f"全プロジェクトが0%のため、プロジェクト1に全時間{total_work_minutes}分を割り当て")
            
            # 検算
            final_total = sum(allocated_times)
            self.logger.info(f"検算: 実働時間{total_work_minutes}分 = 配分合計{final_total}分 (差: {final_total - total_work_minutes}分)")
            
            # プロジェクト時間を更新
            for i, allocated_minutes in enumerate(allocated_times):
                if i < len(projects):
                    allocated_hours = allocated_minutes // 60
                    allocated_mins = allocated_minutes % 60
                    projects[i]['time'] = f"{allocated_hours}:{allocated_mins:02d}"
                    self.logger.info(f"プロジェクト{i+1}最終時間: {projects[i]['time']}")
            
            self.logger.info(f"プロジェクト時間調整完了: 実労働={total_work_minutes}分を{len(projects)}個のプロジェクトに完全配分")
        
        except Exception as e:
            self.logger.error(f"プロジェクト時間調整エラー: {e}")

    def _should_refresh_session(self, current_index: int) -> bool:
        """セッションリフレッシュが必要かどうか判定"""
        return (current_index % self.session_refresh_interval) == 0

    def _refresh_session(self):
        """セッション状態をリフレッシュ（要素ベース）"""
        try:
            self.logger.info("セッション状態をリフレッシュします")
            
            # 1. ページをリフレッシュ
            self.automation.driver.refresh()
            
            # 2. ページ読み込み完了を待機
            self.automation.wait_for_page_load()
            
            # 3. 入力要素が利用可能になるまで待機
            self._wait_for_input_elements_ready()
            
            self.logger.info("セッションリフレッシュ完了")
            
        except Exception as e:
            self.logger.error(f"セッションリフレッシュエラー: {e}")

    def _process_single_day_with_recovery(self, work_data: Dict[str, Any]) -> bool:
        """エラー回復機能付きの単日処理"""
        max_attempts = 2
        
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    self.logger.info(f"処理再試行 {attempt + 1}/{max_attempts}: {work_data['date']}")
                    
                    # 再試行前の回復処理（要素ベース）
                    self._perform_error_recovery()
                
                # 通常の単日処理を実行
                return self.process_single_day(work_data)
                
            except Exception as e:
                self.logger.error(f"処理試行{attempt + 1}でエラー: {e}")
                
                if attempt < max_attempts - 1:
                    self.logger.info("エラー回復処理を実行して再試行します")
                    time.sleep(2 ** attempt)  # 指数バックオフ
                else:
                    self.logger.error(f"全ての試行が失敗しました: {work_data['date']}")
                    return False
        
        return False

    def _perform_error_recovery(self):
        """エラー発生後の回復処理（要素ベース）"""
        try:
            self.logger.info("エラー回復処理を開始")
            
            # 1. スクリーンショットを保存（現状確認）
            if hasattr(self.automation, 'save_screenshot'):
                self.automation.save_screenshot("error_recovery_before")
            
            # 2. ブラウザの状態をクリア
            self._clear_browser_state()
            
            # 3. ページを再読み込み
            self.automation.driver.refresh()
            self.automation.wait_for_page_load()
            
            # 4. 入力要素が準備完了まで待機
            self._wait_for_input_elements_ready()
            
            # 5. 回復後のスクリーンショット
            if hasattr(self.automation, 'save_screenshot'):
                self.automation.save_screenshot("error_recovery_after")
            
            self.logger.info("エラー回復処理完了")
            
        except Exception as e:
            self.logger.error(f"エラー回復処理でエラー: {e}")

    def _clear_browser_state(self):
        """ブラウザの状態をクリア"""
        try:
            # JavaScript実行でブラウザ状態をクリア
            clear_script = """
            // フォームをリセット
            var forms = document.querySelectorAll('form');
            for (var i = 0; i < forms.length; i++) {
                try {
                    forms[i].reset();
                } catch(e) {}
            }
            
            // アクティブな要素のフォーカスを解除
            if (document.activeElement) {
                document.activeElement.blur();
            }
            
            // エラー表示要素を非表示
            var errorElements = document.querySelectorAll('.error, .alert, .warning');
            for (var i = 0; i < errorElements.length; i++) {
                errorElements[i].style.display = 'none';
            }
            
            // オーバーレイを削除
            var overlays = document.querySelectorAll('[data-hidden-by-automation="true"]');
            for (var i = 0; i < overlays.length; i++) {
                overlays[i].style.display = '';
                overlays[i].removeAttribute('data-hidden-by-automation');
            }
            
            return true;
            """
            
            self.automation.driver.execute_script(clear_script)
            self.logger.debug("ブラウザ状態クリア完了")
            
        except Exception as e:
            self.logger.error(f"ブラウザ状態クリアエラー: {e}")

    def _navigate_to_next_day_with_element_wait(self) -> bool:
        """要素ベース待機付きの日付遷移"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.logger.info(f"日付遷移リトライ {attempt + 1}/{max_retries}")
                    
                    # リトライ前の回復処理（要素ベース）
                    self.automation.driver.refresh()
                    self.automation.wait_for_page_load()
                    self._wait_for_input_elements_ready()
                
                # 日付遷移を実行
                if self.automation.navigate_to_next_day():
                    # 遷移後、新しいページの入力要素が準備完了まで待機
                    if self._wait_for_input_elements_ready():
                        self.logger.info("日付遷移成功（入力要素準備完了）")
                        return True
                    else:
                        self.logger.warning("日付遷移後の要素準備が未完了")
                
            except Exception as e:
                self.logger.error(f"日付遷移試行{attempt + 1}でエラー: {e}")
        
        self.logger.error("全ての日付遷移試行が失敗しました")
        return False

    def _wait_for_input_elements_ready(self) -> bool:
        """入力要素が準備完了まで待機"""
        try:
            # 主要な入力要素パターンを定義
            element_patterns = [
                ("KNMTMRNGSTDI", "開始時刻"),
                ("KNMTMRNGETDI", "終了時刻"),
                ("GI_COMBOBOX38_Seq0S", "在宅出社区分")
            ]
            
            # いずれかの要素が見つかれば準備完了とみなす
            for field_name, description in element_patterns:
                try:
                    element = self.automation.wait_for_element(
                        self.automation.driver.find_element, 
                        field_name, 
                        timeout=10
                    )
                    if element:
                        self.logger.info(f"入力要素準備完了: {description} ({field_name})")
                        return True
                except:
                    continue
            
            # フォールバック: 任意のテキスト入力要素
            try:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                WebDriverWait(self.automation.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']:not([name='dummy'])"))
                )
                self.logger.info("入力要素準備完了（フォールバック）")
                return True
            except:
                pass
            
            self.logger.warning("入力要素の準備完了を確認できませんでした")
            return False
            
        except Exception as e:
            self.logger.error(f"入力要素待機エラー: {e}")
            return False