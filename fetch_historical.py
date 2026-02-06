#!/usr/bin/env python3
"""
使用XTracker API获取历史数据
"""

import requests
import json
from datetime import datetime, timedelta

def get_historical_posts(days=60):
    """获取过去N天的推文数据"""

    print("=" * 70)
    print("  📊 获取历史数据")
    print("=" * 70)

    # 计算时间范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # XTracker API
    base_url = "https://xtracker.polymarket.com/api/users/elonmusk/posts"

    # 格式化日期
    start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    print(f"\n📅 时间范围: {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
    print(f"📡 请求: {base_url}")
    print(f"   startDate={start_str}")
    print(f"   endDate={end_str}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
        }

        response = requests.get(
            base_url,
            params={
                'startDate': start_str,
                'endDate': end_str
            },
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 成功获取数据!")
            print(f"   数据类型: {type(data)}")
            print(f"   数据长度: {len(data) if isinstance(data, list) else 'N/A'}")

            # 保存原始数据
            with open('data/raw_historical.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n💾 原始数据已保存到: data/raw_historical.json")

            return data
        else:
            print(f"\n❌ 请求失败: {response.status_code}")
            print(f"   响应: {response.text[:500]}")
            return None

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return None


def get_tracking_periods():
    """获取所有追踪期间"""

    print("\n" + "=" * 70)
    print("  📅 获取追踪期间")
    print("=" * 70)

    # 从之前的请求中获取的tracking ID
    tracking_ids = [
        'a8f7649c-2254-4331-8fa9-0fc27ffa3e1b',
        'f49cddbc-108c-446d-9dd8-6e3d6ddebf12'
    ]

    all_data = []

    for tracking_id in tracking_ids:
        try:
            url = f"https://xtracker.polymarket.com/api/trackings/{tracking_id}?includeStats=true"
            print(f"\n📡 请求: {url}")

            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功!")
                print(f"   数据: {json.dumps(data, indent=2)[:500]}")
                all_data.append(data)
            else:
                print(f"❌ 失败: {response.status_code}")

        except Exception as e:
            print(f"❌ 错误: {e}")

    # 保存
    if all_data:
        with open('data/tracking_periods.json', 'w') as f:
            json.dump(all_data, f, indent=2)
        print(f"\n💾 追踪期间数据已保存")

    return all_data


def main():
    # 获取历史数据
    historical_data = get_historical_posts(days=60)

    if historical_data:
        print(f"\n📊 数据预览:")
        if isinstance(historical_data, list):
            for item in historical_data[:5]:
                print(f"   {item}")
        elif isinstance(historical_data, dict):
            for key, value in list(historical_data.items())[:5]:
                print(f"   {key}: {value}")

    # 获取追踪期间
    tracking_data = get_tracking_periods()


if __name__ == "__main__":
    main()
