#!/usr/bin/env python3
"""
工数管理システム自動化メインスクリプト
"""
import argparse
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from classes.work_time_automation import WorkTimeAutomation
from classes.csv_processor import WorkDataCSVProcessor
from classes.bulk_automation import BulkWorkAutomation


def setup_logging():
    """ログ設定の初期化"""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"work_automation_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def create_template(days: int, start_date: str = None):
    """CSVテンプレートを生成"""
    logger = logging.getLogger(__name__)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"日付形式が正しくありません: {start_date}")
            return False
    else:
        start = datetime.now()
    
    # テンプレートファイル名
    template_file = f"work_template_{start.strftime('%Y%m%d')}.csv"
    
    # ヘッダー行
    headers = [
        "日付", "開始時刻", "終了時刻", "在宅/出社区分",
        "休憩1_開始", "休憩1_終了", "休憩2_開始", "休憩2_終了",
        "プロジェクト1_時間", "プロジェクト1_備考",
        "プロジェクト2_時間", "プロジェクト2_備考",
        "プロジェクト3_時間", "プロジェクト3_備考",
        "プロジェクト4_時間", "プロジェクト4_備考"
    ]
    
    rows = []
    for i in range(days):
        current_date = start + timedelta(days=i)
        # 土日をスキップ
        if current_date.weekday() >= 5:  # 5=土曜, 6=日曜
            continue
            
        row = {
            "日付": current_date.strftime("%Y-%m-%d"),
            "開始時刻": "09:00",
            "終了時刻": "18:00",
            "在宅/出社区分": "在宅",
            "休憩1_開始": "12:00",
            "休憩1_終了": "13:00",
            "休憩2_開始": "",
            "休憩2_終了": "",
            "プロジェクト1_時間": "",
            "プロジェクト1_備考": "",
            "プロジェクト2_時間": "",
            "プロジェクト2_備考": "",
            "プロジェクト3_時間": "",
            "プロジェクト3_備考": "",
            "プロジェクト4_時間": "",
            "プロジェクト4_備考": ""
        }
        rows.append(row)
    
    # CSVファイルに書き込み
    import csv
    with open(template_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"テンプレートファイルを作成しました: {template_file}")
    logger.info(f"作成した日数: {len(rows)}日分（平日のみ）")
    
    return True


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="工数管理システム自動化ツール"
    )
    
    parser.add_argument(
        "--csv",
        help="処理するCSVファイルのパス"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際の入力を行わず検証のみ実行"
    )
    parser.add_argument(
        "--create-template",
        action="store_true",
        help="CSVテンプレートを生成"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=5,
        help="テンプレート生成時の日数（デフォルト: 5）"
    )
    parser.add_argument(
        "--start-date",
        help="テンプレートの開始日（YYYY-MM-DD形式）"
    )
    parser.add_argument(
        "--connection-test",
        action="store_true",
        help="接続確認テストを実行"
    )
    
    args = parser.parse_args()
    
    # ログ設定
    logger = setup_logging()
    logger.info("工数管理システム自動化ツールを開始します")
    
    try:
        # テンプレート生成モード
        if args.create_template:
            success = create_template(args.days, args.start_date)
            return 0 if success else 1
        
        # 接続確認テストモード
        if args.connection_test:
            logger.info("接続確認テストを開始します")
            
            try:
                # Chrome接続
                automation = WorkTimeAutomation.connect_to_existing_chrome()
                
                # 包括的な接続テスト実行
                test_results = automation.comprehensive_connection_test()
                
                # 結果表示
                logger.info("=" * 50)
                logger.info("接続確認テスト結果")
                logger.info("=" * 50)
                logger.info(f"実行時刻: {test_results['timestamp']}")
                logger.info(f"ブラウザ接続: {'✓' if test_results['browser_connection'] else '✗'}")
                logger.info(f"curl接続テスト: {'✓' if test_results['curl_test'] else '✗'}")
                logger.info(f"wget接続テスト: {'✓' if test_results['wget_test'] else '✗'}")
                logger.info(f"総合結果: {test_results['overall_status']}")
                
                # 健全性チェック結果の詳細
                health = test_results.get('health_check', {})
                if health:
                    logger.info("健全性チェック詳細:")
                    logger.info(f"  ページ読み込み: {'✓' if health.get('page_loaded') else '✗'}")
                    logger.info(f"  フォーム要素数: {health.get('form_elements', 0)}")
                    logger.info(f"  入力要素数: {health.get('input_elements', 0)}")
                    if health.get('errors'):
                        logger.warning(f"  エラー: {health['errors']}")
                
                logger.info("=" * 50)
                
                # 結果に基づく終了コード
                if test_results['overall_status'] == 'PASSED':
                    logger.info("接続確認テストが成功しました")
                    return 0
                elif test_results['overall_status'] == 'PARTIAL':
                    logger.warning("接続確認テストは部分的に成功しました")
                    return 0
                else:
                    logger.error("接続確認テストに失敗しました")
                    return 1
                    
            except Exception as e:
                logger.error(f"接続確認テストでエラーが発生しました: {e}")
                return 1
            finally:
                if 'automation' in locals():
                    automation.close()
        
        # CSV処理モード
        if args.csv:
            # CSV読み込み
            logger.info(f"CSVファイルを読み込みます: {args.csv}")
            csv_processor = WorkDataCSVProcessor(args.csv)
            
            if not csv_processor.load_csv_data():
                logger.error("CSVファイルの読み込みに失敗しました")
                return 1
            
            # データ検証
            logger.info("データの検証を開始します")
            if not csv_processor.validate_data():
                logger.error("データ検証でエラーが見つかりました")
                return 1
            
            # サマリー表示
            csv_processor.show_data_summary()
            
            # ドライランモード
            if args.dry_run:
                logger.info("ドライランモードで実行しました（実際の入力は行われません）")
                return 0
            
            # 実行確認
            response = input("\n処理を開始しますか？ (y/n): ")
            if response.lower() != 'y':
                logger.info("処理をキャンセルしました")
                return 0
            
            # Chrome接続
            logger.info("Chromeブラウザに接続します")
            automation = WorkTimeAutomation.connect_to_existing_chrome()
            
            # 一括処理実行
            bulk_processor = BulkWorkAutomation(automation, csv_processor)
            
            success = bulk_processor.process_all_data()
            
            # 結果表示
            bulk_processor.show_results_summary()
            
            # 結果をCSVに保存
            result_file = bulk_processor.save_results_to_csv()
            logger.info(f"処理結果を保存しました: {result_file}")
            
            return 0 if success else 1
            
        else:
            # 引数なしの場合はヘルプを表示
            parser.print_help()
            return 0
            
    except KeyboardInterrupt:
        logger.info("ユーザーによって処理が中断されました")
        return 1
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())