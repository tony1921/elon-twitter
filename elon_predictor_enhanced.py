#!/usr/bin/env python3
"""
Elon Musk Tweet 预测系统 - 完整增强版
================================================
整合了自动抓取、统计模型、智能推荐、趋势分析等所有功能

使用方法：
1. pip install requests beautifulsoup4 playwright numpy scipy pytz
2. python elon_predictor_enhanced.py
"""

import requests
from bs4 import BeautifulSoup
import numpy as np
from scipy.stats import poisson, nbinom, norm
from datetime import datetime, timedelta
import pytz
import time
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ============================================================
# CONFIG 配置区域
# ============================================================

CONFIG = {
    # 当前市场配置 - Elon Musk # tweets February 5 - February 7, 2026
    'market_url': 'https://polymarket.com/event/elon-musk-of-tweets-february-5-february-7/elon-musk-of-tweets-february-5-february-7-0-39',

    # 时间窗口
    'window_start_et': '2026-02-05 12:00 PM',
    'window_end_et': '2026-02-07 12:00 PM',

    # XTracker URL
    'xtracker_url': 'https://xtracker.polymarket.com',

    # 抓取间隔（秒）
    'scrape_interval_seconds': 120,

    # 模型类型
    'model_type': 'poisson',  # 'poisson' 或 'neg_binom'

    # 输出文件
    'output_file': 'predictions.json',
    'history_file': 'monitoring_history.json',

    # 是否显示详细日志
    'verbose': True,

    # 周末调整系数
    'weekend_boost': 1.1,

    # 数据和日志目录
    'data_dir': 'data',
    'logs_dir': 'logs',
}

# ============================================================
# Polymarket 市场区间配置
# ============================================================

POLYMARKET_BUCKETS = [
    '<40',
    '40-64',
    '65-89',
    '90-114',
    '115-139',
    '140-164',
    '165-189',
    '190-214',
    '215-239',
    '240+',
]

# ============================================================
# 核心类定义
# ============================================================


