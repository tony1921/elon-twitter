#!/usr/bin/env python3
"""
检查XTracker是否有历史数据
"""

from playwright.sync_api import sync_playwright
import re

def check_xtracker_history():
    """检查XTracker是否有历史数据"""

    try:
        with sync_playwright() as p:
            print("=" * 70)
            print("  🔍 检查 XTracker 历史数据")
            print("=" * 70)

            browser = p.chromium.launch(headless=False)  # 使用有界面模式，方便观察
            page = browser.new_page()

            print("\n📡 访问 XTracker...")
            page.goto('https://xtracker.polymarket.com', timeout=30000)

            # 等待页面加载
            page.wait_for_timeout(5000)

            # 查找可能的链接和按钮
            print("\n🔍 查找历史数据相关元素...")

            # 查找所有链接
            links = page.query_selector_all('a')
            print(f"\n  找到 {len(links)} 个链接:")

            history_keywords = ['history', 'past', 'archive', 'previous', 'stats', 'data', 'chart', 'graph']

            for link in links[:20]:  # 只显示前20个
                try:
                    text = link.inner_text().strip()
                    href = link.get_attribute('href')
                    if text:
                        print(f"    - {text[:50]} -> {href}")
                except:
                    pass

            # 查找可能包含历史数据的元素
            print("\n🔍 查找数据元素...")

            # 尝试查找图表、表格等
            selectors = [
                '[class*="chart"]',
                '[class*="graph"]',
                '[class*="history"]',
                '[class*="stats"]',
                'table',
                '[role="table"]',
            ]

            for selector in selectors:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"\n  找到 {len(elements)} 个 '{selector}' 元素")
                    for el in elements[:3]:
                        try:
                            text = el.inner_text()[:100]
                            print(f"    内容: {text}")
                        except:
                            pass

            # 检查页面源代码中是否有API端点
            print("\n🔍 检查网络请求...")
            html = page.content()

            # 查找可能的API
            api_patterns = [
                r'https://[^\s"\']*api[^\s"\']*',
                r'https://[^\s"\']*history[^\s"\']*',
                r'https://[^\s"\']*stats[^\s"\']*',
            ]

            for pattern in api_patterns:
                matches = re.findall(pattern, html)
                if matches:
                    print(f"  找到API: {set(matches)}")

            print("\n" + "=" * 70)
            print("  浏览器将保持打开30秒，请手动查看页面...")
            print("  查看是否有历史数据、图表、统计等链接")
            print("=" * 70)

            page.wait_for_timeout(30000)  # 保持30秒让用户查看

            browser.close()

    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    check_xtracker_history()
