#!/bin/bash
set -e

echo "===== 更新软件源 ====="
apt update -y

echo "===== 安装 PostgreSQL ====="
apt install postgresql postgresql-contrib -y

echo "===== 启动并开机自启 ====="
systemctl enable --now postgresql

# 正确获取PG版本号
PG_VER=$(pg_lsclusters | awk 'NR==1 {print $1}' | grep -E '^[0-9]+$')
if [ -z "$PG_VER" ]; then
    echo "无法识别PostgreSQL版本，退出"
    exit 1
fi
CONF_DIR="/etc/postgresql/${PG_VER}/main"
echo "检测到PG版本: $PG_VER 配置目录: $CONF_DIR"

echo "===== 修改监听所有IP ====="
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" ${CONF_DIR}/postgresql.conf

echo "===== 允许任意IP密码登录 ====="
echo "host    all             all             0.0.0.0/0            scram-sha-256" >> ${CONF_DIR}/pg_hba.conf

echo "===== 重启PG生效 ====="
systemctl restart postgresql

# 数据库信息
DB_USER="clawuser"
DB_PASS="Claw@123456"
DB_NAME="clawhunt"

echo "===== 创建业务库与账号 ====="
sudo -u postgres psql <<EOF
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';
CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
EOF

echo -e "\032[32m===== 安装完成 =====\033[0m"
echo "数据库名：$DB_NAME"
echo "账号：$DB_USER"
echo "密码：$DB_PASS"
echo "连接地址：postgresql://$DB_USER:$DB_PASS@127.0.0.1:5432/$DB_NAME"
echo "查看状态命令：systemctl status postgresql"