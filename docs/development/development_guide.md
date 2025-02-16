# MyBlog 开发指南

## 1. 开发环境配置

### 1.1 基础环境准备
- Python 3.8+
- Git
- VSCode 或 PyCharm（推荐的IDE）
- SQLite 数据库工具（如 SQLite Browser）

### 1.2 开发环境设置
```bash
# 1. 克隆项目
git clone git@github.com:dennyops666/myblog.git
cd /data/myblog

# 2. 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装开发依赖
pip install -r requirements-dev.txt
```

### 1.3 IDE配置
#### VSCode 配置
1. 安装推荐的扩展：
   - Python
   - Python Extension Pack
   - GitLens
   - SQLite Viewer
   
2. 工作区设置（.vscode/settings.json）：
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "python.linting.flake8Enabled": true
}
```

## 2. 项目结构说明

### 2.1 核心目录结构
```
/data/myblog/
├── app/                    # 应用主目录
│   ├── __init__.py        # 应用初始化
│   ├── config.py          # 配置文件
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑
│   ├── controllers/       # 控制器
│   ├── templates/         # 模板文件
│   └── static/            # 静态文件
├── tests/                 # 测试目录
├── migrations/            # 数据库迁移
├── requirements.txt       # 生产环境依赖
├── requirements-dev.txt   # 开发环境依赖
└── run.py                # 应用入口
```

### 2.2 配置文件说明
1. config.py 配置类：
```python
class Config:
    SECRET_KEY = 'dev'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///myblog.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
```

## 3. 开发规范

### 3.1 Python代码规范
1. 遵循PEP 8规范
2. 使用Black进行代码格式化
3. 命名规范：
   - 类名：使用驼峰命名法（CamelCase）
   - 函数和变量：使用下划线命名法（snake_case）
   - 常量：全大写加下划线（UPPER_CASE）

### 3.2 注释规范
1. 文件头部注释：
```python
"""
文件名：xxx.py
描述：简要说明模块功能
作者：作者名
创建日期：YYYY-MM-DD
"""
```

2. 函数注释：
```python
def function_name(param1: type, param2: type) -> return_type:
    """
    函数功能简述
    
    Args:
        param1 (type): 参数1说明
        param2 (type): 参数2说明
        
    Returns:
        return_type: 返回值说明
        
    Raises:
        Exception: 异常说明
    """
    pass
```

### 3.3 Git提交规范
1. 提交信息格式：
```
<type>(<scope>): <subject>

<body>

<footer>
```

2. type类型：
   - feat: 新功能
   - fix: 修复bug
   - docs: 文档更新
   - style: 代码格式调整
   - refactor: 重构代码
   - test: 测试相关
   - chore: 构建过程或辅助工具的变动

## 4. 开发流程

### 4.1 功能开发流程
1. 创建功能分支
```bash
git checkout -b feature/feature-name
```

2. 编写代码和测试
3. 运行测试
```bash
pytest tests/
```

4. 提交代码
```bash
git add .
git commit -m "feat(module): add new feature"
git push origin feature/feature-name
```

5. 创建Pull Request
6. 代码审查
7. 合并到主分支

### 4.2 数据库迁移流程
1. 创建迁移
```bash
flask db migrate -m "migration description"
```

2. 检查迁移文件
3. 应用迁移
```bash
flask db upgrade
```

4. 回滚迁移（如果需要）
```bash
flask db downgrade
```

## 5. 测试指南

### 5.1 单元测试
1. 测试文件命名：`test_*.py`
2. 测试类命名：`Test*`
3. 测试方法命名：`test_*`

示例：
```python
# tests/test_models.py
def test_create_user():
    """测试创建用户"""
    user = User(username='test', email='test@example.com')
    db.session.add(user)
    db.session.commit()
    assert user.id is not None
```

### 5.2 测试覆盖率
```bash
# 运行测试并生成覆盖率报告
pytest --cov=app tests/
```

## 6. 调试技巧

### 6.1 使用Flask调试器
```python
from flask import current_app
current_app.logger.debug('Debug message')
```

### 6.2 使用PDB调试
```python
import pdb; pdb.set_trace()
```

### 6.3 日志配置
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 7. 性能优化

### 7.1 数据库查询优化
1. 使用索引
2. 避免N+1查询问题
3. 使用延迟加载和即时加载

### 7.2 缓存策略
1. 使用Flask-Caching
```python
from flask_caching import Cache
cache = Cache()

@cache.cached(timeout=300)
def get_posts():
    return Post.query.all()
```

## 8. 安全开发指南

### 8.1 输入验证
1. 使用WTForms进行表单验证
2. 实施XSS防护
3. 实施CSRF防护

### 8.2 密码安全
1. 使用Werkzeug进行密码哈希
```python
from werkzeug.security import generate_password_hash, check_password_hash
```

### 8.3 SQL注入防护
1. 使用SQLAlchemy ORM
2. 避免原生SQL
3. 使用参数化查询

## 9. API开发指南

### 9.1 RESTful API设计
1. 使用合适的HTTP方法
2. 实现合适的状态码
3. 提供清晰的错误信息

### 9.2 API文档
1. 使用Flask-RESTful
2. 使用Swagger/OpenAPI规范
3. 提供API示例

## 10. 前端开发指南

### 10.1 模板开发
1. 使用Jinja2模板继承
2. 实现响应式设计
3. 使用Bootstrap组件

### 10.2 静态资源管理
1. 使用Flask-Assets
2. 实现资源压缩
3. 配置缓存策略

## 11. 部署检查清单

### 11.1 部署前检查
1. 运行所有测试
2. 检查依赖更新
3. 检查配置文件
4. 备份数据库

### 11.2 部署后检查
1. 验证功能正常
2. 检查日志输出
3. 监控系统性能
4. 测试备份恢复 