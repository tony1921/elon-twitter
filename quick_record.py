#!/usr/bin/env python3
"""
快速记录 - 每天输入推文数量
"""

import json
import os
from datetime import datetime

DATA_FILE = "data/daily_tweets.json"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_count(count):
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 检查今天是否已有记录
    for record in data:
        if record['date'] == today:
            old = record['count']
            record['count'] = count
            record['updated_at'] = now
            save_data(data)
            print(f"✅ 更新: {old} → {count}")
            return

    # 新记录
    data.append({
        "date": today,
        "count": count,
        "created_at": now,
        "updated_at": now
    })
    save_data(data)
    print(f"✅ 记录: {today} - {count} 条")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python3 quick_record.py <推文数量>")
        print("示例: python3 quick_record.py 100")
        sys.exit(1)

    try:
        count = int(sys.argv[1])
        add_count(count)

        # 显示最近7天
        data = load_data()
        if data:
            print(f"\n📊 最近7天:")
            for record in sorted(data, key=lambda x: x['date'], reverse=True)[:7]:
                print(f"  {record['date']}: {record['count']} 条")
    except ValueError:
        print("❌ 请输入有效的数字")
