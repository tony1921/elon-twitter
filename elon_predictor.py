#!/usr/bin/env python3
"""
Elon Musk Tweet 预测系统 - MVP 版本
简化版：单文件运行，无需数据库

使用方法：
1. pip install requests beautifulsoup4 playwright numpy scipy
2. python elon_predictor.py

配置：编辑下面的 CONFIG 部分
"""

import requests
from bs4 import BeautifulSoup
import numpy as np
from scipy.stats import poisson, nbinom
from datetime import datetime, timedelta
import pytz
import time
import json
from pathlib import Path

# ============================================================
# CONFIG 配置区域 - 请根据需要修改
# ============================================================

CONFIG = {
    # Polymarket 市场信息（需要手动填写）
    'market_url': 'https://polymarket.com/event/elon-musk-of-tweets-january-2-january-9',

    # 时间窗口（手动填写，例如：January 2, 2026 12:00 PM ET）
    'window_start_et': '2026-01-02 12:00 PM',  # 格式：YYYY-MM-DD HH:MM AM/PM
    'window_end_et': '2026-01-09 12:00 PM',

    # XTracker URL
    'xtracker_url': 'https://xtracker.polymarket.com/user/elonmusk',

    # 抓取间隔（秒）
    'scrape_interval_seconds': 120,  # 默认 2 分钟

    # 模型类型
    'model_type': 'poisson',  # 'poisson' 或 'neg_binom'

    # 输出文件
    'output_file': 'predictions.json',

    # 是否显示详细日志
    'verbose': True,
}

# ============================================================
# 核心代码 - 不需要修改
# ============================================================


