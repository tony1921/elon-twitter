#!/usr/bin/env python3
"""
Elon Musk 推文记录器 - 简单版
==================================
功能：
1. 记录每天的推文数量
2. 查看历史记录
3. 简单的趋势推测
"""

import json
import os
from datetime import datetime
from pathlib import Path

# 数据文件
DATA_FILE = "data/daily_tweets.json"


class SimpleTweetTracker:
    def __init__(self):
        self.ensure_data_dir()
        self.data = self.load_data()

    def ensure_data_dir(self):
        """确保数据目录存在"""
        os.makedirs("data", exist_ok=True)

    def load_data(self):
        """加载数据"""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_data(self):
        """保存数据"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_record(self, count, note=""):
        """添加记录"""
        today = datetime.now().strftime("%Y-%m-%d")

        # 检查今天是否已有记录
        for record in self.data:
            if record['date'] == today:
                print(f"⚠️  今天 ({today}) 已有记录：{record['count']} 条")
                choice = input("是否覆盖？(y/n): ").strip().lower()
                if choice == 'y':
                    record['count'] = count
                    record['note'] = note
                    record['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.save_data()
                    print(f"✅ 已更新记录：{count} 条")
                else:
                    print("❌ 未保存")
                return

        # 添加新记录
        record = {
            "date": today,
            "count": count,
            "note": note,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.data.append(record)
        self.save_data()
        print(f"✅ 已记录：{today} - {count} 条推文")

    def show_history(self, limit=10):
        """显示历史记录"""
        if not self.data:
            print("📭 暂无记录")
            return

        print(f"\n📊 最近 {min(limit, len(self.data))} 条记录：")
        print("=" * 60)

        # 按日期倒序
        sorted_data = sorted(self.data, key=lambda x: x['date'], reverse=True)[:limit]

        for i, record in enumerate(sorted_data, 1):
            print(f"{i}. {record['date']} - {record['count']} 条", end="")
            if record.get('note'):
                print(f" ({record['note']})", end="")
            print()

    def show_stats(self):
        """显示统计信息"""
        if not self.data:
            print("📭 暂无数据，无法统计")
            return

        counts = [r['count'] for r in self.data]

        print("\n📈 统计信息：")
        print("=" * 60)
        print(f"总记录数：{len(self.data)} 天")
        print(f"平均推文：{sum(counts) / len(counts):.1f} 条/天")
        print(f"最高记录：{max(counts)} 条")
        print(f"最低记录：{min(counts)} 条")
        print(f"总推文数：{sum(counts)} 条")

    def simple_predict(self, days=7):
        """简单推测 - 基于最近几天的平均值"""
        if len(self.data) < days:
            print(f"⚠️  数据不足，需要至少 {days} 天的记录（当前：{len(self.data)} 天）")
            return

        # 获取最近N天的数据
        recent_data = sorted(self.data, key=lambda x: x['date'], reverse=True)[:days]
        recent_counts = [r['count'] for r in recent_data]

        avg = sum(recent_counts) / len(recent_counts)

        print(f"\n🔮 基于最近 {days} 天的推测：")
        print("=" * 60)
        print(f"最近 {days} 天平均：{avg:.1f} 条/天")
        print(f"推测明天：约 {int(avg)} 条")

        # 趋势
        if len(recent_counts) >= 3:
            first_half = recent_counts[-3:]
            second_half = recent_counts[:3]
            avg1 = sum(first_half) / len(first_half)
            avg2 = sum(second_half) / len(second_half)

            if avg2 > avg1 * 1.2:
                print("📈 趋势：上升 ↗️")
            elif avg2 < avg1 * 0.8:
                print("📉 趋势：下降 ↘️")
            else:
                print("➡️ 趋势：稳定")

    def show_menu(self):
        """显示菜单"""
        print("\n" + "=" * 60)
        print("  📝 Elon Musk 推文记录器")
        print("=" * 60)
        print("1. 记录今天的推文数")
        print("2. 查看历史记录")
        print("3. 查看统计信息")
        print("4. 简单推测")
        print("5. 退出")
        print("=" * 60)

    def run(self):
        """运行主程序"""
        while True:
            self.show_menu()
            choice = input("\n请选择 (1-5): ").strip()

            if choice == "1":
                try:
                    count = int(input("今天推文数量："))
                    note = input("备注（可选，按回车跳过）：").strip()
                    self.add_record(count, note)
                except ValueError:
                    print("❌ 请输入有效的数字")

            elif choice == "2":
                try:
                    limit = input("显示最近几条？（默认10）：").strip()
                    limit = int(limit) if limit else 10
                    self.show_history(limit)
                except ValueError:
                    self.show_history()

            elif choice == "3":
                self.show_stats()

            elif choice == "4":
                try:
                    days = input("基于最近几天？（默认7天）：").strip()
                    days = int(days) if days else 7
                    self.simple_predict(days)
                except ValueError:
                    self.simple_predict()

            elif choice == "5":
                print("\n👋 再见！")
                break

            else:
                print("❌ 无效选择")

            input("\n按回车继续...")


def main():
    tracker = SimpleTweetTracker()
    tracker.run()


if __name__ == "__main__":
    main()
