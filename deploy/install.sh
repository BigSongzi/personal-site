#!/usr/bin/env bash
# 阿里云 Linux / CentOS / Anolis 一键安装脚本
# 用法:在服务器上把项目放到 /opt/personal-site,然后:
#   sudo bash deploy/install.sh
# 脚本职责:
#   1. 安装系统依赖(python3.10+/nodejs 18+/git/firewalld)
#   2. 创建 www 用户与日志目录
#   3. 创建 Python venv 并安装 requirements
#   4. 构建前端 dist
#   5. 部署 systemd 单元并启用开机自启
#   6. 放行 firewalld 8080 端口
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/personal-site}"
LOG_DIR="/var/log/personal-site"
SERVICE_USER="www"

echo "==> 项目目录: $PROJECT_DIR"

# 1) 系统依赖
echo "==> 安装系统依赖"
if command -v dnf >/dev/null 2>&1; then
    PKG="dnf"
elif command -v yum >/dev/null 2>&1; then
    PKG="yum"
else
    echo "未识别到 yum/dnf,请手动安装依赖"; exit 1
fi
$PKG install -y python3 python3-pip python3-devel gcc git firewalld curl tar
# 阿里云 Linux 默认无 node,使用 NodeSource
if ! command -v node >/dev/null 2>&1; then
    echo "==> 安装 Node.js 18"
    curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
    $PKG install -y nodejs
fi

# 2) 用户与目录
if ! id -u $SERVICE_USER >/dev/null 2>&1; then
    echo "==> 创建用户 $SERVICE_USER"
    useradd -r -s /usr/sbin/nologin $SERVICE_USER || useradd -r -s /sbin/nologin $SERVICE_USER
fi
mkdir -p "$LOG_DIR"
chown -R $SERVICE_USER:$SERVICE_USER "$LOG_DIR" "$PROJECT_DIR"

# 3) Python venv
echo "==> 创建 Python 虚拟环境"
cd "$PROJECT_DIR/backend"
[ -f .env ] || cp .env.example .env
sudo -u $SERVICE_USER python3 -m venv .venv
sudo -u $SERVICE_USER ./.venv/bin/pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
sudo -u $SERVICE_USER ./.venv/bin/pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 4) 前端构建
echo "==> 构建前端"
cd "$PROJECT_DIR/frontend"
sudo -u $SERVICE_USER npm config set registry https://registry.npmmirror.com
sudo -u $SERVICE_USER npm install
sudo -u $SERVICE_USER npm run build

# 5) systemd
echo "==> 部署 systemd 单元"
cp "$PROJECT_DIR/deploy/personal-site.service" /etc/systemd/system/
cp "$PROJECT_DIR/deploy/gold-monitor.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now personal-site.service
systemctl enable --now gold-monitor.service

# 6) 防火墙
echo "==> 放行 firewalld 端口"
systemctl enable --now firewalld || true
firewall-cmd --permanent --add-port=8080/tcp || true
firewall-cmd --reload || true

echo
echo "==> 全部完成。访问 http://<公网IP>:8080"
echo "==> 服务状态:"
systemctl --no-pager status personal-site.service | head -n 5 || true
systemctl --no-pager status gold-monitor.service | head -n 5 || true
