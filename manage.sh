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
    export FLASK_ENV=production
    export FLASK_DEBUG=0
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
    
    gunicorn "app:create_app()" \
        --bind "$HOST:$PORT" \
        --workers $WORKERS \
        --pid "$PID_FILE" \
        --log-file "$LOG_FILE" \
        --error-logfile "$ERROR_LOG" \
        --daemon
    
    sleep 2
    check_status
}

# 停止服务
stop() {
    echo "正在停止 $APP_NAME..."
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        kill "$pid"
        rm -f "$PID_FILE"
        echo "$APP_NAME 已停止"
    else
        echo "$APP_NAME 未运行"
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