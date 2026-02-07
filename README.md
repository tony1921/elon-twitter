# Elon Musk 推文数据监控系统

自动追踪和记录Elon Musk的推文数据，每小时更新，生成Excel报表和Web看板。

## 功能特点

- ✅ 自动从XTracker获取推文数据
- ✅ 每小时自动更新
- ✅ 生成Excel报表
- ✅ Web实时看板
- ✅ Telegram推送通知（可选）
- ✅ 61天历史数据（2025-12-08 至今）

## 快速开始

### 1. 安装依赖

```bash
pip3 install requests pandas openpyxl playwright
playwright install chromium
```

### 2. 更新数据

```bash
# 更新今天的数据并生成Excel
python3 generate_excel.py

# 或者完整更新（Excel + 看板）
python3 update_dashboard.py
```

### 3. 查看Web看板

```bash
# 启动Web服务器
python3 -m http.server 8888

# 在浏览器访问
open http://localhost:8888/dashboard.html
```

## 自动监控

### 每小时自动更新

```bash
./auto_update.sh
```

### 手动更新

```bash
./update_excel.sh
```

## 文件说明

- `update_dashboard.py` - 更新数据并生成看板
- `generate_excel.py` - 生成Excel报表
- `dashboard.html` - Web看板
- `auto_update.sh` - 自动更新脚本
- `data/daily_tweets.json` - 每日数据
- `data/elon_musk_tweets.xlsx` - Excel报表

## Telegram推送（可选）

编辑 `telegram_config.json`:

```json
{
  "bot_token": "你的Bot_Token",
  "chat_id": "你的Chat_ID",
  "enabled": true
}
```

详细教程请查看 `TELEGRAM_SETUP.md`

## 云服务器部署

详细部署指南请查看 `CLOUD_SERVER_GUIDE.md`

## 数据统计

- 总天数: 61天
- 平均推文: 58.0条/天
- 最高记录: 121条
- 数据范围: 2025-12-08 至今

## 许可证

MIT License

<!-- Auto-triggered update at 2026-02-07 09:10:47 -->
