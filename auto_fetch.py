#!/usr/bin/env python3
"""
自动从XTracker获取推文数量并记录
"""

import json
import os
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

CONFIG = {
    'xtracker_url': 'https://xtracker.polymarket.com',
    'data_file': 'data/daily_tweets.json',
}


def load_data():
    if os.path.exists(CONFIG['data_file']):
        with open(CONFIG['data_file'], 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG['data_file'], 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_record(count):
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 检查今天是否已有记录
    for record in data:
        if record['date'] == today:
            old_count = record['count']
            record['count'] = count
            record['updated_at'] = now

            # 添加历史记录
            if 'history' not in record:
                record['history'] = []
            record['history'].append({
                'time': datetime.now().strftime("%H:%M"),
                'count': count
            })

            save_data(data)
            print(f"📝 更新: {old_count} → {count} 条")
            return True

    # 新记录
    data.append({
        "date": today,
        "count": count,
        "created_at": now,
        "updated_at": now,
        "history": [{
            'time': datetime.now().strftime("%H:%M"),
            'count': count
        }]
    })
    save_data(data)
    print(f"📝 新增: {today} - {count} 条")
    return True


def scrape_xtracker():
    """从XTracker获取推文数量"""

    try:
        with sync_playwright() as p:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在获取 XTracker 数据...")

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(CONFIG['xtracker_url'], timeout=30000)

            # 等待页面加载
            page.wait_for_timeout(3000)

            # 获取页面文本
            text = page.inner_text('body')

            # 查找所有数字
            numbers = re.findall(r'\b\d+\b', text)
            int_numbers = [int(n) for n in numbers]

            # 过滤：推文数量通常是几十到几百之间的数字
            # 排除年份(2026)、大数字(>1000)
            candidates = [n for n in int_numbers if 50 <= n <= 500 and n != 2026]

            print(f"  找到的候选数字: {candidates}")

            if candidates:
                # 如果有多个候选，取最大的（可能是总数）
                count = max(candidates)
                print(f"  ✅ 推测推文数: {count}")
                browser.close()
                return count

            # 如果没找到，尝试直接查找特定元素
            print("  尝试查找特定元素...")

            # 尝试各种选择器
            selectors = [
                'text="Posts"',
                '[class*="post"]',
                '[class*="count"]',
                'h1', 'h2', 'h3',
            ]

            for selector in selectors:
                try:
                    elements = page.query_selector_all(selector)
                    for el in elements:
                        el_text = el.inner_text()
                        match = re.search(r'\b(\d{2,4})\b', el_text)
                        if match:
                            num = int(match.group(1))
                            if 50 <= num <= 500:
                                print(f"  ✅ 从元素找到: {num} ({selector})")
                                browser.close()
                                return num
                except:
                    pass

            browser.close()
            print("  ❌ 无法确定推文数量")
            return None

    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return None


def main():
    print("=" * 70)
    print("  🤖 自动获取并记录推文数量")
    print("=" * 70)

    count = scrape_xtracker()

    if count:
        add_record(count)

        # 显示最近记录
        data = load_data()
        if data:
            print(f"\n📊 最近记录:")
            for record in sorted(data, key=lambda x: x['date'], reverse=True)[:7]:
                print(f"  {record['date']}: {record['count']} 条")
    else:
        print("\n❌ 获取失败，请稍后重试或手动记录")

    print("=" * 70)


if __name__ == "__main__":
    main()
