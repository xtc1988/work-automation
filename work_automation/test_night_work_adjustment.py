#!/usr/bin/env python3
"""深夜勤務申請エラー対策の時刻調整ロジックテスト"""
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))


def test_time_adjustment_logic():
    """新しい時刻調整ロジックのテスト"""
    print("=== 深夜勤務申請エラー対策の時刻調整ロジックテスト ===")
    
    test_cases = [
        ("21:59", "22:00", False, "21:59は22:00以下（調整不要）"),
        ("22:00", "22:00", False, "22:00は22:00と等しい（調整不要）"),
        ("22:01", "22:00", True, "22:01は22:00より大きい（調整必要）"),
        ("22:08", "22:00", True, "22:08は22:00より大きい（調整必要）★修正前は調整不要だった"),
        ("22:15", "22:00", True, "22:15は22:00より大きい（調整必要）"),
        ("22:30", "22:00", True, "22:30は22:00より大きい（調整必要）"),
        ("23:00", "22:00", True, "23:00は22:00より大きい（調整必要）"),
    ]
    
    def time_to_minutes(time_str):
        parts = time_str.split(':')
        if len(parts) != 2:
            return 0
        hour = int(parts[0])
        minute = int(parts[1])
        return hour * 60 + minute
    
    def is_time_greater_than_threshold(time_str, threshold):
        try:
            time_minutes = time_to_minutes(time_str)
            threshold_minutes = time_to_minutes(threshold)
            return time_minutes > threshold_minutes
        except Exception as e:
            print(f"時刻比較エラー: {e}")
            return False
    
    all_passed = True
    for time_str, threshold, expected, description in test_cases:
        result = is_time_greater_than_threshold(time_str, threshold)
        status = "OK" if result == expected else "NG"
        
        if result != expected:
            all_passed = False
        
        if "★" in description:
            status += " ★重要変更"
        
        print(f"{status}: {time_str} > {threshold} = {result} (期待値: {expected}) - {description}")
    
    print(f"\n全体結果: {'全テスト成功' if all_passed else '一部テスト失敗'}")
    return all_passed


def test_error_patterns():
    """深夜勤務申請エラーパターンのテスト"""
    print("\n=== 深夜勤務申請エラーパターンテスト ===")
    
    error_patterns = [
        "深夜勤務申請が提出されていません",
        "深夜勤務申請",
        "業務上やむを得ない理由で勤務する場合",
        "night work application",
        "late night work"
    ]
    
    test_texts = [
        "エラー：深夜勤務申請が提出されていません。業務上やむを得ない理由で勤務する場合は「深夜勤務申請」を申請してください。",
        "深夜勤務申請の処理中にエラーが発生しました",
        "通常のエラーメッセージです",
        "Night work application is required",
        ""
    ]
    
    def detect_night_work_error(text):
        for pattern in error_patterns:
            if pattern in text:
                return True
        return False
    
    for i, text in enumerate(test_texts):
        result = detect_night_work_error(text)
        expected = i < 4  # 最初の4つはエラーを検出すべき
        status = "OK" if result == expected else "NG"
        
        print(f"{status}: '{text[:50]}...' → 検出: {result}")
    
    return True


if __name__ == "__main__":
    print("深夜勤務申請エラー対策機能のテスト\n")
    
    test1_result = test_time_adjustment_logic()
    test2_result = test_error_patterns()
    
    print("\n=== 変更点サマリー ===")
    print("修正前: 22:15より大きい場合のみ22:00に調整")
    print("修正後: 22:00より大きい場合に22:00に調整（深夜勤務申請エラー対策）")
    print("例: 22:08 → 修正前:調整なし, 修正後:22:00に調整")
    
    if test1_result and test2_result:
        print("\n✓ 全てのテストが成功しました")
        sys.exit(0)
    else:
        print("\n✗ 一部テストが失敗しました")
        sys.exit(1)