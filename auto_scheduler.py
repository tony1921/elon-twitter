#!/usr/bin/env python3
"""
本地自动调度器 - 每5分钟运行一次更新脚本
"""

import subprocess
import time
import os
from datetime import datetime

# 切换到脚本目录
os.chdir(r'C:\Users\93019\elon-twitter-repo')

print("=" * 50)
print("🚀 Elon Musk 推文数据自动更新系统")
print("⏰ 每5分钟自动更新一次")
print("📂 工作目录: C:\\Users\\93019\\elon-twitter-repo")
print("=" * 50)
print("按 Ctrl+C 停止运行")
print("=" * 50)

# 创建日志目录
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

update_count = 0

while True:
    try:
        update_count += 1
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n[{timestamp}] 第 {update_count} 次更新开始...")

        # 记录日志
        log_file = os.path.join(log_dir, f"update_{now.strftime('%Y%m%d')}.log")

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"更新 #{update_count} - {timestamp}\n")
            f.write(f"{'='*60}\n")

        # 运行更新脚本
        try:
            # 运行 Python 更新脚本
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            result = subprocess.run(
                ["python", "update_dashboard.py"],
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
                encoding='utf-8',
                errors='replace'
            )

            with open(log_file, "a", encoding="utf-8") as f:
                f.write("STDOUT:\n")
                f.write(result.stdout)
                f.write("\nSTDERR:\n")
                f.write(result.stderr)
                f.write(f"\n返回码: {result.returncode}\n")

            # 检查是否有数据变更
            git_diff = subprocess.run(
                ["git", "diff", "--quiet", "data/daily_tweets.json", "data/dashboard_data.json"],
                capture_output=True
            )

            if git_diff.returncode != 0:
                print("  ✅ 发现新数据，提交到 GitHub...")

                with open(log_file, "a", encoding="utf-8") as f:
                    f.write("\n>>> 提交更新到 GitHub\n")

                # 添加并提交
                subprocess.run(["git", "add", "data/daily_tweets.json", "data/dashboard_data.json"])
                commit_msg = f"🤖 Auto update {now.strftime('%Y-%m-%d %H:%M:%S')}"
                subprocess.run(["git", "commit", "-m", commit_msg])
                push_result = subprocess.run(["git", "push", "origin", "main"])

                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"推送结果: {push_result.returncode}\n")

                # 更新 gh-pages
                print("  📊 更新网页...")
                subprocess.run(["git", "fetch", "origin", "gh-pages:gh-pages"])
                subprocess.run(["git", "checkout", "gh-pages"])
                subprocess.run(["git", "checkout", "main", "--", "dashboard.html",
                              "data/daily_tweets.json", "data/dashboard_data.json"])
                subprocess.run(["git", "add", "."])

                deploy_msg = f"📊 Update dashboard {now.strftime('%Y-%m-%d %H:%M:%S')}"
                subprocess.run(["git", "commit", "-m", deploy_msg])
                subprocess.run(["git", "push", "origin", "gh-pages"])
                subprocess.run(["git", "checkout", "main"])

                print("  ✅ 更新完成！")
            else:
                print("  ℹ️  没有新数据")

        except subprocess.TimeoutExpired:
            print("  ⚠️  更新超时")
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n错误: {e}\n")

        # 显示下次更新时间
        next_update = now.replace(minute=now.minute//5*5+5, second=0, microsecond=0)
        print(f"  ⏰ 下次更新: {next_update.strftime('%Y-%m-%d %H:%M:%S')}")

        # 等待5分钟
        print("\n等待中...")
        time.sleep(300)  # 300秒 = 5分钟

    except KeyboardInterrupt:
        print("\n\n" + "=" * 50)
        print("👋 自动更新已停止")
        print(f"总共运行了 {update_count} 次更新")
        print("=" * 50)
        break
    except Exception as e:
        print(f"\n❌ 严重错误: {e}")
        time.sleep(60)  # 出错后等待1分钟再试
