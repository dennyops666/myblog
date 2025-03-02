#!/bin/bash

# 配置变量
APP_NAME="myblog"
APP_DIR="/data/myblog"
VENV_DIR="$APP_DIR/venv"
PID_FILE="$APP_DIR/app.pid"
LOG_FILE="$APP_DIR/app.log"
ERROR_LOG="$APP_DIR/error.log"
HOST="0.0.0.0"
PORT="5000"
WORKERS=4

# 激活虚拟环境的函数
activate_venv() {
    source "$VENV_DIR/bin/activate"
}

# 设置环境变量
set_env() {
    export FLASK_APP=app
    export FLASK_ENV=development
    export FLASK_DEBUG=1
}

# 检查服务状态
check_status() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null; then
            echo "$APP_NAME 正在运行 (PID: $pid)"
            return 0
        else
            echo "$APP_NAME 未运行 (PID 文件存在但进程不存在)"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo "$APP_NAME 未运行"
        return 1
    fi
}

# 启动服务
start() {
    echo "正在启动 $APP_NAME..."
    if [ -f "$PID_FILE" ]; then
        echo "警告: PID 文件已存在，检查服务是否已经在运行"
        check_status
        if [ $? -eq 0 ]; then
            echo "错误: $APP_NAME 已经在运行"
            return 1
        fi
    fi

    cd "$APP_DIR"
    activate_venv
    set_env
    
    nohup gunicorn "app:create_app()" \
        --bind "$HOST:$PORT" \
        --workers 1 \
        --timeout 120 \
        --reload \
        --pid "$PID_FILE" \
        --log-file "$LOG_FILE" \
        --error-logfile "$ERROR_LOG" \
        --log-level debug \
        --capture-output \
        --enable-stdio-inheritance \
        --daemon > /dev/null 2>&1 &
    
    echo $! > "$PID_FILE"
    
    sleep 2
    check_status
}

# 停止服务
stop() {
    echo "正在停止 $APP_NAME..."
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null; then
            # 先尝试正常停止
            kill "$pid"
            # 等待最多10秒
            for i in {1..10}; do
                if ! ps -p "$pid" > /dev/null; then
                    break
                fi
                sleep 1
            done
            # 如果进程还在运行，强制终止
            if ps -p "$pid" > /dev/null; then
                echo "正常停止失败，正在强制终止..."
                kill -9 "$pid"
            fi
        else
            echo "$APP_NAME 未运行 (PID 文件存在但进程不存在)"
        fi
        rm -f "$PID_FILE"
        echo "$APP_NAME 已停止"
    else
        # 尝试查找并停止所有相关进程
        pids=$(pgrep -f "gunicorn.*app:create_app()")
        if [ -n "$pids" ]; then
            echo "找到运行中的进程，正在停止..."
            for pid in $pids; do
                kill "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
            done
            echo "$APP_NAME 已停止"
        else
            echo "$APP_NAME 未运行"
        fi
    fi
}

# 重启服务
restart() {
    stop
    sleep 2
    start
}

# 重载服务
reload() {
    echo "正在重载 $APP_NAME..."
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        kill -HUP "$pid"
        echo "$APP_NAME 已重载"
    else
        echo "错误: $APP_NAME 未运行"
        return 1
    fi
}

# 主函数
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    reload)
        reload
        ;;
    status)
        check_status
        ;;
    *)
        echo "用法: $0 {start|stop|restart|reload|status}"
        exit 1
        ;;
esac

exit 0 