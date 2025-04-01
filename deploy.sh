#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 打印带颜色的信息
print_info() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

print_warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# 设置应用目录和其他配置
APP_DIR="/data/myblog"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="$APP_DIR/logs"
INSTANCE_DIR="$APP_DIR/instance"

# 检查是否在正确的目录
check_directory() {
    current_dir=$(pwd)
    if [ "$current_dir" != "$APP_DIR" ]; then
        print_warn "当前目录不是 $APP_DIR"
        print_info "切换到 $APP_DIR 目录..."
        cd "$APP_DIR" || { print_error "无法切换到 $APP_DIR 目录"; exit 1; }
    fi
}

# 检查Python环境
check_python() {
    print_info "检查Python环境..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python3未安装，请先安装Python3"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$python_version < 3.6" | bc -l) )); then
        print_error "Python版本必须 >= 3.6，当前版本: $python_version"
        exit 1
    fi
    print_info "Python版本: $python_version ✓"
}

# 检查pip
check_pip() {
    print_info "检查pip..."
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3未安装，请先安装pip3"
        exit 1
    fi
    pip_version=$(pip3 --version | awk '{print $2}')
    print_info "pip版本: $pip_version ✓"
}

# 创建虚拟环境
create_venv() {
    print_info "检查虚拟环境..."
    if [ ! -d "$VENV_DIR" ]; then
        print_info "创建虚拟环境..."
        python3 -m venv "$VENV_DIR"
        if [ $? -ne 0 ]; then
            print_error "创建虚拟环境失败"
            exit 1
        fi
        print_info "虚拟环境创建成功 ✓"
    else
        print_info "虚拟环境已存在 ✓"
    fi
}

# 激活虚拟环境
activate_venv() {
    print_info "激活虚拟环境..."
    source "$VENV_DIR/bin/activate"
    if [ $? -ne 0 ]; then
        print_error "激活虚拟环境失败"
        exit 1
    fi
    print_info "虚拟环境已激活 ✓"
}

# 安装依赖
install_dependencies() {
    print_info "安装项目依赖..."
    pip install --upgrade pip
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        print_error "安装依赖失败"
        exit 1
    fi
    print_info "依赖安装完成 ✓"
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    # 创建日志目录
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
        chmod 755 "$LOG_DIR"
        print_info "日志目录已创建 ✓"
    else
        print_info "日志目录已存在 ✓"
    fi
    
    # 创建实例目录(存放数据库文件)
    if [ ! -d "$INSTANCE_DIR" ]; then
        mkdir -p "$INSTANCE_DIR"
        chmod 755 "$INSTANCE_DIR"
        print_info "实例目录已创建 ✓"
    else
        print_info "实例目录已存在 ✓"
    fi
}

# 设置环境变量
setup_env() {
    print_info "设置环境变量..."
    if [ ! -f ".env" ]; then
        cat > .env << EOL
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
DATABASE_URL=sqlite:///instance/blog-dev.db
EOL
        print_info "环境变量配置文件已创建 ✓"
    else
        print_info "环境变量配置文件已存在，跳过 ✓"
    fi
    
    # 设置当前会话的环境变量
    export FLASK_APP=app
    export FLASK_ENV=production
}

# 初始化数据库
init_database() {
    print_info "初始化数据库..."
    
    # 检查数据库文件是否已存在
    if [ -f "$INSTANCE_DIR/blog-dev.db" ]; then
        read -p "数据库文件已存在，是否重新初始化？(y/n): " answer
        if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
            print_info "跳过数据库初始化"
            return 0
        fi
    fi
    
    # 运行数据库迁移和初始化
    flask db upgrade
    if [ $? -ne 0 ]; then
        print_error "数据库初始化失败"
        exit 1
    fi
    print_info "数据库初始化完成 ✓"
}

# 创建超级管理员用户
create_admin() {
    print_info "检查超级管理员用户..."
    
    # 检查是否已存在admin用户
    admin_exists=$(flask shell -c "from app.models import User; print(User.query.filter_by(username='admin').first() is not None)" 2>/dev/null)
    
    if [ "$admin_exists" == "True" ]; then
        print_info "超级管理员用户已存在，跳过创建 ✓"
    else
        print_info "创建超级管理员用户..."
        # 使用create-admin命令（假设存在）或者通过flask shell创建
        flask create-admin
        if [ $? -ne 0 ]; then
            print_error "创建超级管理员用户失败"
            exit 1
        fi
        print_info "超级管理员用户创建成功 ✓"
    fi
}

# 启动应用
start_application() {
    print_info "启动应用..."
    # 使用已有的manage.sh脚本启动应用
    ./manage.sh start
    if [ $? -ne 0 ]; then
        print_error "启动应用失败"
        exit 1
    fi
}

# 部署完成总结
deployment_summary() {
    print_info "==================================="
    print_info "MyBlog 部署完成!"
    print_info "==================================="
    print_info "您可以使用以下命令管理应用:"
    print_info "启动应用:    ./manage.sh start"
    print_info "停止应用:    ./manage.sh stop"
    print_info "重启应用:    ./manage.sh restart"
    print_info "查看状态:    ./manage.sh status"
    print_info "重载应用:    ./manage.sh reload"
    print_info "==================================="
    print_info "应用访问地址: http://localhost:5000"
    print_info "管理员账号: admin"
    print_info "==================================="
}

# 主函数
main() {
    print_info "开始部署MyBlog..."
    
    # 检查当前目录
    check_directory
    
    # 检查环境
    check_python
    check_pip
    
    # 创建并激活虚拟环境
    create_venv
    activate_venv
    
    # 安装依赖
    install_dependencies
    
    # 创建目录
    create_directories
    
    # 设置环境变量
    setup_env
    
    # 初始化数据库
    init_database
    
    # 创建管理员用户
    create_admin
    
    # 提示用户是否启动应用
    read -p "是否立即启动应用？(y/n): " start_answer
    if [[ "$start_answer" == "y" || "$start_answer" == "Y" ]]; then
        start_application
    else
        print_info "跳过启动应用，您可以稍后使用 ./manage.sh start 命令启动"
    fi
    
    # 部署完成总结
    deployment_summary
}

# 执行主函数
main 