class ElonTweetPredictor:
    """Elon Musk 推文数量预测器"""

    def __init__(self, config: dict):
        self.config = config
        self.historical_data = self._load_historical_data()
        self.predictions_history = []

    def _load_historical_data(self) -> dict:
        """加载历史统计数据（简化版：使用固定先验）"""
        return {
            'avg_total_tweets': 400,  # 基于先验知识：Elon 平均每周约400条
            'avg_hourly_rate': 400 / (7 * 24),  # 每小时约 2.38 条
        }

    def parse_time_window(self) -> dict:
        """解析时间窗口"""
        et = pytz.timezone('America/New_York')
        utc = pytz.UTC

        # 解析 ET 时间
        start_et = et.localize(
            datetime.strptime(CONFIG['window_start_et'], '%Y-%m-%d %I:%M %p')
        )
        end_et = et.localize(
            datetime.strptime(CONFIG['window_end_et'], '%Y-%m-%d %I:%M %p')
        )

        # 转换为 UTC
        start_utc = start_et.astimezone(utc)
        end_utc = end_et.astimezone(utc)

        # 计算窗口总时长
        total_hours = (end_utc - start_utc).total_seconds() / 3600

        return {
            'start_et': start_et,
            'end_et': end_et,
            'start_utc': start_utc,
            'end_utc': end_utc,
            'total_hours': total_hours,
        }

    def scrape_xtracker(self) -> dict:
        """从 XTracker 抓取当前推文计数"""
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始抓取 XTracker...")
        print(f"URL: {self.config['xtracker_url']}")

        try:
            # 发送请求
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(
                self.config['xtracker_url'],
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            # 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 尝试多个选择器查找计数器
            count = None
            selectors = [
                '[data-testid="post-counter"]',
                '.post-count',
                '[class*="PostCounter"]',
                '[class*="tweet-count"]',
            ]

            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    # 提取数字
                    import re
                    match = re.search(r'\d+', text)
                    if match:
                        count = int(match.group())
                        print(f"✓ 成功提取计数: {count} (选择器: {selector})")
                        break

            if count is None:
                # 如果所有选择器都失败，尝试查找任何包含大数字的元素
                print("⚠ 未找到标准选择器，尝试智能搜索...")
                all_text = soup.get_text()
                numbers = re.findall(r'\d{3,}', all_text)  # 查找3位以上的数字
                if numbers:
                    count = int(numbers[0])
                    print(f"✓ 智能搜索找到计数: {count}")
                else:
                    raise ValueError("无法从页面提取推文计数")

            return {
                'current_count': count,
                'timestamp': datetime.now(pytz.UTC).isoformat(),
                'source': 'xtracker_scrape',
            }

        except Exception as e:
            print(f"✗ 抓取失败: {e}")
            raise

    def predict(self, current_count: int, elapsed_hours: float, remaining_hours: float) -> dict:
        """预测最终推文数量"""
        print(f"\n{'─'*60}")
        print("📊 预测计算:")
        print(f"  当前推文数: {current_count}")
        print(f"  已过时间: {elapsed_hours:.1f} 小时")
        print(f"  剩余时间: {remaining_hours:.1f} 小时")

        # 计算当前速率
        lambda_observed = current_count / elapsed_hours if elapsed_hours > 0 else 0
        lambda_prior = self.historical_data['avg_hourly_rate']

        # 动态权重（越接近结算，越信任观察数据）
        total_hours = elapsed_hours + remaining_hours
        progress_pct = (elapsed_hours / total_hours) * 100 if total_hours > 0 else 0
        w = min(1.0, progress_pct / 50)

        lambda_combined = w * lambda_observed + (1 - w) * lambda_prior

        print(f"\n  速率估计:")
        print(f"    观察速率: {lambda_observed:.2f} 条/小时")
        print(f"    先验速率: {lambda_prior:.2f} 条/小时")
        print(f"    融合速率: {lambda_combined:.2f} 条/小时 (权重 w={w:.2f})")

        # 预测未来推文数
        lambda_future = lambda_combined * remaining_hours

        if self.config['model_type'] == 'poisson':
            future_dist = self._predict_poisson(lambda_future)
        else:
            future_dist = self._predict_neg_binom(lambda_future)

        # 计算总数统计
        expected_total = current_count + future_dist['mean']
        ci80_lower = current_count + future_dist['ci80_lower']
        ci80_upper = current_count + future_dist['ci80_upper']
        ci90_lower = current_count + future_dist['ci90_lower']
        ci90_upper = current_count + future_dist['ci90_upper']

        print(f"\n  预测结果:")
        print(f"    期望总数: {expected_total:.1f} 条")
        print(f"    80% 置信区间: [{ci80_lower:.0f}, {ci80_upper:.0f}]")
        print(f"    90% 置信区间: [{ci90_lower:.0f}, {ci90_upper:.0f}]")

        return {
            'expected_total': expected_total,
            'ci80_lower': ci80_lower,
            'ci80_upper': ci80_upper,
            'ci90_lower': ci90_lower,
            'ci90_upper': ci90_upper,
            'lambda_combined': lambda_combined,
            'progress_pct': progress_pct,
        }

    def _predict_poisson(self, lambda_total: float) -> dict:
        """Poisson 分布预测"""
        dist = poisson(mu=lambda_total)
        return {
            'mean': dist.mean(),
            'variance': dist.var(),
            'ci80_lower': dist.ppf(0.1),
            'ci80_upper': dist.ppf(0.9),
            'ci90_lower': dist.ppf(0.05),
            'ci90_upper': dist.ppf(0.95),
        }

    def _predict_neg_binom(self, lambda_total: float) -> dict:
        """Negative Binomial 分布预测"""
        alpha = 0.1  # 过度离散参数
        n = 1 / alpha
        p = 1 / (1 + alpha * lambda_total)

        dist = nbinom(n=n, p=p)
        return {
            'mean': dist.mean(),
            'variance': dist.var(),
            'ci80_lower': dist.ppf(0.1),
            'ci80_upper': dist.ppf(0.9),
            'ci90_lower': dist.ppf(0.05),
            'ci90_upper': dist.ppf(0.95),
        }

    def map_to_buckets(self, expected_total: float) -> dict:
        """将预测映射到 Polymarket 区间"""
        # 简化版：生成常见区间
        buckets = {}
        base = 160
        step = 20

        for i in range(22):  # 22 个区间
            if i < 21:
                bucket_name = f"{base + i*step}-{base + (i+1)*step - 1}"
            else:
                bucket_name = f"{base + i*step}+"

            # 简化概率计算：使用正态分布近似
            from scipy.stats import norm
            if i < 21:
                lower = base + i*step - expected_total
                upper = base + (i+1)*step - 1 - expected_total
                prob = norm.cdf(upper, scale=50) - norm.cdf(lower, scale=50)
            else:
                lower = base + i*step - expected_total
                prob = 1 - norm.cdf(lower, scale=50)

            buckets[bucket_name] = max(0, prob)

        # 归一化
        total = sum(buckets.values())
        buckets = {k: v/total for k, v in buckets.items()}

        # 显示前 5 个最可能的区间
        sorted_buckets = sorted(buckets.items(), key=lambda x: -x[1])[:5]
        print(f"\n  最可能的区间:")
        for bucket, prob in sorted_buckets:
            print(f"    {bucket:>10s}: {prob*100:5.2f}%")

        return buckets

    def save_prediction(self, prediction: dict):
        """保存预测到文件"""
        self.predictions_history.append(prediction)

        # 保存到 JSON
        output_file = Path(self.config['output_file'])
        with open(output_file, 'w') as f:
            json.dump(self.predictions_history, f, indent=2, default=str)

        print(f"\n✓ 预测已保存到: {output_file}")

    def run_once(self) -> dict:
        """运行一次预测"""
        # 解析时间窗口
        window = self.parse_time_window()
        print(f"\n时间窗口:")
        print(f"  开始 (ET): {window['start_et'].strftime('%Y-%m-%d %I:%M %p %Z')}")
        print(f"  结束 (ET): {window['end_et'].strftime('%Y-%m-%d %I:%M %p %Z')}")
        print(f"  总时长: {window['total_hours']:.1f} 小时")

        # 抓取当前计数
        snapshot = self.scrape_xtracker()

        # 计算时间进度
        now = datetime.now(pytz.UTC)
        elapsed = (now - window['start_utc']).total_seconds() / 3600
        remaining = (window['end_utc'] - now).total_seconds() / 3600

        if remaining < 0:
            print(f"\n⚠ 市场已关闭！最终计数: {snapshot['current_count']}")
            return snapshot

        # 预测
        prediction_result = self.predict(
            snapshot['current_count'],
            elapsed,
            remaining
        )

        # 映射到区间
        buckets = self.map_to_buckets(prediction_result['expected_total'])

        # 组合结果
        result = {
            'timestamp': snapshot['timestamp'],
            'current_count': snapshot['current_count'],
            'elapsed_hours': elapsed,
            'remaining_hours': remaining,
            'progress_pct': prediction_result['progress_pct'],
            'prediction': prediction_result,
            'buckets': buckets,
        }

        # 保存
        self.save_prediction(result)

        return result

    def run_continuous(self):
        """持续运行（定时抓取）"""
        print(f"\n{'='*60}")
        print("🚀 Elon Musk Tweet 预测系统启动")
        print(f"抓取间隔: {self.config['scrape_interval_seconds']} 秒")
        print(f"按 Ctrl+C 停止")
        print(f"{'='*60}")

        try:
            while True:
                try:
                    self.run_once()

                except Exception as e:
                    print(f"\n✗ 错误: {e}")
                    import traceback
                    traceback.print_exc()

                # 等待下一次抓取
                print(f"\n⏰ 下次抓取在 {self.config['scrape_interval_seconds']} 秒后...")
                time.sleep(self.config['scrape_interval_seconds'])

        except KeyboardInterrupt:
            print(f"\n\n⏹ 用户停止，程序退出")


# ============================================================
# 主程序
# ============================================================

def main():
    """主程序"""
    print("""
╔════════════════════════════════════════════════════════════╗
║     Elon Musk Tweet Prediction System - MVP              ║
║           Polymarket 市场实时预测工具                       ║
╚════════════════════════════════════════════════════════════╝
    """)

    # 检查配置
    print("⚙️  当前配置:")
    print(f"  市场URL: {CONFIG['market_url']}")
    print(f"  窗口开始: {CONFIG['window_start_et']} ET")
    print(f"  窗口结束: {CONFIG['window_end_et']} ET")
    print(f"  抓取间隔: {CONFIG['scrape_interval_seconds']} 秒")
    print(f"  模型类型: {CONFIG['model_type']}")

    # 创建预测器
    predictor = ElonTweetPredictor(CONFIG)

    # 询问用户运行模式
    print("\n请选择运行模式:")
    print("  1. 单次运行（测试）")
    print("  2. 持续运行（定时抓取）")

    choice = input("\n请输入选项 (1/2，默认1): ").strip() or "1"

    if choice == "1":
        predictor.run_once()
    else:
        predictor.run_continuous()


if __name__ == "__main__":
    main()
