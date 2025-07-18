#!/usr/bin/env python3
"""
工数管理システムエラーチェック専用ツール

指定した日付範囲のエラーをチェックして、
在宅/出社区分以外のエラーを記録・出力します。
"""
import sys
import os
import time
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from classes.work_time_automation import WorkTimeAutomation
from classes.bulk_automation import BulkWorkAutomation
from classes.csv_processor import WorkDataCSVProcessor


def setup_logging():
    """ロギングの設定"""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"error_check_{timestamp}.log"
    
    # ロガーの設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="工数管理システムのエラーチェックツール",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--start-date",
        required=True,
        help="開始日（YYYY-MM-DD形式）"
    )
    
    parser.add_argument(
        "--end-date",
        required=True,
        help="終了日（YYYY-MM-DD形式）"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ドライラン（日付を表示するのみ）"
    )
    
    args = parser.parse_args()
    
    # ロギング設定
    logger = setup_logging()
    
    logger.info("=" * 50)
    logger.info("工数管理システムエラーチェックツール")
    logger.info(f"チェック期間: {args.start_date} 〜 {args.end_date}")
    logger.info("=" * 50)
    
    # 日付の検証
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        
        if start_date > end_date:
            logger.error("開始日が終了日より後になっています")
            return 1
            
    except ValueError:
        logger.error("日付形式が正しくありません（YYYY-MM-DD形式で指定してください）")
        return 1
    
    # ドライランの場合
    if args.dry_run:
        logger.info("ドライランモード: 日付の確認のみ実行")
        current = start_date
        check_count = 0
        
        while current <= end_date:
            logger.info(f"  - {current.strftime('%Y-%m-%d')}")
            current += timedelta(days=1)
            check_count += 1
            
        logger.info(f"チェック対象: {check_count}日分")
        return 0
    
    # Chromeブラウザに接続
    logger.info("Chromeブラウザに接続します")
    logger.info("事前にChromeをデバッグモードで起動してください:")
    logger.info('  chrome.exe --remote-debugging-port=9222')
    
    try:
        # ダミーのCSVプロセッサを作成（エラーチェックのみなので不要）
        csv_processor = WorkDataCSVProcessor(None)
        
        # 自動化インスタンスの作成
        automation = WorkTimeAutomation.connect_to_existing_chrome()
        bulk_automation = BulkWorkAutomation(automation, csv_processor)
        
        logger.info("接続成功")
        
        # エラーチェックの実行
        logger.info("\nエラーチェックを開始します...")
        
        error_results = bulk_automation.check_errors_only(
            args.start_date,
            args.end_date
        )
        
        # 結果のサマリー表示
        logger.info("\n" + "=" * 50)
        logger.info("エラーチェック結果サマリー")
        logger.info("=" * 50)
        
        total_errors = 0
        error_dates = []
        
        for date, errors in sorted(error_results.items()):
            if errors and errors != ["エラーなし"]:
                total_errors += len(errors)
                error_dates.append(date)
                logger.warning(f"{date}: {len(errors)}件のエラー")
                for error in errors:
                    logger.warning(f"  - {error}")
            else:
                logger.info(f"{date}: エラーなし")
        
        logger.info(f"\n合計: {total_errors}件のエラー（{len(error_dates)}日分）")
        
        if total_errors > 0:
            logger.warning(f"\n⚠️ エラーが検出されました。")
            logger.info("詳細はCSVファイルを確認してください。")
            logger.info("エラー記録は logs/error_records/ ディレクトリに保存されています。")
        else:
            logger.info("\n✅ エラーは検出されませんでした。")
        
        return 0
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        return 1
        
    finally:
        if 'automation' in locals():
            automation.close()
            logger.info("ブラウザ接続を終了しました")


if __name__ == "__main__":
    sys.exit(main())