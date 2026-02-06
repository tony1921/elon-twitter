#!/usr/bin/env python3
"""
尝试从XTracker获取数据 - 多种方法
"""

import requests
import json
import re

def try_api_method():
    """尝试API方法"""
    print("📡 方法1: 尝试API接口...")

    # XTracker可能的API端点
    api_urls = [
        'https://xtracker.polymarket.com/api/posts',
        'https://xtracker.polymarket.com/api/stats',
        'https://xtracker.polymarket.com/api/data',
        'https://api.polymarket.com/xtracker',
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
    }

    for url in api_urls:
        try:
            print(f"  尝试: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"  ✅ 成功! 状态码: {response.status_code}")
                print(f"  数据: {response.text[:500]}")
                return response.json()
        except Exception as e:
            print(f"  ❌ 失败: {e}")

    return None


def try_json_in_html():
    """尝试从HTML中提取JSON数据"""
    print("\n📄 方法2: 从HTML中提取JSON...")

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        response = requests.get('https://xtracker.polymarket.com', headers=headers, timeout=30)
        response.raise_for_status()

        html = response.text

        # 查找JSON数据（Next.js常用方式）
        patterns = [
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
            r'window\.__DATA__\s*=\s*({.*?});',
            r'data-testid="tweet-count"[^>]*>(\d+)</',
            r'"count":\s*(\d+)',
            r'"posts":\s*(\d+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            if matches:
                print(f"  ✅ 找到匹配: {pattern[:50]}...")
                for match in matches[:3]:  # 只显示前3个
                    print(f"    数据: {match[:200]}")
                return matches

        print("  ❌ 未找到JSON数据")

    except Exception as e:
        print(f"  ❌ 错误: {e}")

    return None


def try_playwright():
    """尝试使用Playwright（需要安装）"""
    print("\n🎭 方法3: 尝试Playwright浏览器自动化...")

    try:
        from playwright.sync_api import sync_playwright

        print("  Playwright已安装，启动浏览器...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://xtracker.polymarket.com', timeout=30000)

            # 等待页面加载
            page.wait_for_timeout(3000)

            # 获取页面文本
            text = page.inner_text('body')

            # 查找数字
            numbers = re.findall(r'\b\d{2,4}\b', text)
            if numbers:
                print(f"  ✅ 找到数字: {numbers}")

                # 尝试获取特定元素
                try:
                    count_element = page.query_selector('[data-testid="tweet-count"], .post-count, h1, h2')
                    if count_element:
                        count_text = count_element.inner_text()
                        print(f"  ✅ 元素文本: {count_text}")
                except:
                    pass

                browser.close()
                return numbers

            browser.close()

    except ImportError:
        print("  ⚠️  Playwright未安装")
        print("  安装方法: pip3 install playwright && playwright install chromium")
        return None
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return None


def main():
    print("=" * 70)
    print("  🔍 XTracker 数据抓取测试")
    print("=" * 70)

    # 方法1: API
    result = try_api_method()

    # 方法2: JSON
    if not result:
        result = try_json_in_html()

    # 方法3: Playwright
    if not result:
        result = try_playwright()

    print("\n" + "=" * 70)
    if result:
        print("✅ 抓取成功！")
        print(f"结果: {result}")
    else:
        print("❌ 所有方法都失败了")
        print("\n建议:")
        print("1. 安装Playwright: pip3 install playwright && playwright install chromium")
        print("2. 或者使用手动记录: python3 quick_record.py <数量>")
    print("=" * 70)


if __name__ == "__main__":
    main()
