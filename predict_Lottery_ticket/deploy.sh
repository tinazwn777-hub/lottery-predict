#!/bin/bash

#==========================================
# 彩票预测系统 - 一键部署脚本
#==========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
DOMAIN=""
GITHUB_REPO=""
PROJECT_DIR="/var/www/lottery-predict"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
SERVICE_NAME="lottery-backend"

# 打印彩色信息
print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "请使用 root 用户运行此脚本"
        exit 1
    fi
}

# 获取域名和GitHub仓库
get_domain() {
    echo ""
    echo "=========================================="
    echo "  彩票预测系统 - 一键部署"
    echo "=========================================="
    echo ""
    read -p "请输入你的域名（例如 lottery.yourdomain.cn）: " DOMAIN
    if [ -z "$DOMAIN" ]; then
        print_error "域名不能为空"
        exit 1
    fi
    print_info "已设置域名: $DOMAIN"
    echo ""
    read -p "请输入GitHub仓库地址（例如 https://github.com/username/repo.git）: " GITHUB_REPO
    if [ -z "$GITHUB_REPO" ]; then
        print_error "GitHub仓库地址不能为空"
        exit 1
    fi
    print_info "已设置GitHub仓库: $GITHUB_REPO"
}

# 检测系统并安装依赖
install_dependencies() {
    print_info "正在检测系统并安装依赖..."

    # 检测系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    else
        print_error "无法检测操作系统"
        exit 1
    fi

    print_info "检测到系统: $OS"

    # 安装基础依赖
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        apt update
        apt install -y python3 python3-pip python3-venv nodejs npm nginx curl git wget
    elif [ "$OS" = "centos" ] || [ "$OS" = "rocky" ] || [ "$OS" = "almalinux" ]; then
        yum install -y python3 python3-pip nodejs npm nginx curl git wget
    else
        print_warn "未识别的系统，请手动安装依赖"
    fi

    print_info "依赖安装完成"
}

# 创建项目目录并从GitHub拉取代码
create_directories() {
    print_info "正在创建项目目录并从GitHub拉取代码..."

    # 如果目录已存在，先备份
    if [ -d "$PROJECT_DIR" ]; then
        BACKUP_DIR="${PROJECT_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
        print_warn "目录已存在，备份到: $BACKUP_DIR"
        mv "$PROJECT_DIR" "$BACKUP_DIR"
    fi

    # 从GitHub克隆代码
    git clone "$GITHUB_REPO" "$PROJECT_DIR"

    # 创建必要目录
    mkdir -p "$PROJECT_DIR/backend/data"

    # 创建 www-data 用户（如果不存在）
    id -u www-data &>/dev/null || useradd -r -s /usr/sbin/nologin www-data

    print_info "代码拉取完成"
}

# 部署后端
deploy_backend() {
    print_info "正在部署后端..."

    cd "$BACKEND_DIR"

    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # 激活虚拟环境
    source venv/bin/activate

    # 安装依赖
    pip install --upgrade pip
    pip install -r requirements.txt

    # 退出虚拟环境
    deactivate

    # 创建 systemd 服务
    cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Lottery Prediction API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin"
ExecStart=$BACKEND_DIR/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    # 重载 systemd 并启动服务
    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME}
    systemctl restart ${SERVICE_NAME}

    # 等待服务启动
    sleep 3

    # 检查服务状态
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        print_info "后端服务启动成功"
    else
        print_error "后端服务启动失败，请检查日志: journalctl -u ${SERVICE_NAME} -n 50"
        exit 1
    fi
}

# 部署前端
deploy_frontend() {
    print_info "正在部署前端..."

    cd "$FRONTEND_DIR"

    # 安装依赖
    npm install

    # 构建生产版本
    npm run build

    # 设置权限
    if [ -d "dist" ]; then
        chown -R www-data:www-data "$FRONTEND_DIR/dist"
        print_info "前端构建完成"
    else
        print_error "前端构建失败"
        exit 1
    fi
}

# 配置 Nginx
configure_nginx() {
    print_info "正在配置 Nginx..."

    # 创建 Nginx 配置
    cat > /etc/nginx/sites-available/lottery-predict <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    # 前端静态文件
    location / {
        root $FRONTEND_DIR/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebSocket 支持（如果需要）
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
EOF

    # 启用站点
    ln -sf /etc/nginx/sites-available/lottery-predict /etc/nginx/sites-enabled/

    # 禁用默认站点
    rm -f /etc/nginx/sites-enabled/default

    # 测试 Nginx 配置
    nginx -t

    # 重载 Nginx
    systemctl reload nginx

    print_info "Nginx 配置完成"
}

# 配置 HTTPS
configure_https() {
    print_info "正在配置 HTTPS..."

    # 安装 Certbot
    if ! command -v certbot &> /dev/null; then
        apt install -y certbot python3-certbot-nginx
    fi

    # 获取证书（自动配置 Nginx）
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN"

    print_info "HTTPS 配置完成"
}

# 配置防火墙
configure_firewall() {
    print_info "正在配置防火墙..."

    # Ubuntu
    if command -v ufw &> /dev/null; then
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 22/tcp
    fi

    print_info "防火墙配置完成"
}

# 显示部署结果
show_result() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}  部署完成！${NC}"
    echo "=========================================="
    echo ""
    echo "访问地址:"
    echo -e "  ${GREEN}HTTP:${NC}  http://$DOMAIN"
    echo -e "  ${GREEN}HTTPS:${NC} https://$DOMAIN"
    echo ""
    echo "管理命令:"
    echo "  查看后端日志: journalctl -u ${SERVICE_NAME} -f"
    echo "  重启后端:     systemctl restart ${SERVICE_NAME}"
    echo "  重载 Nginx:  systemctl reload nginx"
    echo ""
}

# 主函数
main() {
    check_root
    get_domain
    install_dependencies
    create_directories
    deploy_backend
    deploy_frontend
    configure_nginx
    configure_https
    configure_firewall
    show_result
}

# 运行主函数
main
