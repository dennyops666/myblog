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

# 检查Docker是否安装
check_docker() {
    print_info "检查Docker环境..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        print_info "可以使用以下命令安装Docker："
        print_info "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
        exit 1
    fi
    docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_info "Docker版本: $docker_version ✓"
}

# 检查Docker Compose是否安装
check_docker_compose() {
    print_info "检查Docker Compose环境..."
    if ! command -v docker-compose &> /dev/null; then
        if command -v docker &> /dev/null && docker compose version &> /dev/null; then
            print_info "使用Docker插件方式的Docker Compose ✓"
            # 设置docker-compose为docker compose的别名
            docker_compose="docker compose"
        else
            print_error "Docker Compose未安装，请先安装Docker Compose"
            print_info "可以使用以下命令安装Docker Compose："
            print_info "curl -SL https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose"
            exit 1
        fi
    else
        docker_compose="docker-compose"
        compose_version=$(docker-compose --version | awk '{print $3}' | sed 's/,//')
        print_info "Docker Compose版本: $compose_version ✓"
    fi
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    # 创建日志目录
    if [ ! -d "logs" ]; then
        mkdir -p logs
        chmod 755 logs
        print_info "日志目录已创建 ✓"
    else
        print_info "日志目录已存在 ✓"
    fi
    
    # 创建实例目录(存放数据库文件)
    if [ ! -d "instance" ]; then
        mkdir -p instance
        chmod 755 instance
        print_info "实例目录已创建 ✓"
    else
        print_info "实例目录已存在 ✓"
    fi
}

# 生成环境变量文件
generate_env_file() {
    print_info "生成环境变量文件..."
    if [ ! -f ".env" ]; then
        echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" > .env
        print_info "环境变量文件已生成 ✓"
    else
        print_info "环境变量文件已存在，跳过 ✓"
    fi
}

# 构建Docker镜像
build_docker_image() {
    print_info "构建Docker镜像..."
    $docker_compose build
    if [ $? -ne 0 ]; then
        print_error "构建Docker镜像失败"
        exit 1
    fi
    print_info "Docker镜像构建成功 ✓"
}

# 启动Docker容器
start_docker_container() {
    print_info "启动Docker容器..."
    $docker_compose up -d
    if [ $? -ne 0 ]; then
        print_error "启动Docker容器失败"
        exit 1
    fi
    print_info "Docker容器已启动 ✓"
}

# 显示容器日志
show_container_logs() {
    print_info "显示容器日志..."
    $docker_compose logs -f --tail=20
}

# 部署完成总结
deployment_summary() {
    print_info "==================================="
    print_info "MyBlog Docker部署完成!"
    print_info "==================================="
    print_info "您可以使用以下命令管理Docker容器:"
    print_info "启动容器:    docker-compose up -d"
    print_info "停止容器:    docker-compose down"
    print_info "查看日志:    docker-compose logs -f"
    print_info "重启容器:    docker-compose restart"
    print_info "==================================="
    print_info "应用访问地址: http://localhost:5000"
    print_info "管理员账号: admin"
    print_info "==================================="
}

# 主函数
main() {
    print_info "开始Docker部署MyBlog..."
    
    # 检查Docker环境
    check_docker
    check_docker_compose
    
    # 创建必要的目录
    create_directories
    
    # 生成环境变量文件
    generate_env_file
    
    # 构建Docker镜像
    build_docker_image
    
    # 启动Docker容器
    start_docker_container
    
    # 提示用户是否查看日志
    read -p "是否查看容器日志？(y/n): " show_logs
    if [[ "$show_logs" == "y" || "$show_logs" == "Y" ]]; then
        show_container_logs
    fi
    
    # 部署完成总结
    deployment_summary
}

# 执行主函数
main 