class EnhancedTweetPredictor:
    """增强版 Elon Musk 推文预测器"""

    def __init__(self, config: dict):
        self.config = config
        self.predictions_history = []
        self.ensure_directories()

    def ensure_directories(self):
        """确保必要的目录存在"""
        for dir_name in [self.config['data_dir'], self.config['logs_dir']]:
            os.makedirs(dir_name, exist_ok=True)

    def log_message(self, message: str):
        """记录日志到文件和控制台"""
        if self.config['verbose']:
            print(message)

        # 保存到日志文件
        log_file = os.path.join(
            self.config['logs_dir'],
            f"predictor_{datetime.now().strftime('%Y%m%d')}.log"
        )
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    # ========================================================
    # 数据加载与保存
    # ========================================================

    def load_historical_data(self) -> dict:
        """加载历史统计数据（先验知识）"""
        return {
            'avg_total_tweets': 400,  # 基于历史：Elon 平均每周约400条
            'avg_hourly_rate': 400 / (7 * 24),  # 每小时约 2.38 条
        }

    def load_history(self) -> List[dict]:
        """加载历史预测记录"""
        history_file = os.path.join(self.config['data_dir'], self.config['history_file'])
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_prediction(self, prediction: dict):
        """保存预测到历史记录"""
        self.predictions_history.append(prediction)

        # 保存到 JSON
        history_file = os.path.join(self.config['data_dir'], self.config['history_file'])
        history = self.load_history()
        history.append(prediction)

        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False, default=str)

        self.log_message(f"✓ 预测已保存到: {history_file}")

    # ========================================================
    # 时间与窗口解析
    # ========================================================

    def parse_time_window(self) -> dict:
        """解析时间窗口"""
        et = pytz.timezone('America/New_York')
        utc = pytz.UTC

        # 解析 ET 时间
        start_et = et.localize(
            datetime.strptime(self.config['window_start_et'], '%Y-%m-%d %I:%M %p')
        )
        end_et = et.localize(
            datetime.strptime(self.config['window_end_et'], '%Y-%m-%d %I:%M %p')
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

    def count_weekend_hours(self, start_utc: datetime, end_utc: datetime) -> int:
        """计算周末小时数"""
        weekend_hours = 0
        current = start_utc
        while current < end_utc:
            if current.weekday() >= 5:  # 周六=5, 周日=6
                weekend_hours += 1
            current += timedelta(hours=1)
        return weekend_hours

    # ========================================================
    # 数据抓取
    # ========================================================

    def scrape_xtracker(self) -> Optional[dict]:
        """从 XTracker 抓取当前推文计数"""
        self.log_message(f"\n{'='*60}")
        self.log_message(f"[{datetime.now().strftime('%H:%M:%S')}] 开始抓取 XTracker...")
        self.log_message(f"URL: {self.config['xtracker_url']}")

        try:
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
                    match = re.search(r'\d+', text)
                    if match:
                        count = int(match.group())
                        self.log_message(f"✓ 成功提取计数: {count} (选择器: {selector})")
                        break

            if count is None:
                # 智能搜索
                self.log_message("⚠ 未找到标准选择器，尝试智能搜索...")
                all_text = soup.get_text()
                numbers = re.findall(r'\d{2,4}', all_text)
                if numbers:
                    count = int(numbers[0])
                    self.log_message(f"✓ 智能搜索找到计数: {count}")
                else:
                    raise ValueError("无法从页面提取推文计数")

            return {
                'current_count': count,
                'timestamp': datetime.now(pytz.UTC).isoformat(),
                'source': 'xtracker_scrape',
            }

        except Exception as e:
            self.log_message(f"✗ 抓取失败: {e}")
            return None

    # ========================================================
    # 预测模型
    # ========================================================

    def predict(self, current_count: int, elapsed_hours: float, remaining_hours: float) -> dict:
        """预测最终推文数量"""
        self.log_message(f"\n{'─'*60}")
        self.log_message("📊 预测计算:")
        self.log_message(f"  当前推文数: {current_count}")
        self.log_message(f"  已过时间: {elapsed_hours:.1f} 小时")
        self.log_message(f"  剩余时间: {remaining_hours:.1f} 小时")

        # 计算当前速率
        lambda_observed = current_count / elapsed_hours if elapsed_hours > 0 else 0
        lambda_prior = self.load_historical_data()['avg_hourly_rate']

        # 动态权重
        total_hours = elapsed_hours + remaining_hours
        progress_pct = (elapsed_hours / total_hours) * 100 if total_hours > 0 else 0
        w = min(1.0, progress_pct / 50)

        lambda_combined = w * lambda_observed + (1 - w) * lambda_prior

        self.log_message(f"\n  速率估计:")
        self.log_message(f"    观察速率: {lambda_observed:.2f} 条/小时")
        self.log_message(f"    先验速率: {lambda_prior:.2f} 条/小时")
        self.log_message(f"    融合速率: {lambda_combined:.2f} 条/小时 (权重 w={w:.2f})")

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

        # 线性预测（简单方法）
        predicted_linear = int(lambda_observed * total_hours) if elapsed_hours > 0 else 0

        # 保守预测
        conservative_factor = 0.9
        predicted_conservative = int(current_count + (lambda_observed * remaining_hours * conservative_factor))

        # 周末调整预测
        window = self.parse_time_window()
        weekend_hours = self.count_weekend_hours(window['start_utc'], window['end_utc'])
        if weekend_hours > 0:
            predicted_weekend = int(current_count + (lambda_observed * remaining_hours * self.config['weekend_boost']))
            self.log_message(f"    检测到周末: {weekend_hours} 小时")
        else:
            predicted_weekend = predicted_conservative

        self.log_message(f"\n  预测结果:")
        self.log_message(f"    期望总数: {expected_total:.1f} 条")
        self.log_message(f"    线性预测: {predicted_linear} 条")
        self.log_message(f"    保守预测: {predicted_conservative} 条")
        self.log_message(f"    周末调整: {predicted_weekend} 条")
        self.log_message(f"    80% 置信区间: [{ci80_lower:.0f}, {ci80_upper:.0f}]")
        self.log_message(f"    90% 置信区间: [{ci90_lower:.0f}, {ci90_upper:.0f}]")

        return {
            'expected_total': expected_total,
            'predicted_linear': predicted_linear,
            'predicted_conservative': predicted_conservative,
            'predicted_weekend': predicted_weekend,
            'ci80_lower': ci80_lower,
            'ci80_upper': ci80_upper,
            'ci90_lower': ci90_lower,
            'ci90_upper': ci90_upper,
            'lambda_combined': lambda_combined,
            'progress_pct': progress_pct,
            'daily_rate': lambda_observed * 24,
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
        alpha = 0.1
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

    # ========================================================
    # 区间映射
    # ========================================================

    def map_to_buckets(self, expected_total: float, std_dev: float = 50) -> Dict[str, float]:
        """将预测映射到 Polymarket 区间"""
        buckets = {}

        # 定义区间边界
        bucket_ranges = [
            ('<40', 0, 39),
            ('40-64', 40, 64),
            ('65-89', 65, 89),
            ('90-114', 90, 114),
            ('115-139', 115, 139),
            ('140-164', 140, 164),
            ('165-189', 165, 189),
            ('190-214', 190, 214),
            ('215-239', 215, 239),
            ('240+', 240, 1000),
        ]

        # 计算每个区间的概率（使用正态分布近似）
        for name, lower, upper in bucket_ranges:
            if name == '240+':
                # 最后一个区间：从 lower 到无穷
                z_lower = (lower - expected_total) / std_dev
                prob = 1 - norm.cdf(z_lower)
            else:
                # 普通区间：[lower, upper]
                z_lower = (lower - expected_total) / std_dev
                z_upper = (upper - expected_total) / std_dev
                prob = norm.cdf(z_upper) - norm.cdf(z_lower)

            buckets[name] = max(0, prob)

        # 归一化
        total = sum(buckets.values())
        if total > 0:
            buckets = {k: v/total for k, v in buckets.items()}

        # 显示前 5 个最可能的区间
        sorted_buckets = sorted(buckets.items(), key=lambda x: -x[1])[:5]
        self.log_message(f"\n  最可能的区间:")
        for bucket, prob in sorted_buckets:
            self.log_message(f"    {bucket:>10s}: {prob*100:5.2f}%")

        return buckets

    # ========================================================
    # 趋势分析
    # ========================================================

    def analyze_trend(self, history: List[dict]) -> dict:
        """分析预测趋势"""
        if len(history) < 2:
            return {
                'direction': '数据不足',
                'stability': '数据不足',
                'recommendation': '需要至少2次预测',
            }

        # 获取最近的预测
        recent = history[-5:] if len(history) >= 5 else history
        conservative_preds = [p.get('predicted_conservative', 0) for p in recent]

        # 计算趋势
        n = len(conservative_preds)
        x = list(range(n))
        y = conservative_preds

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i]**2 for i in range(n))

        if n * sum_x2 - sum_x**2 != 0:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
        else:
            slope = 0

        # 判断方向
        if slope > 2:
            direction = "↗️ 强劲上升"
        elif slope > 0.5:
            direction = "↗️ 上升"
        elif slope > -0.5:
            direction = "➡️ 稳定"
        elif slope > -2:
            direction = "↘️ 下降"
        else:
            direction = "↘️ 快速下降"

        # 计算稳定性
        mean = sum(y) / len(y)
        variance = sum((v - mean)**2 for v in y) / len(y)
        std_dev = variance ** 0.5

        cv = (std_dev / mean) * 100 if mean != 0 else 0

        if cv < 5:
            stability = "非常稳定"
        elif cv < 10:
            stability = "稳定"
        elif cv < 20:
            stability = "中等波动"
        else:
            stability = "高波动"

        return {
            'direction': direction,
            'stability': stability,
            'slope': slope,
            'cv': cv,
        }

    # ========================================================
    # 智能推荐
    # ========================================================

    def get_recommendation(self, prediction: dict, history: List[dict]) -> dict:
        """基于预测和历史给出下注建议"""
        current_pred = prediction['predicted_conservative']
        completion = prediction['progress_pct']

        # 趋势分析
        trend = self.analyze_trend(history) if len(history) >= 2 else {
            'direction': '数据不足',
            'stability': '数据不足'
        }

        # 确定推荐区间
        recommendation = {
            '主推荐': '',
            '次推荐': '',
            '避免': '',
            '置信度': '',
            '理由': [],
            '趋势分析': trend,
        }

        # 根据预测值推荐
        if current_pred < 40:
            recommendation['主推荐'] = '<40'
            recommendation['次推荐'] = '40-64'
            recommendation['避免'] = '90+'
            recommendation['置信度'] = '高' if '稳定' in trend['stability'] else '中等'
            recommendation['理由'].append('预测值低于40，极低区间')

        elif 40 <= current_pred < 65:
            recommendation['主推荐'] = '40-64'
            recommendation['次推荐'] = '65-89'
            recommendation['避免'] = '115+'
            recommendation['置信度'] = '高'
            recommendation['理由'].append('预测值在40-64区间内')

        elif 65 <= current_pred < 90:
            recommendation['主推荐'] = '65-89'
            recommendation['次推荐'] = '90-114'
            recommendation['避免'] = '<40'
            recommendation['置信度'] = '高'
            recommendation['理由'].append('预测值在65-89区间内')

        elif 90 <= current_pred < 115:
            recommendation['主推荐'] = '90-114'
            recommendation['次推荐'] = '65-89 或 115-139'
            recommendation['避免'] = '<40'
            recommendation['置信度'] = '高'
            recommendation['理由'].append('预测值在90-114区间内')

        elif 115 <= current_pred < 140:
            recommendation['主推荐'] = '115-139'
            recommendation['次推荐'] = '90-114 或 140-164'
            recommendation['避免'] = '<65'
            recommendation['置信度'] = '中等'
            recommendation['理由'].append('预测值在115-139区间内')

        elif 140 <= current_pred < 165:
            recommendation['主推荐'] = '140-164'
            recommendation['次推荐'] = '115-139'
            recommendation['避免'] = '<90'
            recommendation['置信度'] = '中等'
            recommendation['理由'].append('预测值在140-164区间内')

        elif 165 <= current_pred < 190:
            recommendation['主推荐'] = '165-189'
            recommendation['次推荐'] = '140-164 或 190-214'
            recommendation['避免'] = '<115'
            recommendation['置信度'] = '中等'
            recommendation['理由'].append('预测值在165-189区间内')

        else:  # 190+
            recommendation['主推荐'] = '190-214'
            recommendation['次推荐'] = '215-239 或 240+'
            recommendation['避免'] = '<140'
            recommendation['置信度'] = '低'
            recommendation['理由'].append('预测值超过190，高风险')

        # 根据趋势调整
        if '上升' in trend['direction']:
            recommendation['理由'].append('预测呈上升趋势，考虑下注更高区间')
        elif '下降' in trend['direction']:
            recommendation['理由'].append('预测呈下降趋势，考虑下注更低区间')
        elif '稳定' in trend['stability']:
            recommendation['置信度'] = '高'
            recommendation['理由'].append('预测稳定，置信度高')

        # 完成度建议
        if completion < 20:
            recommendation['理由'].append(f'⚠️ 仅完成{completion:.0f}%，建议等待更多数据')
        elif 20 <= completion < 50:
            recommendation['理由'].append(f'✓ 完成{completion:.0f}%，可以小注试探（25%预算）')
        elif 50 <= completion < 80:
            recommendation['理由'].append(f'✓✓ 完成{completion:.0f}%，最佳下注时机（50%预算）')
        else:
            recommendation['理由'].append(f'✓✓✓ 完成{completion:.0f}%，最后调整机会')

        return recommendation

    # ========================================================
    # 显示功能
    # ========================================================

    def display_recommendation(self, prediction: dict, recommendation: dict, current_count: int):
        """显示推荐报告"""
        print("\n" + "="*70)
        print("🤖 Elon Musk 推文预测系统 - 智能推荐")
        print("="*70)
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*70)

        # 显示当前数据
        print("\n📊 当前数据:")
        print(f"   当前推文数: {current_count}")
        print(f"   日均推文:   {prediction['daily_rate']:.1f} 条/天")
        window = self.parse_time_window()
        elapsed = (datetime.now(pytz.UTC) - window['start_utc']).total_seconds() / 3600
        total = window['total_hours']
        print(f"   已过时间:   {elapsed:.1f} 小时 ({elapsed/24:.1f} 天)")
        print(f"   完成度:     {prediction['progress_pct']:.1f}%")

        # 显示预测结果
        print("\n📈 预测结果:")
        print(f"   线性预测:     {prediction['predicted_linear']} 条")
        print(f"   保守预测:     {prediction['predicted_conservative']} 条")
        print(f"   周末调整:     {prediction['predicted_weekend']} 条")
        print(f"   统计期望:     {prediction['expected_total']:.1f} 条")
        print(f"   80% 置信区间: [{prediction['ci80_lower']:.0f}, {prediction['ci80_upper']:.0f}]")

        # 显示趋势分析
        print("\n📉 趋势分析:")
        print(f"   方向: {recommendation['趋势分析']['direction']}")
        print(f"   稳定性: {recommendation['趋势分析']['stability']}")

        # 显示下注建议
        print("\n" + "="*70)
        print("💡 下注建议")
        print("="*70)

        print(f"\n   ✅ 主推荐区间: {recommendation['主推荐']}")
        if recommendation['次推荐']:
            print(f"   ✅ 次推荐区间: {recommendation['次推荐']}")
        if recommendation['避免']:
            print(f"   ❌ 避免区间:   {recommendation['避免']}")

        print(f"\n   🎯 置信度: {recommendation['置信度']}")

        print("\n   📝 理由:")
        for i, reason in enumerate(recommendation['理由'], 1):
            print(f"      {i}. {reason}")

        # 显示行动建议
        print("\n" + "-"*70)
        print("🎬 行动建议:")

        completion = prediction['progress_pct']
        if completion < 20:
            print("   ⏸️  建议：暂不下注，等待更多数据")
            print("   📅 下次检查时间：6-12小时后")
        elif 20 <= completion < 50:
            print("   💰 建议：可以小注（25%预算）")
            print("   🎲 优先考虑：主推荐区间")
            print("   📅 下次检查时间：12-24小时后")
        elif 50 <= completion < 80:
            print("   💰💰 建议：增加下注（50%预算）")
            print("   🎲 如果趋势稳定：可以投入更多")
            print("   📅 下次检查时间：12-24小时后")
        else:
            print("   💰💰💰 建议：最后机会，调整下注")
            print("   🎲 根据当前数据做最终决定")
            print("   📅 下次检查时间：6-12小时后（结束前）")

        print("\n" + "="*70)

    def show_history(self):
        """显示历史预测"""
        history = self.load_history()

        if not history:
            print("\n还没有历史预测记录")
            return

        print("\n" + "="*70)
        print("📜 历史预测记录（最近10次）")
        print("="*70)

        for i, record in enumerate(history[-10:], 1):
            print(f"\n记录 #{i}")
            print(f"时间: {record.get('timestamp', 'N/A')}")
            print(f"当前推文: {record.get('current_count', 'N/A')}")
            print(f"已过时间: {record.get('elapsed_hours', 0):.1f} 小时")
            print(f"保守预测: {record.get('predicted_conservative', 'N/A')}")
            print("-"*70)

    def open_polymarket(self):
        """打开 Polymarket 网站"""
        try:
            subprocess.run(['open', self.config['market_url']], check=True)
            print("\n✓ 已在浏览器中打开 Polymarket 市场")
        except:
            print(f"\n请手动打开浏览器访问: {self.config['market_url']}")

    # ========================================================
    # 核心运行逻辑
    # ========================================================

    def run_with_count(self, count: int) -> dict:
        """使用指定推文数量运行预测"""
        # 解析时间窗口
        window = self.parse_time_window()
        self.log_message(f"\n时间窗口:")
        self.log_message(f"  开始 (ET): {window['start_et'].strftime('%Y-%m-%d %I:%M %p %Z')}")
        self.log_message(f"  结束 (ET): {window['end_et'].strftime('%Y-%m-%d %I:%M %p %Z')}")
        self.log_message(f"  总时长: {window['total_hours']:.1f} 小时")

        # 使用指定的计数
        current_count = count

        # 计算时间进度
        now = datetime.now(pytz.UTC)
        elapsed = (now - window['start_utc']).total_seconds() / 3600
        remaining = (window['end_utc'] - now).total_seconds() / 3600

        if remaining < 0:
            self.log_message(f"\n⚠ 市场已关闭！最终计数: {current_count}")
            return {'current_count': current_count, 'market_closed': True}

        # 预测
        prediction_result = self.predict(current_count, elapsed, remaining)

        # 映射到区间
        buckets = self.map_to_buckets(prediction_result['expected_total'])

        # 加载历史并获取推荐
        history = self.load_history()
        recommendation = self.get_recommendation(prediction_result, history)

        # 显示推荐
        self.display_recommendation(prediction_result, recommendation, current_count)

        # 组合结果
        result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_count': current_count,
            'elapsed_hours': elapsed,
            'remaining_hours': remaining,
            'progress_pct': prediction_result['progress_pct'],
            'predicted_linear': prediction_result['predicted_linear'],
            'predicted_conservative': prediction_result['predicted_conservative'],
            'predicted_weekend': prediction_result['predicted_weekend'],
            'expected_total': prediction_result['expected_total'],
            'ci80_lower': prediction_result['ci80_lower'],
            'ci80_upper': prediction_result['ci80_upper'],
            'ci90_lower': prediction_result['ci90_lower'],
            'ci90_upper': prediction_result['ci90_upper'],
            'daily_rate': prediction_result['daily_rate'],
            'buckets': buckets,
            'recommendation': recommendation,
        }

        # 保存
        self.save_prediction(result)

        return result

    def run_once(self, manual_input: bool = False) -> dict:
        """运行一次预测"""
        # 解析时间窗口
        window = self.parse_time_window()
        self.log_message(f"\n时间窗口:")
        self.log_message(f"  开始 (ET): {window['start_et'].strftime('%Y-%m-%d %I:%M %p %Z')}")
        self.log_message(f"  结束 (ET): {window['end_et'].strftime('%Y-%m-%d %I:%M %p %Z')}")
        self.log_message(f"  总时长: {window['total_hours']:.1f} 小时")

        # 获取当前计数
        if manual_input:
            current_count = int(input("\n请输入当前推文数量: "))
        else:
            snapshot = self.scrape_xtracker()
            if not snapshot:
                print("无法获取数据，请手动输入：")
                current_count = int(input("当前推文数量: "))
            else:
                current_count = snapshot['current_count']

        # 计算时间进度
        now = datetime.now(pytz.UTC)
        elapsed = (now - window['start_utc']).total_seconds() / 3600
        remaining = (window['end_utc'] - now).total_seconds() / 3600

        if remaining < 0:
            self.log_message(f"\n⚠ 市场已关闭！最终计数: {current_count}")
            return {'current_count': current_count, 'market_closed': True}

        # 预测
        prediction_result = self.predict(current_count, elapsed, remaining)

        # 映射到区间
        buckets = self.map_to_buckets(prediction_result['expected_total'])

        # 加载历史并获取推荐
        history = self.load_history()
        recommendation = self.get_recommendation(prediction_result, history)

        # 显示推荐
        self.display_recommendation(prediction_result, recommendation, current_count)

        # 组合结果
        result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_count': current_count,
            'elapsed_hours': elapsed,
            'remaining_hours': remaining,
            'progress_pct': prediction_result['progress_pct'],
            'predicted_linear': prediction_result['predicted_linear'],
            'predicted_conservative': prediction_result['predicted_conservative'],
            'predicted_weekend': prediction_result['predicted_weekend'],
            'expected_total': prediction_result['expected_total'],
            'ci80_lower': prediction_result['ci80_lower'],
            'ci80_upper': prediction_result['ci80_upper'],
            'ci90_lower': prediction_result['ci90_lower'],
            'ci90_upper': prediction_result['ci90_upper'],
            'daily_rate': prediction_result['daily_rate'],
            'buckets': buckets,
            'recommendation': recommendation,
        }

        # 保存
        self.save_prediction(result)

        return result

    def run_continuous(self):
        """持续运行（定时抓取）"""
        print(f"\n{'='*70}")
        print("🚀 Elon Musk Tweet 预测系统启动 - 持续监控模式")
        print(f"抓取间隔: {self.config['scrape_interval_seconds']} 秒")
        print(f"按 Ctrl+C 停止")
        print(f"{'='*70}")

        try:
            while True:
                try:
                    self.run_once()

                except Exception as e:
                    self.log_message(f"\n✗ 错误: {e}")
                    import traceback
                    traceback.print_exc()

                # 等待下一次抓取
                self.log_message(f"\n⏰ 下次抓取在 {self.config['scrape_interval_seconds']} 秒后...")
                time.sleep(self.config['scrape_interval_seconds'])

        except KeyboardInterrupt:
            print(f"\n\n⏹ 用户停止，程序退出")

    def run_interactive(self):
        """交互式菜单"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                                ║
║        🤖 Elon Musk 推文预测系统 - 完整增强版                  ║
║                                                                ║
║        自动抓取 + 统计模型 + 智能推荐 + 趋势分析                ║
║                                                                ║
╚══════════════════════════════════════════════════════════════╝
        """)

        while True:
            print("\n请选择操作:")
            print("   1. 自动抓取并预测")
            print("   2. 手动输入预测")
            print("   3. 查看历史预测")
            print("   4. 打开 Polymarket 市场")
            print("   5. 持续监控模式")
            print("   6. 退出")

            choice = input("\n请选择 (1-6): ").strip()

            if choice == '1':
                self.run_once(manual_input=False)
            elif choice == '2':
                self.run_once(manual_input=True)
            elif choice == '3':
                self.show_history()
            elif choice == '4':
                self.open_polymarket()
            elif choice == '5':
                self.run_continuous()
            elif choice == '6':
                print("\n再见！祝你好运！🍀")
                break
            else:
                print("无效选择，请重试")


