@echo off
REM 启动自动更新调度器

set PYTHONIOENCODING=utf-8

echo ========================================
echo 启动 Elon Musk 推文数据自动更新
echo ========================================
echo.
echo 每5分钟自动更新一次
echo 工作目录: C:\Users\93019\elon-twitter-repo
echo 日志目录: C:\Users\93019\elon-twitter-repo\logs
echo.
echo 按 Ctrl+C 可以随时停止
echo ========================================
echo.

python auto_scheduler.py

pause
