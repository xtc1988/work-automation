"""
CSV処理クラス
"""
import pandas as pd
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import re


class WorkDataCSVProcessor:
    """CSVファイルから工数データを処理するクラス"""
    
    def __init__(self, csv_file_path: str):
        """
        CSVファイルパスを受け取り、初期化
        
        Args:
            csv_file_path: CSVファイルのパス
        """
        self.csv_file_path = csv_file_path
        self.data = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def load_csv_data(self) -> bool:
        """CSVファイルを読み込み"""
        try:
            # 複数のエンコーディングを試行
            encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932']
            
            for encoding in encodings:
                try:
                    self.data = pd.read_csv(self.csv_file_path, encoding=encoding)
                    self.logger.info(f"CSVファイル読み込み成功: {self.csv_file_path} (エンコーディング: {encoding})")
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if self.data is None:
                self.logger.error("CSVファイルの読み込みに失敗しました（全エンコーディングで失敗）")
                return False
            
            # 空行を削除
            self.data = self.data.dropna(how='all')
            
            # 日付列を確認
            if '日付' not in self.data.columns:
                self.logger.error("日付列が見つかりません")
                return False
                
            self.logger.info(f"読み込み完了: {len(self.data)}行")
            return True
            
        except Exception as e:
            self.logger.error(f"CSVファイル読み込みエラー: {e}")
            return False
    
    def validate_data(self) -> bool:
        """データの検証"""
        if self.data is None:
            self.logger.error("データが読み込まれていません")
            return False
        
        errors = []
        
        for idx, row in self.data.iterrows():
            row_errors = self._validate_row(idx, row)
            errors.extend(row_errors)
        
        if errors:
            self.logger.error(f"データ検証エラー: {len(errors)}件")
            for error in errors:
                self.logger.error(f"  - {error}")
            return False
        
        self.logger.info("データ検証完了: エラーなし")
        return True
    
    def _validate_row(self, idx: int, row: pd.Series) -> List[str]:
        """行データの検証"""
        errors = []
        row_num = idx + 2  # ヘッダー行を考慮
        
        # 必須フィールドチェック
        required_fields = ['日付', '開始時刻', '終了時刻', '在宅/出社区分']
        for field in required_fields:
            if pd.isna(row.get(field)) or str(row.get(field)).strip() == '':
                errors.append(f"行{row_num}: {field}が入力されていません")
        
        # 日付フォーマット検証
        if not pd.isna(row.get('日付')):
            if not self._validate_date_format(str(row['日付'])):
                errors.append(f"行{row_num}: 日付形式が正しくありません（YYYY-MM-DD形式で入力）")
        
        # 時刻フォーマット検証
        time_fields = ['開始時刻', '終了時刻']
        for field in time_fields:
            if not pd.isna(row.get(field)):
                if not self._validate_time_format(str(row[field])):
                    errors.append(f"行{row_num}: {field}の形式が正しくありません（HH:MM形式で入力）")
        
        # 在宅/出社区分の値チェック
        if not pd.isna(row.get('在宅/出社区分')):
            valid_locations = ['在宅', '出社（通勤費往復）', '出社（通勤費片道）', '出社（通勤費なし）', 'その他']
            if str(row['在宅/出社区分']).strip() not in valid_locations:
                errors.append(f"行{row_num}: 在宅/出社区分の値が正しくありません")
        
        # 休憩時間の検証
        break_fields = [col for col in row.index if col.startswith('休憩') and ('開始' in col or '終了' in col)]
        for field in break_fields:
            if not pd.isna(row.get(field)) and str(row[field]).strip() != '':
                if not self._validate_time_format(str(row[field])):
                    errors.append(f"行{row_num}: {field}の形式が正しくありません（HH:MM形式で入力）")
        
        # プロジェクト時間の検証
        project_time_fields = [col for col in row.index if col.startswith('プロジェクト') and '時間' in col]
        for field in project_time_fields:
            if not pd.isna(row.get(field)) and str(row[field]).strip() != '':
                if not self._validate_project_time_format(str(row[field])):
                    errors.append(f"行{row_num}: {field}の形式が正しくありません（H:MM形式または%形式で入力）")
        
        # 論理チェック（開始時刻 < 終了時刻）
        if (not pd.isna(row.get('開始時刻')) and not pd.isna(row.get('終了時刻')) and
            self._validate_time_format(str(row['開始時刻'])) and self._validate_time_format(str(row['終了時刻']))):
            
            start_time = self._parse_time(str(row['開始時刻']))
            end_time = self._parse_time(str(row['終了時刻']))
            
            if start_time >= end_time:
                errors.append(f"行{row_num}: 開始時刻が終了時刻以降になっています")
        
        return errors
    
    def _validate_date_format(self, date_str: str) -> bool:
        """日付フォーマットの検証"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    def _validate_time_format(self, time_str: str) -> bool:
        """時刻フォーマットの検証（HH:MM）"""
        pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        return bool(re.match(pattern, time_str.strip()))
    
    def _validate_project_time_format(self, time_str: str) -> bool:
        """プロジェクト時間フォーマットの検証（H:MMまたは割合%）"""
        time_str = time_str.strip()
        
        # H:MM形式のチェック
        time_pattern = r'^([0-9]|[0-9][0-9]):[0-5][0-9]$'
        if re.match(time_pattern, time_str):
            return True
        
        # 割合（%）形式のチェック (例: 50%, 100%, 12.5%)
        percentage_pattern = r'^\d+(\.\d+)?%$'
        if re.match(percentage_pattern, time_str):
            # 0%より大きく100%以下であることを確認
            percentage_value = float(time_str.rstrip('%'))
            return 0 < percentage_value <= 100
        
        return False
    
    def _parse_time(self, time_str: str) -> int:
        """時刻文字列を分数に変換"""
        hour, minute = map(int, time_str.split(':'))
        return hour * 60 + minute
    
    def _convert_project_time(self, time_str: str, total_work_minutes: int = None) -> str:
        """プロジェクト時間を標準形式（H:MM）に変換
        
        Args:
            time_str: 時間文字列（H:MM形式または%形式）
            total_work_minutes: 総労働時間（分）。割合計算に使用
            
        Returns:
            H:MM形式の時間文字列
        """
        time_str = time_str.strip()
        
        # すでにH:MM形式の場合はそのまま返す
        if ':' in time_str:
            return time_str
        
        # %形式の場合はそのまま返す（BulkWorkAutomationでパーセンテージ処理を行うため）
        if time_str.endswith('%'):
            return time_str
        
        return time_str
    
    def get_work_data_by_date(self, date: str) -> Optional[Dict[str, Any]]:
        """指定日の工数データを取得"""
        if self.data is None:
            return None
        
        matching_rows = self.data[self.data['日付'] == date]
        
        if len(matching_rows) == 0:
            return None
        
        row = matching_rows.iloc[0]
        return self._convert_row_to_work_data(row)
    
    def get_date_range_data(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """日付範囲のデータを取得"""
        if self.data is None:
            return []
        
        filtered_data = self.data
        
        if start_date:
            filtered_data = filtered_data[filtered_data['日付'] >= start_date]
        
        if end_date:
            filtered_data = filtered_data[filtered_data['日付'] <= end_date]
        
        result = []
        for _, row in filtered_data.iterrows():
            work_data = self._convert_row_to_work_data(row)
            result.append(work_data)
        
        return result
    
    def get_all_data(self) -> List[Dict[str, Any]]:
        """全データを取得"""
        if self.data is None:
            return []
        
        result = []
        for _, row in self.data.iterrows():
            work_data = self._convert_row_to_work_data(row)
            result.append(work_data)
        
        return result
    
    def _convert_row_to_work_data(self, row: pd.Series) -> Dict[str, Any]:
        """CSV行から内部辞書形式への変換"""
        # 終了時刻の調整処理
        end_time = str(row['終了時刻'])
        if self._validate_time_format(end_time):
            end_minutes = self._parse_time(end_time)
            # 22:15より大きい場合は22:00に修正
            if end_minutes > self._parse_time("22:15"):
                original_time = end_time
                end_time = "22:00"
                self.logger.info(f"終了時刻を修正: {original_time} → {end_time} (日付: {row['日付']})")
        
        work_data = {
            'date': str(row['日付']),
            'start_time': str(row['開始時刻']),
            'end_time': end_time,
            'location_type': str(row['在宅/出社区分']),
            'break_times': [],
            'projects': []
        }
        
        # 総労働時間を計算（割合計算用）
        total_work_minutes = None
        if (not pd.isna(row.get('開始時刻')) and self._validate_time_format(str(row['開始時刻'])) and
            self._validate_time_format(end_time)):
            start_minutes = self._parse_time(str(row['開始時刻']))
            end_minutes = self._parse_time(end_time)  # 修正後の終了時刻を使用
            total_work_minutes = end_minutes - start_minutes
        
        # 休憩時間の動的取得と合計計算
        break_start_cols = [col for col in row.index if col.startswith('休憩') and '開始' in col]
        break_end_cols = [col for col in row.index if col.startswith('休憩') and '終了' in col]
        
        total_break_minutes = 0
        for start_col, end_col in zip(sorted(break_start_cols), sorted(break_end_cols)):
            start_time = row.get(start_col)
            end_time = row.get(end_col)
            
            if (not pd.isna(start_time) and not pd.isna(end_time) and
                str(start_time).strip() != '' and str(end_time).strip() != ''):
                work_data['break_times'].append((str(start_time), str(end_time)))
                
                # 休憩時間を分単位で計算
                if self._validate_time_format(str(start_time)) and self._validate_time_format(str(end_time)):
                    break_start_minutes = self._parse_time(str(start_time))
                    break_end_minutes = self._parse_time(str(end_time))
                    total_break_minutes += (break_end_minutes - break_start_minutes)
        
        # 実労働時間を計算（総労働時間 - 休憩時間）
        actual_work_minutes = None
        if total_work_minutes is not None:
            actual_work_minutes = total_work_minutes - total_break_minutes
            self.logger.debug(f"総労働時間: {total_work_minutes}分, 休憩時間: {total_break_minutes}分, 実労働時間: {actual_work_minutes}分")
        
        # プロジェクトの動的取得
        project_time_cols = [col for col in row.index if col.startswith('プロジェクト') and '時間' in col]
        project_comment_cols = [col for col in row.index if col.startswith('プロジェクト') and '備考' in col]
        
        for time_col in sorted(project_time_cols):
            time_value = row.get(time_col)
            
            if not pd.isna(time_value) and str(time_value).strip() != '':
                # 対応する備考列を探す
                project_num = time_col.split('プロジェクト')[1].split('_')[0]
                comment_col = f'プロジェクト{project_num}_備考'
                comment_value = row.get(comment_col, '')
                
                if pd.isna(comment_value):
                    comment_value = ''
                
                # 時間を標準形式に変換（%形式の場合はH:MM形式に変換）
                # 実労働時間を基準に使用
                converted_time = self._convert_project_time(str(time_value), actual_work_minutes)
                
                work_data['projects'].append({
                    'time': converted_time,
                    'comment': str(comment_value)
                })
        
        return work_data
    
    def show_data_summary(self):
        """データサマリーを表示"""
        if self.data is None:
            self.logger.error("データが読み込まれていません")
            return
        
        print("\n=== データサマリー ===")
        print(f"総行数: {len(self.data)}行")
        
        # 日付範囲
        if not self.data.empty:
            dates = pd.to_datetime(self.data['日付'])
            print(f"日付範囲: {dates.min().strftime('%Y-%m-%d')} ～ {dates.max().strftime('%Y-%m-%d')}")
        
        # 在宅/出社区分の集計
        location_counts = self.data['在宅/出社区分'].value_counts()
        print("\n在宅/出社区分の内訳:")
        for location, count in location_counts.items():
            print(f"  {location}: {count}日")
        
        # プロジェクト作業がある日数
        project_cols = [col for col in self.data.columns if col.startswith('プロジェクト') and '時間' in col]
        project_days = 0
        for _, row in self.data.iterrows():
            has_project = any(not pd.isna(row.get(col)) and str(row.get(col)).strip() != '' for col in project_cols)
            if has_project:
                project_days += 1
        
        print(f"\nプロジェクト作業がある日数: {project_days}日")
        
        print("=" * 30)
    
    def save_validation_report(self, output_file: str = None) -> str:
        """検証レポートをファイルに保存"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"validation_report_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== データ検証レポート ===\n")
            f.write(f"CSVファイル: {self.csv_file_path}\n")
            f.write(f"検証日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if self.data is not None:
                f.write(f"総行数: {len(self.data)}行\n")
                
                # 各行の検証結果
                for idx, row in self.data.iterrows():
                    errors = self._validate_row(idx, row)
                    if errors:
                        f.write(f"\n行{idx + 2}のエラー:\n")
                        for error in errors:
                            f.write(f"  - {error}\n")
                
                f.write("\n=== 検証完了 ===\n")
        
        self.logger.info(f"検証レポートを保存しました: {output_file}")
        return output_file