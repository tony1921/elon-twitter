#!/usr/bin/env python3
"""
Elon Musk 推文自动记录器
==================================
功能：
1. 自动从 XTracker 抓取推文数量
2. 按日期记录
3. 显示历史趋势
4. 定时自动抓取
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import re

# 配置
CONFIG = {
    'xtracker_url': 'https://xtracker.polymarket.com',
    'data_file': 'data/daily_tweets.json',
    'scrape_interval_minutes': 60,  # 每60分钟抓取一次
    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}


class AutoTweetTracker:
    def __init__(self):
        self.ensure_data_dir()
        self.data = self.load_data()

    def ensure_data_dir(self):
        """确保数据目录存在"""
        os.makedirs("data", exist_ok=True)

    def load_data(self):
        """加载数据"""
        if os.path.exists(CONFIG['data_file']):
            with open(CONFIG['data_file'], 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_data(self):
        """保存数据"""
        with open(CONFIG['data_file'], 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def scrape_xtracker(self):
        """从 XTracker 抓取当前推文数"""
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在抓取 XTracker...")

            headers = {'User-Agent': CONFIG['user_agent']}
            response = requests.get(CONFIG['xtracker_url'], headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 尝试多种方式提取数字
            count = None

            # 方法1: 查找包含推文计数的元素
            selectors = [
                '[data-testid="post-counter"]',
                '.post-count',
                '[class*="PostCounter"]',
                '[class*="tweet-count"]',
                'h1', 'h2', 'h3',
            ]

            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    # 查找2-4位数字
                    match = re.search(r'\b\d{2,4}\b', text)
                    if match:
                        count = int(match.group())
                        print(f"✅ 找到计数: {count} (选择器: {selector})")
                        break
                if count:
                    break

            # 方法2: 在整个页面中搜索
            if not count:
                all_text = soup.get_text()
                numbers = re.findall(r'\b\d{2,4}\b', all_text)
                if numbers:
                    # 取最大的数字（可能是推文总数）
                    count = int(max(numbers))
                    print(f"✅ 智能搜索找到计数: {count}")

            return count

        except Exception as e:
            print(f"❌ 抓取失败: {e}")
            return None

    def add_record(self, count):
        """添加或更新今天的记录"""
        today = datetime.now().strftime("%Y-%m-%d")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 查找今天的记录
        for record in self.data:
            if record['date'] == today:
                # 更新现有记录
                old_count = record['count']
                record['count'] = count
                record['updated_at'] = now_str

                # 添加历史记录（如果数量变化）
                if 'history' not in record:
                    record['history'] = []
                record['history'].append({
                    'time': datetime.now().strftime("%H:%M"),
                    'count': count
                })

                print(f"📝 更新记录: {today} - {old_count} → {count} 条")
                self.save_data()
                return True

        # 创建新记录
        record = {
            "date": today,
            "count": count,
            "created_at": now_str,
            "updated_at": now_str,
            "history": [{
                'time': datetime.now().strftime("%H:%M"),
                'count': count
            }]
        }
        self.data.append(record)
        self.save_data()
        print(f"📝 新增记录: {today} - {count} 条")
        return True

    def show_history(self, days=7):
        """显示最近几天的记录"""
        if not self.data:
            print("📭 暂无记录")
            return

        # 按日期排序，取最近N天
        sorted_data = sorted(self.data, key=lambda x: x['date'], reverse=True)[:days]

        print(f"\n📊 最近 {len(sorted_data)} 天的记录：")
        print("=" * 70)

        for record in sorted_data:
            print(f"{record['date']}: {record['count']} 条", end="")

            # 显示当天的变化
            if 'history' in record and len(record['history']) > 1:
                first = record['history'][0]['count']
                last = record['history'][-1]['count']
                change = last - first
                if change > 0:
                    print(f" (增加 +{change})", end="")
                elif change < 0:
                    print(f" (减少 {change})", end="")

            print()

    def show_stats(self):
        """显示统计信息"""
        if len(self.data) < 2:
            print("⚠️  数据不足，需要至少2天的记录")
            return

        counts = [r['count'] for r in self.data]
        avg = sum(counts) / len(counts)

        print(f"\n📈 统计信息（共 {len(self.data)} 天）：")
        print("=" * 60)
        print(f"平均推文：{avg:.1f} 条/天")
        print(f"最高记录：{max(counts)} 条")
        print(f"最低记录：{min(counts)} 条")

        # 最近3天 vs 前3天
        if len(self.data) >= 6:
            recent = sorted(self.data, key=lambda x: x['date'], reverse=True)
            recent_3 = [r['count'] for r in recent[:3]]
            previous_3 = [r['count'] for r in recent[3:6]]

            avg_recent = sum(recent_3) / 3
            avg_previous = sum(previous_3) / 3

            print(f"\n趋势分析：")
            print(f"最近3天平均：{avg_recent:.1f} 条/天")
            print(f"前3天平均：{avg_previous:.1f} 条/天")

            if avg_recent > avg_previous * 1.1:
                print("📈 趋势：上升 ↗️")
            elif avg_recent < avg_previous * 0.9:
                print("📉 趋势：下降 ↘️")
            else:
                print("➡️ 趋势：稳定")

    def predict_tomorrow(self):
        """简单推测明天"""
        if len(self.data) < 3:
            print("⚠️  数据不足，需要至少3天的记录")
            return

        # 使用最近3-7天的数据
        recent = sorted(self.data, key=lambda x: x['date'], reverse=True)[:7]
        weights = [3, 2, 1, 1, 1, 1, 1]  # 最近的天数权重更高

        weighted_sum = sum(r['count'] * weights[i] for i, r in enumerate(recent))
        total_weight = sum(weights[:len(recent)])
        prediction = weighted_sum / total_weight

        print(f"\n🔮 推测明天的推文数：约 {int(prediction)} 条")
        print(f"基于最近 {len(recent)} 天的加权平均")

    def run_once(self):
        """运行一次抓取"""
        print("=" * 60)
        print("🤖 自动抓取模式")
        print("=" * 60)

        count = self.scrape_xtracker()
        if count:
            self.add_record(count)
            self.show_history()
            self.show_stats()
        else:
            print("❌ 抓取失败，本次未记录")

    def run_continuous(self):
        """持续运行模式"""
        print("=" * 60)
        print("🔄 持续监控模式")
        print("=" * 60)
        print(f"每 {CONFIG['scrape_interval_minutes']} 分钟自动抓取一次")
        print("按 Ctrl+C 停止\n")

        try:
            while True:
                self.run_once()

                print(f"\n⏰ 下次抓取: {CONFIG['scrape_interval_minutes']} 分钟后...")
                print("=" * 60)

                time.sleep(CONFIG['scrape_interval_minutes'] * 60)

        except KeyboardInterrupt:
            print("\n\n👋 已停止监控")

    def show_menu(self):
        """显示菜单"""
        print("\n" + "=" * 60)
        print("  📝 Elon Musk 推文自动记录器")
        print("=" * 60)
        print("1. 立即抓取一次")
        print("2. 持续监控（每60分钟抓取一次）")
        print("3. 查看历史记录")
        print("4. 查看统计信息")
        print("5. 推测明天")
        print("6. 退出")
        print("=" * 60)


def main():
    tracker = AutoTweetTracker()

    # 如果有命令行参数，直接运行一次
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        tracker.run_once()
        return

    # 交互式菜单
    while True:
        tracker.show_menu()
        choice = input("\n请选择 (1-6): ").strip()

        if choice == "1":
            tracker.run_once()

        elif choice == "2":
            tracker.run_continuous()

        elif choice == "3":
            tracker.show_history()

        elif choice == "4":
            tracker.show_stats()

        elif choice == "5":
            tracker.predict_tomorrow()

        elif choice == "6":
            print("\n👋 再见！")
            break

        else:
            print("❌ 无效选择")


if __name__ == "__main__":
    main()
