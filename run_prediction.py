#!/usr/bin/env python3
"""
一键运行版本 - 直接执行预测并显示结果
"""

from elon_predictor_enhanced import EnhancedTweetPredictor, CONFIG
from datetime import datetime
import pytz

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                                ║
║        🤖 Elon Musk 推文预测系统 - 一键运行版                   ║
║                                                                ║
╚══════════════════════════════════════════════════════════════╝
    """)

    predictor = EnhancedTweetPredictor(CONFIG)

    # 解析时间窗口
    window = predictor.parse_time_window()

    print(f"📊 市场信息:")
    print(f"   市场: Elon Musk # tweets February 5 - February 7, 2026")
    print(f"   开始: {window['start_et'].strftime('%Y-%m-%d %I:%M %p %Z')}")
    print(f"   结束: {window['end_et'].strftime('%Y-%m-%d %I:%M %p %Z')}")
    print(f"   总时长: {window['total_hours']:.1f} 小时 ({window['total_hours']/24:.1f} 天)")
    print()

    # 计算当前时间
    now = datetime.now(pytz.UTC)
    elapsed = (now - window['start_utc']).total_seconds() / 3600
    remaining = (window['end_utc'] - now).total_seconds() / 3600

    print(f"⏰ 当前时间状态:")
    if elapsed < 0:
        print(f"   市场尚未开始")
        print(f"   距离开始还有: {abs(elapsed):.1f} 小时")
        print()
        print("📝 使用模拟数据进行演示（假设市场进行24小时，85条推文）")
        current_count = 85
        elapsed_hours = 24
        remaining_hours = 24
    elif remaining < 0:
        print(f"   市场已结束")
        print(f"   已结束: {abs(remaining):.1f} 小时前")
        return
    else:
        print(f"   已进行: {elapsed:.1f} 小时 ({elapsed/24:.1f} 天)")
        print(f"   剩余: {remaining:.1f} 小时 ({remaining/24:.1f} 天)")
        print()

        # 尝试自动抓取
        print("🔄 正在从 XTracker 抓取数据...")
        snapshot = predictor.scrape_xtracker()

        if snapshot:
            current_count = snapshot['current_count']
            print(f"✓ 成功获取: {current_count} 条推文")
        else:
            print("⚠ 自动抓取失败，请手动输入当前推文数:")
            try:
                current_count = int(input("   当前推文数: "))
            except (EOFError, ValueError):
                print("   使用模拟数据: 85")
                current_count = 85

        elapsed_hours = elapsed
        remaining_hours = remaining

    print()
    print("="*70)
    print("📊 开始预测...")
    print("="*70)

    # 执行预测
    prediction = predictor.predict(current_count, elapsed_hours, remaining_hours)

    # 映射到区间
    buckets = predictor.map_to_buckets(prediction['expected_total'])

    # 获取推荐
    history = predictor.load_history()
    recommendation = predictor.get_recommendation(prediction, history)

    # 显示完整推荐
    predictor.display_recommendation(prediction, recommendation, current_count)

    # 保存结果
    result = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'current_count': current_count,
        'elapsed_hours': elapsed_hours,
        'remaining_hours': remaining_hours,
        'progress_pct': prediction['progress_pct'],
        'predicted_linear': prediction['predicted_linear'],
        'predicted_conservative': prediction['predicted_conservative'],
        'predicted_weekend': prediction['predicted_weekend'],
        'expected_total': prediction['expected_total'],
        'ci80_lower': prediction['ci80_lower'],
        'ci80_upper': prediction['ci80_upper'],
        'ci90_lower': prediction['ci90_lower'],
        'ci90_upper': prediction['ci90_upper'],
        'daily_rate': prediction['daily_rate'],
        'buckets': buckets,
        'recommendation': recommendation,
    }

    predictor.save_prediction(result)

    print()
    print("="*70)
    print("✅ 预测完成！")
    print("="*70)
    print(f"\n💾 数据已保存:")
    print(f"   - 历史记录: data/monitoring_history.json")
    print(f"   - 运行日志: logs/predictor_{datetime.now().strftime('%Y%m%d')}.log")
    print()
    print("💡 提示:")
    print("   - 查看历史: python3 -c \"import json; print(json.dumps(json.load(open('data/monitoring_history.json')), indent=2))\"")
    print("   - 再次运行: python3 run_prediction.py")
    print("   - 交互模式: python3 elon_predictor_enhanced.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹ 用户停止")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
