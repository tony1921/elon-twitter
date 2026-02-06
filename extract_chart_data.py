#!/usr/bin/env python3
"""
提取XTracker图表中的历史数据
"""

from playwright.sync_api import sync_playwright
import json
import re
from datetime import datetime, timedelta

def extract_chart_data():
    """提取图表数据"""

    try:
        with sync_playwright() as p:
            print("=" * 70)
            print("  📊 提取 XTracker 历史图表数据")
            print("=" * 70)

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            url = 'https://xtracker.polymarket.com/user/elonmusk'
            print(f"\n📡 访问: {url}")
            page.goto(url, timeout=30000)

            # 等待页面加载
            page.wait_for_timeout(5000)

            # 方法1: 查找页面中的JSON数据
            print("\n🔍 方法1: 查找页面JSON数据...")
            html = page.content()

            # 查找常见的图表数据模式
            patterns = [
                r'"data":\s*\[.*?\]',  # 图表数据数组
                r'"points":\s*\[.*?\]',  # 数据点
                r'"values":\s*\[.*?\]',  # 值
                r'window\.__DATA__\s*=\s*({.*?});',
                r'__NEXT_DATA__.*?>(.*?)</script>',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                if matches:
                    print(f"  ✅ 找到匹配: {pattern[:50]}")
                    for match in matches[:2]:
                        print(f"    数据: {match[:200]}")
                    break

            # 方法2: 尝试点击不同的时间范围
            print("\n🔍 方法2: 尝试不同时间范围...")

            time_ranges = [
                ('Past 7d', '过去7天'),
                ('Past 30d', '过去30天'),
                ('This Month', '本月'),
            ]

            for range_name, range_desc in time_ranges:
                try:
                    print(f"\n  尝试: {range_desc} ({range_name})")

                    # 查找并点击
                    buttons = page.query_selector_all('button, div[role="button"], [class*="tab"]')
                    for btn in buttons:
                        text = btn.inner_text()
                        if range_name in text:
                            btn.click()
                            page.wait_for_timeout(3000)

                            # 获取新页面内容
                            new_text = page.inner_text('body')

                            # 提取数字（可能是每日数据）
                            numbers = re.findall(r'\b\d{1,4}\b', new_text)
                            print(f"    找到数字: {numbers[:10]}")
                            break
                except Exception as e:
                    print(f"    失败: {e}")

            # 方法3: 查找API调用
            print("\n🔍 方法3: 监听网络请求...")

            # 监听网络请求
            api_data = []

            def log_request(route):
                if 'api' in route.request.url.lower():
                    print(f"  API请求: {route.request.url}")
                route.continue_()

            page.route('**/*', log_request)

            # 刷新页面
            page.reload()
            page.wait_for_timeout(5000)

            browser.close()

    except Exception as e:
        print(f"❌ 错误: {e}")


def get_tracking_periods():
    """获取所有追踪期间的数据"""

    try:
        with sync_playwright() as p:
            print("\n" + "=" * 70)
            print("  📅 获取追踪期间数据")
            print("=" * 70)

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto('https://xtracker.polymarket.com/user/elonmusk', timeout=30000)
            page.wait_for_timeout(5000)

            # 查找追踪期间
            print("\n🔍 活跃的追踪期间:")

            periods = page.query_selector_all('[class*="period"], [class*="tracking"]')
            for period in periods:
                try:
                    text = period.inner_text()
                    if 'Feb' in text or 'Jan' in text:
                        print(f"\n  📅 {text[:200]}")
                except:
                    pass

            browser.close()

    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    extract_chart_data()
    get_tracking_periods()
