#!/usr/bin/env python3
"""
更新今天的推文数据（简单准确版本）
"""

import json
import requests
from datetime import datetime, timedelta

def update_today():
    """获取今天的最新数据并追加到历史记录"""

    print("=" * 70)
    print("  🔄 更新今天的数据")
    print("=" * 70)

    # 获取今天的推文
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # API请求今天的数据
    start_date = f"{today}T00:00:00.000Z"
    end_date = f"{today}T23:59:59.000Z"

    url = "https://xtracker.polymarket.com/api/users/elonmusk/posts"

    print(f"\n📡 获取 {today} 的数据...")

    try:
        response = requests.get(
            url,
            params={'startDate': start_date, 'endDate': end_date},
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                count = len(data['data'])
                print(f"  ✅ 今天推文数: {count} 条")

                # 更新daily_tweets.json
                with open('data/daily_tweets.json', 'r') as f:
                    daily_data = json.load(f)

                # 查找今天的记录
                updated = False
                for record in daily_data:
                    if record['date'] == today:
                        record['count'] = count
                        record['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        updated = True
                        print(f"  📝 更新记录: {count} 条")
                        break

                # 如果今天还没记录，添加
                if not updated:
                    daily_data.append({
                        'date': today,
                        'count': count,
                        'source': 'xtracker_api',
                        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    print(f"  📝 新增记录: {count} 条")

                # 保存
                with open('data/daily_tweets.json', 'w') as f:
                    json.dump(daily_data, f, ensure_ascii=False, indent=2)

                print(f"\n✅ 已更新！")

                # 显示最近7天
                print(f"\n📊 最近7天:")
                for record in daily_data[-7:]:
                    print(f"  {record['date']}: {record['count']} 条")

            else:
                print(f"  ℹ️  今天还没有推文数据")

        else:
            print(f"  ❌ 请求失败: {response.status_code}")

    except Exception as e:
        print(f"  ❌ 错误: {e}")

    print("=" * 70)


if __name__ == "__main__":
    update_today()
