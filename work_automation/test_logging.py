#!/usr/bin/env python3
"""
ログ機能の基本テスト
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

# ログディレクトリ作成
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

# ログファイル名
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"test_log_{timestamp}.log"

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_logging():
    """ログ機能のテスト"""
    print("=== ログ機能テスト開始 ===")
    
    logger.info("テスト開始: ログ機能の確認")
    logger.info("日本語のログメッセージもテスト")
    
    # 警告メッセージ
    logger.warning("これは警告メッセージです")
    
    # エラーメッセージ
    logger.error("これはエラーメッセージです")
    
    # デバッグメッセージ（通常は表示されない）
    logger.debug("これはデバッグメッセージです")
    
    print(f"ログファイルが作成されました: {log_file}")
    
    # ログファイルの内容確認
    if log_file.exists():
        print(f"ログファイルサイズ: {log_file.stat().st_size} bytes")
        print("✓ ログ機能は正常に動作しています")
    else:
        print("✗ ログファイルが作成されませんでした")
        return False
    
    print("=== ログ機能テスト完了 ===")
    return True

if __name__ == "__main__":
    success = test_logging()
    sys.exit(0 if success else 1)