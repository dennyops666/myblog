FROM python:3.9-slim

LABEL maintainer="MyBlog Team"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app \
    FLASK_ENV=production \
    DATABASE_URL=sqlite:///instance/blog-dev.db

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/

# 创建必要的目录
RUN mkdir -p /app/logs /app/instance \
    && chmod 755 /app/logs /app/instance

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 5000

# 设置启动命令
CMD ["gunicorn", "wsgi:application", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "--log-file", "/app/logs/myblog.log", "--error-logfile", "/app/logs/error.log", "--log-level", "debug", "--capture-output", "--enable-stdio-inheritance"]