# ============================================================
# 主程序
# ============================================================

def main():
    """主程序"""
    import sys

    # 检查命令行参数
    if len(sys.argv) > 1:
        # 快速预测模式：python elon_predictor_enhanced.py <推文数量>
        try:
            count = int(sys.argv[1])
            if count < 0:
                print("❌ 错误：推文数量不能为负数")
                sys.exit(1)
            predictor = EnhancedTweetPredictor(CONFIG)
            predictor.run_with_count(count)
            return
        except ValueError:
            print("❌ 错误：请输入有效的推文数量")
            print("用法: python elon_predictor_enhanced.py <推文数量>")
            print("示例: python elon_predictor_enhanced.py 100")
            sys.exit(1)

    # 交互模式
    predictor = EnhancedTweetPredictor(CONFIG)

    # 询问用户运行模式
    print("\n请选择运行模式:")
    print("  1. 交互式菜单（推荐）")
    print("  2. 持续监控模式（定时抓取）")
    print("  3. 单次自动抓取测试")

    choice = input("\n请输入选项 (1/2/3，默认1): ").strip() or "1"

    if choice == "1":
        predictor.run_interactive()
    elif choice == "2":
        predictor.run_continuous()
    else:
        predictor.run_once(manual_input=False)


if __name__ == "__main__":
    main()
