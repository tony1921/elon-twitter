#!/usr/bin/env python3
"""
获取Elon Musk的历史追踪数据
"""

from playwright.sync_api import sync_playwright
import json
import re
from datetime import datetime

def get_elon_history():
    """获取Elon Musk的历史数据"""

    try:
        with sync_playwright() as p:
            print("=" * 70)
            print("  🔍 获取 Elon Musk 历史数据")
            print("=" * 70)

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 访问Elon Musk页面
            url = 'https://xtracker.polymarket.com/user/elonmusk'
            print(f"\n📡 访问: {url}")
            page.goto(url, timeout=30000)
            page.wait_for_timeout(5000)

            # 获取页面文本
            text = page.inner_text('body')
            print(f"\n📄 页面内容:\n{text[:1000]}")

            # 查找所有数字
            numbers = re.findall(r'\b\d+\b', text)
            print(f"\n🔢 找到的数字: {numbers[:20]}")

            # 查找可能的追踪期间
            print("\n🔍 查找追踪期间...")

            # 尝试查找列表、表格等
            periods = page.query_selector_all('[class*="period"], [class*="tracking"], li, tr')
            print(f"\n  找到 {len(periods)} 个可能的元素")

            for i, el in enumerate(periods[:10]):
                try:
                    el_text = el.inner_text()[:100]
                    print(f"  [{i}] {el_text}")
                except:
                    pass

            # 查找时间范围
            print("\n📅 查找时间范围...")
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}',
                r'\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',
            ]

            for pattern in date_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    print(f"  日期匹配: {matches}")

            # 检查是否有API调用
            print("\n🔍 检查API...")
            html = page.content()
            api_urls = re.findall(r'"url"\s*:\s*"([^"]*)"', html)
            if api_urls:
                print(f"  找到API: {api_urls}")

            # 截图保存
            screenshot_path = 'data/elonmusk_page.png'
            page.screenshot(path=screenshot_path)
            print(f"\n📸 截图已保存: {screenshot_path}")

            browser.close()

    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    get_elon_history()
