#!/usr/bin/env python3
"""
快速预测脚本 - 直接使用推文数量进行预测
"""

import sys
from elon_predictor_enhanced import EnhancedTweetPredictor, CONFIG

def quick_predict(count):
    """快速预测"""
    predictor = EnhancedTweetPredictor(CONFIG)

    # 验证输入
    try:
        current_count = int(count)
        if current_count < 0:
            print("❌ 错误：推文数量不能为负数")
            return
    except ValueError:
        print("❌ 错误：请输入有效的数字")
        return

    print(f"\n📊 使用推文数量: {current_count}")
    print("=" * 60)

    # 运行预测
    result = predictor.run_prediction_with_count(current_count)

    if result:
        print("\n✅ 预测完成！")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 quick_predict.py <推文数量>")
        print("示例: python3 quick_predict.py 100")
        print("")
        print("提示：访问 https://xtracker.polymarket.com 查看当前推文数量")
        sys.exit(1)

    quick_predict(sys.argv[1])
