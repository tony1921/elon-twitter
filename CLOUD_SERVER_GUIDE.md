# 云服务器部署指南 - Elon Musk 推文监控系统

## 📋 目录
1. [购买云服务器](#1-购买云服务器)
2. [连接服务器](#2-连接服务器)
3. [安装环境](#3-安装环境)
4. [部署代码](#4-部署代码)
5. [设置定时任务](#5-设置定时任务)
6. [配置Web访问](#6-配置web访问)

---

## 1. 购买云服务器

### 推荐方案（按价格排序）

#### 方案A: 阿里云/腾讯云（适合国内）
- **配置**: 1核2G内存
- **价格**: 约￥50-100/月
- **优点**: 国内访问快、稳定
- **缺点**: 需要实名认证

**购买链接**:
- 阿里云：https://www.aliyun.com/product/ecs
- 腾讯云：https://cloud.tencent.com/product/cvm

#### 方案B: AWS/Google Cloud（国际）
- **配置**: t2.micro 或 e2-micro
- **价格**: 约$5-10/月（￥35-70/月）
- **优点**: 有免费套餐、全球CDN
- **缺点**: 需要信用卡

**购买链接**:
- AWS：https://aws.amazon.com/ec2/
- Google Cloud：https://cloud.google.com/compute

#### 方案C: GitHub Codespaces（免费开发版）
- **价格**: 免费（每月60小时）
- **优点**: 完全免费、设置简单
- **缺点**: 有时间限制、不适合24小时运行

---

## 2. 连接服务器

### 使用SSH连接（Mac/Linux）

```bash
# 格式
ssh root@服务器IP地址

# 示例
ssh root@123.45.67.89
```

输入密码后即可连接。

### Windows用户
下载工具：
- **PuTTY**: https://www.putty.org/
- 或使用 Windows Terminal 自带SSH

---

## 3. 安装环境

### 3.1 更新系统

```bash
# Ubuntu/Debian
apt update && apt upgrade -y

# CentOS/RHEL
yum update -y
```

### 3.2 安装Python和必要工具

```bash
# Ubuntu/Debian
apt install -y python3 python3-pip git

# CentOS/RHEL
yum install -y python3 python3-pip git
```

### 3.3 安装Python依赖

```bash
pip3 install requests pandas openpyxl playwright
playwright install chromium
```

---

## 4. 部署代码

### 4.1 克隆或上传代码

**方法1: 使用Git（推荐）**
```bash
# 如果代码在GitHub
git clone https://github.com/你的用户名/polymarket-predictor.git
cd polymarket-predictor
```

**方法2: 直接上传**
```bash
# 在本地电脑打包
tar -czf polymarket-predictor.tar.gz polymarket-predictor/

# 上传到服务器
scp polymarket-predictor.tar.gz root@服务器IP:/root/

# 在服务器上解压
tar -xzf polymarket-predictor.tar.gz
cd polymarket-predictor
```

### 4.2 测试运行

```bash
# 测试数据获取
python3 update_dashboard.py
```

如果成功，会看到"✅ 全部完成！"

---

## 5. 设置定时任务

使用 `crontab` 设置每小时自动运行：

```bash
# 编辑crontab
crontab -e

# 添加以下行（每小时运行一次）
0 * * * * cd /root/polymarket-predictor && /usr/bin/python3 update_dashboard.py >> /var/log/tweet_monitor.log 2>&1
```

保存退出（按 `ESC`，输入 `:wq`，按 `Enter`）

### 查看定时任务
```bash
crontab -l
```

### 查看运行日志
```bash
tail -f /var/log/tweet_monitor.log
```

---

## 6. 配置Web访问

### 方案A: 使用简单的HTTP服务器

```bash
# 安装screen（保持后台运行）
apt install -y screen  # Ubuntu/Debian
yum install -y screen  # CentOS/RHEL

# 创建screen会话
screen -S dashboard

# 启动Web服务器
cd /root/polymarket-predictor
python3 -m http.server 8888

# 按 Ctrl+A 然后按 D 来退出screen（服务器继续运行）
```

访问：`http://服务器IP:8888/dashboard.html`

### 方案B: 使用Nginx（推荐生产环境）

```bash
# 安装Nginx
apt install -y nginx  # Ubuntu/Debian
yum install -y nginx  # CentOS/RHEL

# 配置Nginx
nano /etc/nginx/sites-available/tweet-monitor

# 添加以下内容
server {
    listen 80;
    server_name 你的域名或服务器IP;

    root /root/polymarket-predictor;
    index dashboard.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /data/ {
        add_header Access-Control-Allow-Origin *;
    }
}
```

启用配置：
```bash
ln -s /etc/nginx/sites-available/tweet-monitor /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

访问：`http://服务器IP/dashboard.html`

---

## 7. 配置Telegram通知（可选）

```bash
cd /root/polymarket-predictor
nano telegram_config.json
```

修改为你的配置：
```json
{
  "bot_token": "你的Bot_Token",
  "chat_id": "你的Chat_ID",
  "enabled": true
}
```

---

## 8. 设置开机自启动（推荐）

### 创建systemd服务

```bash
nano /etc/systemd/system/tweet-monitor.service
```

添加以下内容：
```ini
[Unit]
Description=Elon Musk Tweet Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/polymarket-predictor
ExecStart=/usr/bin/screen -dmS dashboard python3 -m http.server 8888
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
systemctl daemon-reload
systemctl enable tweet-monitor
systemctl start tweet-monitor
```

---

## 📊 完整检查清单

- [ ] 购买云服务器
- [ ] 使用SSH连接服务器
- [ ] 安装Python和依赖
- [ ] 上传代码到服务器
- [ ] 测试运行 `python3 update_dashboard.py`
- [ ] 设置crontab定时任务
- [ ] 启动Web服务器
- [ ] 配置Telegram通知（可选）
- [ ] 设置开机自启动（可选）
- [ ] 测试访问网页看板

---

## 🔧 常用命令

```bash
# 查看定时任务
crontab -l

# 查看运行日志
tail -f /var/log/tweet_monitor.log

# 查看Python进程
ps aux | grep python

# 查看Web服务器是否运行
netstat -tulnp | grep 8888

# 重启Nginx
systemctl restart nginx

# 手动运行更新
cd /root/polymarket-predictor
python3 update_dashboard.py
```

---

## 💰 成本估算

| 方案 | 月费用 | 年费用 |
|------|--------|--------|
| 阿里云/腾讯云（1核2G） | ￥50-100 | ￥600-1200 |
| AWS t2.micro | $8.5 | $102 |
| Google Cloud e2-micro | $5-10 | $60-120 |
| GitHub Codespaces | 免费（60小时/月） | 免费 |

---

## 🆘 常见问题

### Q1: 忘记服务器密码怎么办？
在云服务器控制台重置密码

### Q2: 如何备份数据？
```bash
# 备份到本地
scp root@服务器IP:/root/polymarket-predictor/data/*.json ./
```

### Q3: 服务器被攻击了怎么办？
1. 立即修改密码
2. 检查 `~/.ssh/authorized_keys`
3. 安装防火墙：`ufw` 或 `iptables`

### Q4: 如何停止监控？
```bash
# 删除crontab任务
crontab -e
# 删除对应的行

# 停止Web服务器
pkill -f "python3 -m http.server 8888"
```

---

## 📞 需要帮助？

如果遇到问题，可以：
1. 查看日志：`tail -f /var/log/tweet_monitor.log`
2. 检查配置：确保所有路径正确
3. 测试网络：`ping xtracker.polymarket.com`

---

**祝您部署顺利！** 🚀
