# MyBlog 部署文档

## 1. 系统要求

### 1.1 硬件要求
- CPU: 1核心及以上
- 内存: 1GB及以上
- 硬盘: 10GB及以上

### 1.2 软件要求
- 操作系统: Linux (推荐Ubuntu 20.04 LTS)
- Python: 3.8及以上
- SQLite: 3.x
- Nginx: 1.18及以上
- Git: 2.x及以上

## 2. 开发环境部署

### 2.1 安装Python环境
```bash
# 更新系统包
sudo apt update
sudo apt upgrade

# 安装Python和相关工具
sudo apt install python3 python3-pip python3-venv
```

### 2.2 克隆项目
```bash
# 克隆项目代码
git clone https://github.com/dennyops666/myblog.git
cd myblog

# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate
```

### 2.3 安装依赖
```bash
# 安装项目依赖
pip install -r requirements.txt
```

### 2.4 配置环境变量
```bash
# 创建.env文件
cp .env.example .env

# 编辑.env文件，配置必要的环境变量
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///myblog.db
```

### 2.5 初始化数据库
```bash
# 创建数据库表
flask db upgrade

# 创建管理员账户
flask create-admin
```

### 2.6 运行开发服务器
```bash
# 启动开发服务器
flask run
```

## 3. 生产环境部署

### 3.1 服务器准备
```bash
# 更新系统
sudo apt update
sudo apt upgrade

# 安装必要的软件包
sudo apt install python3 python3-pip python3-venv nginx supervisor
```

### 3.2 部署项目
```bash
# 创建项目目录（如果不存在）
sudo mkdir -p /data/myblog
sudo chown -R $USER:$USER /data/myblog

# 克隆项目
git clone https://github.com/dennyops666/myblog.git /data/myblog
cd /data/myblog

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn
```

### 3.3 配置Supervisor
```ini
# /etc/supervisor/conf.d/myblog.conf
[program:myblog]
directory=/data/myblog
command=/data/myblog/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 run:app
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/myblog/supervisor.err.log
stdout_logfile=/var/log/myblog/supervisor.out.log
```

### 3.4 配置Nginx
```nginx
# /etc/nginx/sites-available/myblog
server {
    listen 80;
    server_name my.blog.com;

    access_log /var/log/nginx/myblog.access.log;
    error_log /var/log/nginx/myblog.error.log;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /data/myblog/app/static;
        expires 30d;
    }
}
```

### 3.5 启动服务
```bash
# 创建日志目录
sudo mkdir -p /var/log/myblog
sudo chown -R www-data:www-data /var/log/myblog

# 启用Nginx配置
sudo ln -s /etc/nginx/sites-available/myblog /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 启动Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start myblog
```

## 4. 安全配置

### 4.1 防火墙配置
```bash
# 安装UFW
sudo apt install ufw

# 配置防火墙规则
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### 4.2 SSL证书配置
```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d my.blog.com

# 自动续期证书
sudo certbot renew --dry-run
```

## 5. 维护指南

### 5.1 备份
```bash
# 备份数据库
cp /data/myblog/instance/myblog.db /backup/myblog_$(date +%Y%m%d).db

# 备份配置文件
cp /data/myblog/.env /backup/env_$(date +%Y%m%d)
```

### 5.2 更新
```bash
# 进入项目目录
cd /data/myblog

# 拉取最新代码
git pull origin main

# 激活虚拟环境
source venv/bin/activate

# 更新依赖
pip install -r requirements.txt

# 数据库迁移
flask db upgrade

# 重启服务
sudo supervisorctl restart myblog
```

### 5.3 日志管理
```bash
# 查看应用日志
tail -f /var/log/myblog/supervisor.out.log

# 查看错误日志
tail -f /var/log/myblog/supervisor.err.log

# 查看Nginx访问日志
tail -f /var/log/nginx/myblog.access.log
```

## 6. 监控

### 6.1 系统监控
```bash
# 安装监控工具
sudo apt install htop

# 查看系统资源使用情况
htop
```

### 6.2 应用监控
- 使用Flask-Monitor扩展监控应用性能
- 配置Sentry进行错误跟踪
- 设置邮件通知系统

## 7. 故障排除

### 7.1 常见问题
1. 502 Bad Gateway
   - 检查Gunicorn是否正在运行
   - 检查Supervisor日志
   - 检查应用日志

2. 静态文件404
   - 检查Nginx静态文件配置
   - 确认静态文件权限

3. 数据库连接错误
   - 检查数据库文件权限
   - 确认数据库路径配置

### 7.2 性能优化
1. 配置Nginx缓存
2. 优化Gunicorn工作进程数
3. 启用Gzip压缩
4. 配置静态文件缓存 