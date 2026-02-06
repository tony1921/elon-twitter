# Telegram Bot 设置指南

## 快速设置（5分钟）

### 第一步：创建Telegram Bot

1. 在Telegram中搜索 `@BotFather`
2. 发送 `/newbot` 命令
3. 按提示设置bot名称（例如：`elon_musk_tracker_bot`）
4. 获取 **Bot Token**（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 第二步：获取Chat ID

1. 在Telegram中搜索你的bot（刚创建的）
2. 发送任意消息给它（例如：`hello`）
3. 在浏览器访问：
   ```
   https://api.telegram.org/bot<你的BOT_TOKEN>/getUpdates
   ```
4. 找到 `"chat":{"id":数字}` 中的数字，这就是你的 **Chat ID**

### 第三步：配置

编辑 `telegram_config.json` 文件：

```json
{
  "bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
  "chat_id": "123456789",
  "enabled": true
}
```

将 `enabled` 改为 `true`

### 第四步：测试

运行测试命令：
```bash
python3 telegram_notify.py
```

如果成功，你会在Telegram收到消息！

---

## 示例消息格式

🤖 *Elon Musk 推文数据更新*

📅 *2026-02-06* | 🕐 *14:30*

━━━━━━━━━━━━━━━━━━━━━
📊 *今日数据*
   今天: *45* 条
   7天平均: 52.3 条/天

━━━━━━━━━━━━━━━━━━━━━
📈 *最近3天*
   2026-02-04: 41 条
   2026-02-05: 22 条
   2026-02-06: 45 条

━━━━━━━━━━━━━━━━━━━━━
📉 *趋势*: 📈 上升

📊 *历史统计*
   总天数: 61 天
   平均: 58.0 条/天
   最高: 121 条

📂 Excel已更新
━━━━━━━━━━━━━━━━━━━━━
