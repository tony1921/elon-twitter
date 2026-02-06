#!/usr/bin/env python3
"""
生成看板数据并发送Telegram通知
使用追踪期间数据
"""

import json
import requests
from datetime import datetime, timedelta

# 当前追踪期间配置
CURRENT_PERIOD = {
    'name': 'Feb 3 - Feb 10, 2026',
    'start': '2026-02-03T17:00:00.000Z',
    'end': '2026-02-10T22:00:00.000Z'
}

def fetch_tracking_period_data():
    """从追踪期间获取数据并按EST日期分组"""
    url = 'https://xtracker.polymarket.com/api/users/elonmusk/posts'

    try:
        response = requests.get(
            url,
            params={
                'startDate': CURRENT_PERIOD['start'],
                'endDate': CURRENT_PERIOD['end']
            },
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                posts = data['data']

                # 按EST时区分组统计
                daily_counts = {}
                for post in posts:
                    created_at = post.get('createdAt', '')
                    if created_at:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        est_dt = dt - timedelta(hours=5)
                        date = est_dt.strftime("%Y-%m-%d")
                        daily_counts[date] = daily_counts.get(date, 0) + 1

                return daily_counts

    except Exception as e:
        print(f"❌ 获取数据失败: {e}")

    return None


def update_dashboard_data():
    """更新看板数据"""

    # 获取追踪期间数据
    period_data = fetch_tracking_period_data()

    if not period_data:
        print("⚠️  无法获取追踪期间数据")
        return None, 0

    # 加载历史数据
    try:
        with open('data/daily_tweets.json', 'r') as f:
            daily_data = json.load(f)
    except:
        daily_data = []

    # 更新追踪期间的日期数据
    today_str = datetime.now().strftime("%Y-%m-%d")

    for date, count in period_data.items():
        # 查找或创建记录
        found = False
        for record in daily_data:
            if record['date'] == date:
                record['count'] = count
                record['period'] = CURRENT_PERIOD['name']
                record['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                found = True
                break

        if not found:
            daily_data.append({
                'date': date,
                'count': count,
                'period': CURRENT_PERIOD['name'],
                'source': 'xtracker_api',
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    # 保存
    with open('data/daily_tweets.json', 'w') as f:
        json.dump(daily_data, f, ensure_ascii=False, indent=2)

    # 排序
    sorted_data = sorted(daily_data, key=lambda x: x['date'])

    # 计算统计数据
    counts = [r['count'] for r in sorted_data]
    recent_7 = sorted_data[-7:]

    # 获取今天的记录
    today_record = None
    for record in sorted_data:
        if record['date'] == today_str:
            today_record = record
            break

    if not today_record:
        today_record = {'count': 0}

    # 生成看板数据
    dashboard_data = {
        'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'today': {
            'date': today_str,
            'count': today_record['count'],
            'vs_avg': today_record['count'] - (sum(counts) / len(counts))
        },
        'week_avg': sum([r['count'] for r in recent_7]) / len(recent_7),
        'stats': {
            'total_days': len(sorted_data),
            'avg': sum(counts) / len(counts),
            'max': max(counts),
            'min': min(counts),
            'max_date': max(sorted_data, key=lambda x: x['count'])['date']
        },
        'recent_days': [
            {
                'date': r['date'],
                'count': r['count']
            }
            for r in recent_7
        ]
    }

    # 保存看板数据
    with open('data/dashboard_data.json', 'w') as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 看板数据已更新")

    return dashboard_data, today_record['count'] if today_record else 0


def send_telegram_notification(today_count, recent_data, stats):
    """发送Telegram通知"""

    # 加载配置
    try:
        with open('telegram_config.json', 'r') as f:
            config = json.load(f)
    except:
        print("⚠️  Telegram配置文件不存在")
        return

    if not config.get('enabled'):
        print("ℹ️  Telegram推送未启用")
        return

    bot_token = config.get('bot_token')
    chat_id = config.get('chat_id')

    if bot_token == "YOUR_BOT_TOKEN_HERE" or chat_id == "YOUR_CHAT_ID_HERE":
        print("⚠️  请先配置Telegram Bot")
        return

    # 计算趋势
    recent_3_avg = sum(r['count'] for r in recent_data[-3:]) / 3
    previous_3_avg = sum(r['count'] for r in recent_data[-6:-3]) / 3 if len(recent_data) >= 6 else recent_3_avg

    if recent_3_avg > previous_3_avg * 1.1:
        trend = "📈 上升"
    elif recent_3_avg < previous_3_avg * 0.9:
        trend = "📉 下降"
    else:
        trend = "➡️ 稳定"

    # 构建消息
    now = datetime.now()
    message = f"""🤖 *Elon Musk 推文数据更新*

📅 *{now.strftime("%Y-%m-%d")}* | 🕐 *{now.strftime("%H:%M")}*

━━━━━━━━━━━━━━━━━━━━━
📊 *今日数据*
   今天: *{today_count}* 条
   7天平均: {sum([r['count'] for r in recent_data[-7:]]) / 7:.1f} 条/天

━━━━━━━━━━━━━━━━━━━━━
📈 *最近3天*
"""

    for day in recent_data[-3:]:
        message += f"   {day['date']}: {day['count']} 条\n"

    message += f"""
━━━━━━━━━━━━━━━━━━━━━
📉 *趋势*: {trend}

📊 *历史统计*
   总天数: {stats['total_days']} 天
   平均: {stats['avg']:.1f} 条/天
   最高: {stats['max']} 条

📂 Excel & 看板已更新
━━━━━━━━━━━━━━━━━━━━━
🤖 Auto-update by polymarket-predictor
"""

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(
            url,
            json={
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            },
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Telegram推送成功")
        else:
            print(f"❌ Telegram推送失败: {response.text}")

    except Exception as e:
        print(f"❌ Telegram推送错误: {e}")


def main():
    """主函数"""

    print("=" * 70)
    print("  🔄 更新数据 & 推送通知")
    print("=" * 70)

    try:
        # 更新看板数据
        dashboard_data, today_count = update_dashboard_data()

        if not dashboard_data:
            print("⚠️  数据更新失败，跳过后续步骤")
            return

        # 同时更新Excel
        print("\n📊 更新Excel...")
        import subprocess
        subprocess.run(['python3', 'generate_excel.py'], capture_output=True)

        # 发送Telegram通知 (只有当数据正常时才发送)
        print("\n📱 发送Telegram通知...")
        if 'recent_days' in dashboard_data and 'stats' in dashboard_data:
            send_telegram_notification(
                today_count,
                dashboard_data['recent_days'],
                dashboard_data['stats']
            )
        else:
            print("⚠️  数据不完整，跳过Telegram通知")

        print("\n✅ 全部完成！")
    except Exception as e:
        print(f"\n❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 70)


if __name__ == "__main__":
    main()
