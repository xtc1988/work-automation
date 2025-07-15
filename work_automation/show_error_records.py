#!/usr/bin/env python3
"""
エラー記録を表示するスクリプト
"""
import os
import json
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))


def show_error_records():
    """エラー記録を表示"""
    error_records_dir = Path(__file__).parent / "logs" / "error_records"
    
    if not error_records_dir.exists():
        print("エラー記録ディレクトリが存在しません")
        return
    
    # 全てのエラー記録ファイルを取得
    error_files = sorted(error_records_dir.glob("*.json"))
    
    if not error_files:
        print("エラー記録はありません")
        return
    
    print("=== エラー記録一覧 ===\n")
    
    total_pending = 0
    total_applied = 0
    total_resolved = 0
    
    for error_file in error_files:
        date = error_file.stem
        
        try:
            with open(error_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            if not records:
                continue
            
            print(f"【{date}】")
            
            for record in records:
                timestamp = record.get('timestamp', 'Unknown')
                status = record.get('status', 'pending')
                errors = record.get('errors', [])
                
                status_mark = {
                    'pending': '⚠️ 未申請',
                    'applied': '📋 申請済',
                    'resolved': '✅ 解決済'
                }.get(status, status)
                
                print(f"  時刻: {timestamp}")
                print(f"  状態: {status_mark}")
                print(f"  エラー:")
                for error in errors:
                    print(f"    - {error}")
                print()
                
                # 統計
                if status == 'pending':
                    total_pending += 1
                elif status == 'applied':
                    total_applied += 1
                elif status == 'resolved':
                    total_resolved += 1
            
        except Exception as e:
            print(f"  エラー: ファイル読み込み失敗 - {e}")
    
    print("\n=== 統計 ===")
    print(f"未申請: {total_pending}件")
    print(f"申請済: {total_applied}件")
    print(f"解決済: {total_resolved}件")
    print(f"合計: {total_pending + total_applied + total_resolved}件")
    
    if total_pending > 0:
        print(f"\n⚠️ {total_pending}件の未申請エラーがあります")


def export_error_records_csv():
    """エラー記録をCSV形式でエクスポート"""
    import csv
    
    error_records_dir = Path(__file__).parent / "logs" / "error_records"
    output_file = Path(__file__).parent / "logs" / f"error_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    if not error_records_dir.exists():
        print("エラー記録ディレクトリが存在しません")
        return
    
    error_files = sorted(error_records_dir.glob("*.json"))
    
    if not error_files:
        print("エラー記録はありません")
        return
    
    rows = []
    
    for error_file in error_files:
        date = error_file.stem
        
        try:
            with open(error_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            for record in records:
                timestamp = record.get('timestamp', 'Unknown')
                status = record.get('status', 'pending')
                errors = record.get('errors', [])
                
                for error in errors:
                    rows.append({
                        '日付': date,
                        '記録時刻': timestamp,
                        '状態': status,
                        'エラー内容': error
                    })
                    
        except Exception as e:
            print(f"エラー: {error_file} - {e}")
    
    # CSVファイルに出力
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        fieldnames = ['日付', '記録時刻', '状態', 'エラー内容']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nエラー記録をCSVファイルに出力しました: {output_file}")


if __name__ == "__main__":
    show_error_records()
    
    # CSVエクスポートも実行する場合
    response = input("\nCSVファイルとしてエクスポートしますか？ (y/n): ")
    if response.lower() == 'y':
        export_error_records_csv()