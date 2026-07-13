@echo off
chcp 65001 >nul
fltmc >nul 2>&1 || (
    echo 错误：必须右键【以管理员身份运行】此脚本！
    pause
    exit /b 1
)
echo ==============================================
echo PostgreSQL 开启局域网访问配置工具（管理员版）
echo ==============================================
echo.

:: 这里改成你自己的PG版本！！
set PG_VERSION=17
set PG_ROOT=C:\Program Files\PostgreSQL\%PG_VERSION%
set CONF_DIR=%PG_ROOT%\data
set PG_CONF=%CONF_DIR%\postgresql.conf
set HBA_CONF=%CONF_DIR%\pg_hba.conf

if not exist "%PG_CONF%" (
    echo 错误：未找到 %PG_CONF%
    echo 请修改脚本内 PG_VERSION 为你的PG版本号后重试
    pause
    exit /b 1
)

echo [1] 修改 postgresql.conf 允许监听所有IP
findstr /c:"listen_addresses = '*'" "%PG_CONF%" >nul
if %errorlevel% equ 1 (
    powershell -Command "(Get-Content '%PG_CONF%') -replace '#listen_addresses = ''localhost''', 'listen_addresses = ''*''' | Set-Content '%PG_CONF%'"
    echo 已开启全局监听
) else (
    echo 监听地址已为 *，无需修改
)

echo [2] 修改 pg_hba.conf 放行局域网网段（推荐192.168.1.0/24，比0.0.0.0安全）
findstr /c:"192.168.1.0/24" "%HBA_CONF%" >nul
if %errorlevel% equ 1 (
    echo host    all             all             192.168.1.0/24            scram-sha-256 >> "%HBA_CONF%"
    echo 已添加局域网访问规则
) else (
    echo 局域网规则已存在，无需修改
)

echo [3] Windows防火墙放行5432端口
netsh advfirewall firewall show rule name="PostgreSQL 5432" >nul
if %errorlevel% equ 1 (
    netsh advfirewall firewall add rule name="PostgreSQL 5432" dir=in action=allow protocol=TCP localport=5432 profile=any remoteip=192.168.1.0/24 enable=yes
    echo 防火墙放行局域网5432成功
) else (
    echo 防火墙规则已存在
)

echo [4] 重启PostgreSQL服务
set SERVICE_NAME=postgresql-x64-%PG_VERSION%
sc query %SERVICE_NAME% >nul
if %errorlevel% equ 0 (
    net stop %SERVICE_NAME%
    net start %SERVICE_NAME%
    echo 服务重启完成
) else (
    echo 警告：服务名 %SERVICE_NAME% 不存在！
    echo 请修改脚本内 PG_VERSION 为你本机实际版本
)

echo.
echo ==============================================
echo 配置完成！
echo 1. Windows本机局域网IP：cmd执行 ipconfig 查看IPv4（如192.168.1.18）
echo 2. Khadas连接配置示例：
echo DB_HOST=192.168.1.18
echo DB_PORT=5432
echo DB_USER=postgres
echo DB_PASSWORD=你的PG密码
echo DB_NAME=clawhunt
echo ==============================================
pause