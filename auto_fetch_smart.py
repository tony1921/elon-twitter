#!/usr/bin/env python3
"""
智能XTracker记录器 - 自动计算每天增量
"""

import json
import os
import re
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

CONFIG = {
    'xtracker_url': 'https://xtracker.polymarket.com',
    'snapshot_file': 'data/snapshots.json',  # 存储每次抓取的快照
    'daily_file': 'data/daily_tweets.json',  # 存储计算后的每日数据
}


def load_data(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_data(filepath, data):
    os.makedirs("data", exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def scrape_xtracker():
    """从XTracker获取当前总数"""

    try:
        with sync_playwright() as p:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在获取 XTracker...")

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(CONFIG['xtracker_url'], timeout=30000)
            page.wait_for_timeout(3000)

            text = page.inner_text('body')
            numbers = re.findall(r'\b\d+\b', text)
            int_numbers = [int(n) for n in numbers]
            candidates = [n for n in int_numbers if 50 <= n <= 1000 and n != 2026]

            if candidates:
                count = max(candidates)
                print(f"  ✅ 当前总数: {count} 条")
                browser.close()
                return count

            browser.close()
            return None

    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return None


def calculate_daily增量():
    """
    根据快照计算每天的增量

    策略：
    1. 记录每次抓取的总数和时间
    2. 计算相邻两次抓取之间的增量
    3. 根据时间差分配到对应日期
    """

    snapshots = load_data(CONFIG['snapshot_file'])
    daily_data = load_data(CONFIG['daily_file'])

    if len(snapshots) < 2:
        print("  ⚠️  快照不足，无法计算增量")
        return

    # 按时间排序
    snapshots = sorted(snapshots, key=lambda x: x['timestamp'])

    # 计算每天的增量
    daily_增量 = {}

    for i in range(1, len(snapshots)):
        prev = snapshots[i - 1]
        curr = snapshots[i]

        # 时间差（小时）
        prev_time = datetime.fromisoformat(prev['timestamp'])
        curr_time = datetime.fromisoformat(curr['timestamp'])
        hours_diff = (curr_time - prev_time).total_seconds() / 3600

        # 推文增量
        count_diff = curr['total_count'] - prev['total_count']

        if count_diff < 0:
            print(f"  ⚠️  推文数减少: {prev['total_count']} → {curr['total_count']}，跳过")
            continue

        # 计算每小时速率
        hourly_rate = count_diff / hours_diff if hours_diff > 0 else 0

        print(f"  📊 {prev_time.strftime('%m-%d %H:%M')} → {curr_time.strftime('%m-%d %H:%M')}")
        print(f"     增量: +{count_diff} 条 ({hours_diff:.1f}小时, 速率: {hourly_rate:.1f}条/小时)")

        # 根据跨越的天数分配增量
        current_date = prev_time.date()

        while current_date <= curr_time.date():
            # 计算当天的时间范围
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())

            # 实际重叠时间
            overlap_start = max(prev_time, day_start)
            overlap_end = min(curr_time, day_end)
            overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600

            if overlap_hours > 0:
                # 分配增量
                allocated = int(hourly_rate * overlap_hours)

                date_str = current_date.strftime("%Y-%m-%d")
                if date_str not in daily_增量:
                    daily_增量[date_str] = 0
                daily_增量[date_str] += allocated

                print(f"       {date_str}: +{allocated} 条 ({overlap_hours:.1f}小时)")

            current_date += timedelta(days=1)

    # 更新每日数据
    print("\n  💾 更新每日数据:")
    for date_str, increment in sorted(daily_增量.items()):
        # 查找或创建记录
        found = False
        for record in daily_data:
            if record['date'] == date_str:
                old = record['count']
                record['count'] = increment
                record['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"     {date_str}: {old} → {increment} 条")
                found = True
                break

        if not found:
            daily_data.append({
                "date": date_str,
                "count": increment,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_calculated": True  # 标记为计算值
            })
            print(f"     {date_str}: {increment} 条 (新)")

    save_data(CONFIG['daily_file'], daily_data)
    print("\n  ✅ 每日数据已更新")


def main():
    print("=" * 70)
    print("  🤖 智能XTracker记录器")
    print("=" * 70)

    # 1. 抓取当前总数
    total_count = scrape_xtracker()

    if not total_count:
        print("\n❌ 抓取失败")
        return

    # 2. 保存快照
    snapshots = load_data(CONFIG['snapshot_file'])

    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "total_count": total_count,
        "date": datetime.now().strftime("%Y-%m-%d")
    }

    # 检查是否有重复
    if snapshots and snapshots[-1]['total_count'] == total_count:
        last_time = datetime.fromisoformat(snapshots[-1]['timestamp'])
        print(f"\n  ℹ️  总数未变化 ({total_count} 条)，距离上次抓取: {(datetime.now() - last_time).total_seconds()/60:.0f}分钟")
    else:
        snapshots.append(snapshot)
        save_data(CONFIG['snapshot_file'], snapshots)
        print(f"\n  ✅ 快照已保存 (总计: {len(snapshots)} 次)")

    # 3. 计算每日增量
    print("\n" + "=" * 70)
    print("  📊 计算每日增量")
    print("=" * 70)
    calculate_daily增量()

    # 4. 显示当前每日数据
    print("\n" + "=" * 70)
    print("  📈 每日推文统计")
    print("=" * 70)

    daily_data = load_data(CONFIG['daily_file'])
    if daily_data:
        for record in sorted(daily_data, key=lambda x: x['date'], reverse=True)[:7]:
            flag = " (计算值)" if record.get('is_calculated') else ""
            print(f"  {record['date']}: {record['count']} 条{flag}")
    else:
        print("  暂无数据")

    print("=" * 70)


if __name__ == "__main__":
    main()
