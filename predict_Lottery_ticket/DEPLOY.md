# 彩票预测系统部署指南

## 服务器要求
- 系统: Ubuntu 20.04+ / CentOS 7+
- 配置: 2核4G以上
- 域名: 已完成 ICP 备案

---

## 第一步：服务器环境准备

### 1.1 连接服务器
```bash
ssh root@你的服务器IP
```

### 1.2 安装基础依赖
```bash
# Ubuntu/Debian
apt update && apt install -y python3 python3-pip nodejs npm nginx curl git

# CentOS
yum install -y python3 python3-pip nodejs npm nginx curl git
```

### 1.3 安装 Python 虚拟环境
```bash
pip3 install virtualenv
```

---

## 第二步：上传代码

### 方式一：使用 Git（推荐）
```bash
# 在服务器上
cd /var/www
git clone https://github.com/你的仓库地址/lottery-predict.git
cd lottery-predict
```

### 方式二：使用 scp 上传
```bash
# 本地终端
scp -r predict_Lottery_ticket root@服务器IP:/var/www/
```

---

## 第三步：配置后端

### 3.1 进入后端目录并安装依赖
```bash
cd /var/www/lottery-predict/backend
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3.2 创建 systemd 服务文件
```bash
cat > /etc/systemd/system/lottery-backend.service <<EOF
[Unit]
Description=Lottery Prediction API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/lottery-predict/backend
Environment="PATH=/var/www/lottery-predict/backend/venv/bin"
ExecStart=/var/www/lottery-predict/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

### 3.3 启动后端服务
```bash
systemctl daemon-reload
systemctl enable lottery-backend
systemctl start lottery-backend
systemctl status lottery-backend
```

---

## 第四步：配置前端

### 4.1 安装前端依赖
```bash
cd /var/www/lottery-predict/frontend
npm install
```

### 4.2 构建生产版本
```bash
npm run build
```

构建后的文件在 `dist` 目录

---

## 第五步：配置 Nginx

### 5.1 创建 Nginx 配置文件
```bash
cat > /etc/nginx/sites-available/lottery-predict <<EOF
server {
    listen 80;
    server_name lottery.你的域名.cn;

    # 前端静态文件
    location / {
        root /var/www/lottery-predict/frontend/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF
```

### 5.2 启用站点
```bash
ln -s /etc/nginx/sites-available/lottery-predict /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

---

## 第六步：配置域名解析

在阿里云 DNS 控制台添加记录：
- 类型: A记录
- 主机记录: lottery（或 @）
- 记录值: 你的服务器IP

---

## 第七步：配置 HTTPS（可选但强烈推荐）

### 使用 Let's Encrypt 免费证书
```bash
# 安装 Certbot
apt install -y certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d lottery.你的域名.cn

# 按提示完成配置
```

证书会自动续期。

---

## 访问地址

部署完成后访问：
- http://lottery.你的域名.cn（HTTP）
- https://lottery.你的域名.cn（HTTPS，推荐）

---

## 常用命令

```bash
# 查看后端日志
journalctl -u lottery-backend -f

# 重启后端
systemctl restart lottery-backend

# 重启 Nginx
systemctl reload nginx
```
