# MyBlog 个人博客系统

**当前版本**: v1.0.0 (2025-03-28) - 功能完整测试版本

MyBlog 是一个基于 Python Flask 开发的个人博客系统，采用传统的单体架构，实现了文章发布、分类管理、标签管理、评论互动等核心功能，提供了直观友好的前台展示和强大的后台管理功能。

## 项目概述

本项目作为毕业设计项目，旨在展示个人技术能力的同时，提供一个实用的博客平台。系统采用 MVC 设计模式，使用 SQLite 数据库存储数据，实现了响应式前端设计，确保系统安全性和可靠性。

## 技术栈

### 后端技术
- **编程语言**：Python 3.8+
- **Web 框架**：Flask 3.0.0
- **数据库**：SQLite 3.x
- **ORM**：SQLAlchemy 2.0.23
- **模板引擎**：Jinja2 3.1.2
- **缓存**：Flask-Caching 2.1.0

### 前端技术
- HTML5
- CSS3
- JavaScript
- Bootstrap 5.x
- jQuery 3.x
- Markdown 编辑器：SimpleMDE

## 主要功能

### 1. 文章管理
- 创建、编辑、删除和查看文章
- Markdown 格式支持
- 文章分类和标签
- 文章预览和发布
- 文章列表和搜索

### 2. 分类管理
- 创建、编辑和删除分类
- 分类统计和导航

### 3. 标签管理
- 创建、编辑和删除标签
- 标签云和标签统计

### 4. 评论功能
- 访客评论
- 评论审核
- 层级回复结构

### 5. 用户系统
- 管理员登录
- 权限控制
- 用户信息管理

### 6. 前台展示
- 响应式设计
- 文章详情页
- 目录导航
- 文章归档
- 标签和分类导航

### 7. 系统设置
- 站点基本信息配置
- 系统参数设置

## 安装与部署

### 方法一：使用脚本自动部署（推荐）

项目提供了自动部署脚本，可以一键完成整个部署过程：

```bash
# 克隆仓库
git clone git@github.com:dennyops666/myblog.git
cd myblog

# 使用部署脚本
./deploy.sh
```

部署脚本会自动完成以下操作：
- 检查环境依赖
- 创建并激活虚拟环境
- 安装所需依赖
- 创建必要目录
- 初始化数据库
- 创建管理员账号
- 启动应用服务

### 方法二：Docker部署（适合容器化环境）

如果您的环境支持Docker，可以使用Docker部署：

```bash
# 克隆仓库
git clone git@github.com:dennyops666/myblog.git
cd myblog

# 使用Docker部署脚本
./docker_deploy.sh
```

Docker部署脚本会自动完成以下操作：
- 检查Docker环境
- 创建必要的目录结构
- 构建Docker镜像
- 启动容器
- 初始化应用

您也可以手动使用Docker Compose命令：

```bash
# 构建并启动
docker-compose up -d

# 查看容器状态
docker-compose ps

# 查看应用日志
docker-compose logs -f

# 停止应用
docker-compose down
```

### 方法三：传统手动部署

如果您希望手动控制部署过程，可以按照以下步骤操作：

1. **环境准备**
```bash
sudo mkdir -p /data/myblog
sudo chown -R your_user:your_group /data/myblog
```

2. **部署项目**
```bash
git clone git@github.com:dennyops666/myblog.git /data/myblog
cd /data/myblog
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **初始化数据库**
```bash
flask db upgrade
flask create-admin
```

4. **使用管理脚本启动服务**
```bash
./manage.sh start
```

## 应用管理

无论使用哪种部署方式，都可以使用以下命令管理应用：

```bash
# 启动应用
./manage.sh start

# 停止应用
./manage.sh stop

# 重启应用
./manage.sh restart

# 查看应用状态
./manage.sh status

# 重载应用配置
./manage.sh reload
```

## 使用说明

1. **访问网站**
   - 前台主页：http://Your domain name or IP:5000/blog
   - 管理后台：http://Your domain name or IP:5000/admin

2. **登录管理后台**
   - 用户名：admin
   - 密码：admin123

3. **使用管理后台**
   - **仪表盘**  ：查看统计信息和最近文章
   - **文章管理**：管理博客文章
   - **分类管理**：管理文章分类
   - **标签管理**：管理文章标签
   - **评论管理**：管理文章评论
   - **用户管理**：管理系统用户
   - **系统管理**：配置系统参数

4. **主题切换**：系统支持浅色和深色两种主题模式，点击导航栏右侧的主题切换按钮可以切换模式。

## 项目结构

```
myblog/
├── app/                    # 应用主目录
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑层
│   ├── controllers/       # 控制器层
│   ├── templates/         # 模板文件
│   ├── static/            # 静态文件
│   ├── utils/             # 工具函数
│   └── config.py          # 配置文件
├── tests/                 # 测试目录
├── docs/                  # 文档目录
├── logs/                  # 日志文件
├── instance/              # 实例配置
├── migrations/            # 数据库迁移
├── deploy.sh              # 自动部署脚本
├── docker_deploy.sh       # Docker部署脚本
├── Dockerfile             # Docker镜像定义
├── docker-compose.yml     # Docker Compose配置
├── requirements.txt       # 依赖列表
├── run.py                 # 应用入口
└── manage.sh              # 管理脚本
```

## 系统维护

1. **日志文件**
   - 应用日志：`/data/myblog/logs/myblog.log`
   - 错误日志：`/data/myblog/logs/error.log`

2. **数据库文件**
   - 开发数据库：`/data/myblog/instance/blog-dev.db`

3. **备份还原**
   对于数据备份，可以使用以下方法：
   ```bash
   # 备份数据库
   cp /data/myblog/instance/blog-dev.db /path/to/backup/blog-backup-$(date +%Y%m%d).db
   
   # 还原数据库
   cp /path/to/backup/blog-backup-YYYYMMDD.db /data/myblog/instance/blog-dev.db
   ```

4. **故障排除**
   如果遇到问题，请检查日志文件：
   ```bash
   # 查看最新的应用日志
   tail -f /data/myblog/logs/myblog.log
   
   # 查看错误日志
   tail -f /data/myblog/logs/error.log
   ```

## 项目开发团队

本项目由毕业设计团队开发，团队成员包括：
- 项目负责人：[denny]
- 后端开发：[denny]
- 前端开发：[denny]
- 测试：[denny]

## 许可证

本项目采用 MIT 许可证，详情请参见 LICENSE 文件。 