from flask import Flask, request, redirect, url_for, render_template_string, send_from_directory, flash, jsonify
import os
from datetime import datetime
import json

app = Flask(__name__, static_folder='static')
app.secret_key = 'supersecretkey'

# 简单的内存用户数据库
users = {
    'admin': 'password'
}

# 简单的内存文章数据库
posts = [
    {
        'id': 1,
        'title': '欢迎使用博客系统',
        'content': '这是一篇测试文章，介绍如何使用博客系统。',
        'status': '已发布',
        'created_at': datetime(2025, 3, 24, 10, 30),
        'view_count': 15
    },
    {
        'id': 2,
        'title': '如何编写优质博客文章',
        'content': '这篇文章详细讲解如何编写高质量的博客文章，吸引更多读者。',
        'status': '已发布',
        'created_at': datetime(2025, 3, 23, 8, 45),
        'view_count': 8
    },
    {
        'id': 3,
        'title': '新功能开发计划',
        'content': '我们计划在下个月添加评论功能和标签管理...',
        'status': '草稿',
        'created_at': datetime(2025, 3, 22, 15, 20),
        'view_count': 0
    }
]

# 用于分类的内存数据库
categories = [
    {
        'id': 1,
        'name': '技术',
        'description': '技术相关文章'
    },
    {
        'id': 2,
        'name': '生活',
        'description': '生活分享'
    },
    {
        'id': 3,
        'name': '学习',
        'description': '学习经验'
    }
]

# 用于标签的内存数据库
tags = [
    {
        'id': 1,
        'name': 'Python',
        'description': 'Python编程语言'
    },
    {
        'id': 2,
        'name': 'Flask',
        'description': 'Flask Web框架'
    },
    {
        'id': 3,
        'name': '学习笔记',
        'description': '各类学习笔记'
    }
]

# 公共的基础布局模板
base_template = """
<!DOCTYPE html>
<html lang="zh-CN" class="{{ 'dark-theme' if request.cookies.get('theme') == 'dark' else '' }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}管理后台{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/admin.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/themes/dark.css') }}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        {% block extra_css %}{% endblock %}
    </style>
</head>
<body>
    <!-- 侧边栏 -->
    <div class="sidebar">
        <div class="sidebar-header">
            <h1>博客管理系统</h1>
        </div>
        <div class="sidebar-menu">
            <a href="/admin" class="{{ 'active' if active_page == 'admin' else '' }}">
                <i class="fas fa-home"></i>
                <span>首页</span>
            </a>
            <a href="/admin/posts" class="{{ 'active' if active_page == 'posts' else '' }}">
                <i class="fas fa-file-alt"></i>
                <span>文章管理</span>
            </a>
            <a href="/admin/categories" class="{{ 'active' if active_page == 'categories' else '' }}">
                <i class="fas fa-folder"></i>
                <span>分类管理</span>
            </a>
            <a href="/admin/tags" class="{{ 'active' if active_page == 'tags' else '' }}">
                <i class="fas fa-tags"></i>
                <span>标签管理</span>
            </a>
            <a href="/admin/comments" class="{{ 'active' if active_page == 'comments' else '' }}">
                <i class="fas fa-comments"></i>
                <span>评论管理</span>
            </a>
            <a href="/admin/users" class="{{ 'active' if active_page == 'users' else '' }}">
                <i class="fas fa-users"></i>
                <span>用户管理</span>
            </a>
            <a href="/admin/profile" class="{{ 'active' if active_page == 'profile' else '' }}">
                <i class="fas fa-user"></i>
                <span>个人资料</span>
            </a>
            <a href="/admin/settings" class="{{ 'active' if active_page == 'settings' else '' }}">
                <i class="fas fa-cog"></i>
                <span>系统设置</span>
            </a>
        </div>
        <div class="sidebar-footer">
            <a href="javascript:void(0);" class="theme-toggle" title="切换主题">
                <i class="fas fa-moon"></i>
                <span class="theme-toggle-icon">切换主题</span>
            </a>
            <a href="/logout">
                <i class="fas fa-sign-out-alt"></i>
                <span>退出</span>
            </a>
        </div>
    </div>
    
    <!-- 内容区域 -->
    <div class="container" style="margin-left: var(--sidebar-width); width: calc(100% - var(--sidebar-width));">
        <!-- 消息提示 -->
        {% if messages %}
            <div class="flash-messages">
            {% for category, message in messages %}
                <div class="alert alert-{{ category }} alert-dismissible">
                    {{ message }}
                    <button type="button" class="close" onclick="this.parentElement.style.display='none'">&times;</button>
                </div>
            {% endfor %}
            </div>
        {% endif %}
        
        <div class="content">
            {% block content %}{% endblock %}
        </div>
    </div>
    
    <script src="{{ url_for('static', filename='js/admin.js') }}"></script>
    <script src="{{ url_for('static', filename='js/theme-switcher.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
"""

# 管理面板模板
admin_template = """
{% extends 'base' %}

{% block title %}控制面板 - 管理后台{% endblock %}

{% block content %}
    <h2>控制面板</h2>
    <p>欢迎使用博客管理后台，{{ username }}。</p>
    
    <div class="stats">
        <div class="stat-box">
            <div class="stat-number">{{ post_count }}</div>
            <div>文章总数</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{{ published_count }}</div>
            <div>已发布</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{{ draft_count }}</div>
            <div>草稿</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{{ total_views }}</div>
            <div>总浏览量</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{{ category_count }}</div>
            <div>分类数</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{{ tag_count }}</div>
            <div>标签数</div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h3>最近文章</h3>
        </div>
        <div class="card-body">
            <table class="table">
                <thead>
                    <tr>
                        <th>标题</th>
                        <th>状态</th>
                        <th>创建时间</th>
                        <th>浏览量</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for post in recent_posts %}
                    <tr>
                        <td>{{ post.title }}</td>
                        <td>{{ post.status }}</td>
                        <td>{{ post.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                        <td>{{ post.view_count }}</td>
                        <td><a href="/admin/posts/{{ post.id }}" class="btn btn-sm btn-primary">查看</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}
"""

# 文章列表模板
posts_template = """
{% extends 'base' %}

{% block title %}文章管理 - 管理后台{% endblock %}

{% block content %}
    <h2>文章管理</h2>
    <div style="margin-bottom: 20px;">
        <a href="/admin/posts/new" class="btn btn-primary">新建文章</a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <table class="table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>标题</th>
                        <th>状态</th>
                        <th>创建时间</th>
                        <th>浏览量</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for post in posts %}
                    <tr>
                        <td>{{ post.id }}</td>
                        <td>{{ post.title }}</td>
                        <td>{{ post.status }}</td>
                        <td>{{ post.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                        <td>{{ post.view_count }}</td>
                        <td class="actions">
                            <a href="/admin/posts/{{ post.id }}" class="btn btn-sm btn-primary">查看</a>
                            <a href="/admin/posts/{{ post.id }}/edit" class="btn btn-sm btn-success">编辑</a>
                            <a href="#" onclick="if(confirm('确定要删除吗?')) window.location.href='/admin/posts/{{ post.id }}/delete';" class="btn btn-sm btn-danger">删除</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}
"""

# 登录页面模板
login_template = """
<!DOCTYPE html>
<html lang="zh-CN" class="{{ 'dark-theme' if request.cookies.get('theme') == 'dark' else '' }}">
<head>
    <title>管理员登录</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/admin.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/themes/dark.css') }}">
    <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 20px;
            background-color: var(--card-bg, #fff);
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 { text-align: center; margin-bottom: 20px; }
        .error { color: #dc3545; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>管理员登录</h1>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="post">
            <div class="form-group">
                <label for="username" class="form-label">用户名</label>
                <input type="text" id="username" name="username" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="password" class="form-label">密码</label>
                <input type="password" id="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary" style="width: 100%;">登录</button>
        </form>
        <div style="text-align: center; margin-top: 20px;">
            <a href="javascript:void(0);" class="theme-toggle" title="切换主题">
                <span class="theme-toggle-icon">🌙</span> 切换主题
            </a>
        </div>
    </div>
    
    <script src="{{ url_for('static', filename='js/theme-switcher.js') }}"></script>
</body>
</html>
"""

# 文章查看模板
post_view_template = """
{% extends 'base' %}

{% block title %}查看文章 - 管理后台{% endblock %}

{% block content %}
    <div style="margin-bottom: 20px;">
        <a href="/admin/posts" class="btn btn-secondary">返回列表</a>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h2>{{ post.title }}</h2>
            <div style="color: #666;">
                状态: {{ post.status }} | 创建时间: {{ post.created_at.strftime('%Y-%m-%d %H:%M') }} | 浏览量: {{ post.view_count }}
            </div>
        </div>
        <div class="card-body">
            <div style="line-height: 1.6;">
                {{ post.content }}
            </div>
            <div style="margin-top: 20px;">
                <a href="/admin/posts" class="btn btn-secondary">返回列表</a>
                <a href="/admin/posts/{{ post.id }}/edit" class="btn btn-success">编辑文章</a>
            </div>
        </div>
    </div>
{% endblock %}
"""

# 文章编辑模板
post_edit_template = """
{% extends 'base' %}

{% block title %}{% if post %}编辑文章{% else %}新建文章{% endif %} - 管理后台{% endblock %}

{% block extra_css %}
.editor-toolbar {
    padding: 10px;
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
}
.dark-theme .editor-toolbar {
    background-color: #333;
    border-color: #444;
}
.editor-toolbar button {
    margin-right: 10px;
    padding: 5px 10px;
    background: none;
    border: 1px solid #ccc;
    border-radius: 3px;
    cursor: pointer;
    font-size: 14px;
}
.dark-theme .editor-toolbar button {
    border-color: #555;
    color: #e0e0e0;
}
.editor-toolbar button:hover {
    background-color: #e9ecef;
}
.dark-theme .editor-toolbar button:hover {
    background-color: #444;
}
textarea#content-editor {
    min-height: 300px;
}
{% endblock %}

{% block content %}
    <div style="margin-bottom: 20px;">
        <a href="{% if post %}/admin/posts/{{ post.id }}{% else %}/admin/posts{% endif %}" class="btn btn-secondary">返回</a>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h2>{% if post %}编辑文章{% else %}新建文章{% endif %}</h2>
        </div>
        <div class="card-body">
            <form method="post">
                <div class="form-group">
                    <label for="title" class="form-label">标题</label>
                    <input type="text" id="title" name="title" class="form-control" value="{{ post.title if post else '' }}" required>
                </div>
                <div class="form-group">
                    <label for="content-editor" class="form-label">内容</label>
                    <textarea id="content-editor" name="content" class="form-control" required>{{ post.content if post else '' }}</textarea>
                </div>
                <div class="form-group">
                    <label for="status" class="form-label">状态</label>
                    <select id="status" name="status" class="form-control">
                        <option value="草稿" {% if post and post.status == '草稿' %}selected{% endif %}>草稿</option>
                        <option value="已发布" {% if post and post.status == '已发布' %}selected{% endif %}>已发布</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">保存</button>
                <a href="{% if post %}/admin/posts/{{ post.id }}{% else %}/admin/posts{% endif %}" class="btn btn-secondary">取消</a>
            </form>
        </div>
    </div>
{% endblock %}

{% block scripts %}
<script>
    // 当页面加载完毕时初始化编辑器
    document.addEventListener('DOMContentLoaded', function() {
        initializeEditor();
    });
</script>
{% endblock %}
"""

# 分类管理模板
categories_template = """
{% extends 'base' %}

{% block title %}分类管理 - 管理后台{% endblock %}

{% block content %}
    <h2>分类管理</h2>
    <div style="margin-bottom: 20px;">
        <a href="/admin/categories/new" class="btn btn-primary">新建分类</a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <table class="table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>名称</th>
                        <th>描述</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for category in categories %}
                    <tr>
                        <td>{{ category.id }}</td>
                        <td>{{ category.name }}</td>
                        <td>{{ category.description }}</td>
                        <td class="actions">
                            <a href="/admin/categories/{{ category.id }}/edit" class="btn btn-sm btn-success">编辑</a>
                            <a href="#" onclick="if(confirm('确定要删除分类「{{ category.name }}」吗?')) window.location.href='/admin/categories/{{ category.id }}/delete';" class="btn btn-sm btn-danger">删除</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}
"""

# 标签管理模板
tags_template = """
{% extends 'base' %}

{% block title %}标签管理 - 管理后台{% endblock %}

{% block content %}
    <h2>标签管理</h2>
    <div style="margin-bottom: 20px;">
        <a href="/admin/tags/new" class="btn btn-primary">新建标签</a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <table class="table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>名称</th>
                        <th>描述</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for tag in tags %}
                    <tr>
                        <td>{{ tag.id }}</td>
                        <td>{{ tag.name }}</td>
                        <td>{{ tag.description }}</td>
                        <td class="actions">
                            <a href="/admin/tags/{{ tag.id }}/edit" class="btn btn-sm btn-success">编辑</a>
                            <a href="#" onclick="if(confirm('确定要删除标签「{{ tag.name }}」吗?')) window.location.href='/admin/tags/{{ tag.id }}/delete';" class="btn btn-sm btn-danger">删除</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}
"""

@app.route('/')
def hello():
    return '欢迎访问博客系统！<a href="/admin">进入管理后台</a>'

@app.route('/admin')
@app.route('/admin/')
def admin():
    # 检查是否已登录
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 计算统计数据
    post_count = len(posts)
    published_count = sum(1 for post in posts if post['status'] == '已发布')
    draft_count = sum(1 for post in posts if post['status'] == '草稿')
    total_views = sum(post['view_count'] for post in posts)
    category_count = len(categories)
    tag_count = len(tags)
    
    # 获取最近的文章
    recent_posts = sorted(posts, key=lambda x: x['created_at'], reverse=True)[:3]
    
    # 使用扩展的base模板
    context = {
        'username': username,
        'post_count': post_count,
        'published_count': published_count,
        'draft_count': draft_count,
        'total_views': total_views,
        'category_count': category_count,
        'tag_count': tag_count,
        'recent_posts': recent_posts,
        'messages': [],
        'active_page': 'admin'  # 添加活动页面标记
    }
    
    return render_template_string(admin_template, **context, base=base_template)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username] == password:
            # 登录成功，设置cookie
            response = redirect(url_for('admin'))
            response.set_cookie('username', username)
            return response
        else:
            error = '用户名或密码错误'
    
    return render_template_string(login_template, error=error)

@app.route('/logout')
def logout():
    response = redirect(url_for('hello'))
    response.delete_cookie('username')
    return response

@app.route('/admin/posts')
def admin_posts():
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 按创建时间降序排序文章
    sorted_posts = sorted(posts, key=lambda x: x['created_at'], reverse=True)
    
    context = {
        'username': username,
        'posts': sorted_posts,
        'messages': [],
        'active_page': 'posts'  # 添加活动页面标记
    }
    
    return render_template_string(posts_template, **context, base=base_template)

@app.route('/admin/categories')
def admin_categories():
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    context = {
        'username': username,
        'categories': categories,
        'messages': [],
        'active_page': 'categories'  # 添加活动页面标记
    }
    
    return render_template_string(categories_template, **context, base=base_template)

@app.route('/admin/categories/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_category(category_id):
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 查找对应ID的分类
    category = next((c for c in categories if c['id'] == category_id), None)
    if not category:
        return "分类不存在", 404
    
    if request.method == 'POST':
        # 更新分类信息
        category['name'] = request.form.get('name')
        category['description'] = request.form.get('description')
        
        return redirect(url_for('admin_categories'))
    
    # 分类编辑模板
    category_edit_template = """
    {% extends 'base' %}
    
    {% block title %}编辑分类 - 管理后台{% endblock %}
    
    {% block content %}
        <div style="margin-bottom: 20px;">
            <a href="/admin/categories" class="btn btn-secondary">返回分类列表</a>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2>编辑分类</h2>
            </div>
            <div class="card-body">
                <form method="post">
                    <div class="form-group">
                        <label for="name" class="form-label">名称</label>
                        <input type="text" id="name" name="name" class="form-control" value="{{ category.name }}" required>
                    </div>
                    <div class="form-group">
                        <label for="description" class="form-label">描述</label>
                        <textarea id="description" name="description" class="form-control">{{ category.description }}</textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">保存</button>
                    <a href="/admin/categories" class="btn btn-secondary">取消</a>
                </form>
            </div>
        </div>
    {% endblock %}
    """
    
    context = {
        'username': username,
        'category': category,
        'messages': [],
        'active_page': 'categories'  # 编辑分类页面使用categories标记
    }
    
    return render_template_string(category_edit_template, **context, base=base_template)

# 添加创建新分类的路由
@app.route('/admin/categories/new', methods=['GET', 'POST'])
def new_category():
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # 创建新分类
        new_id = max(category['id'] for category in categories) + 1 if categories else 1
        new_category = {
            'id': new_id,
            'name': request.form.get('name'),
            'description': request.form.get('description')
        }
        categories.append(new_category)
        
        return redirect(url_for('admin_categories'))
    
    # 新建分类模板
    category_new_template = """
    {% extends 'base' %}
    
    {% block title %}新建分类 - 管理后台{% endblock %}
    
    {% block content %}
        <div style="margin-bottom: 20px;">
            <a href="/admin/categories" class="btn btn-secondary">返回分类列表</a>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2>新建分类</h2>
            </div>
            <div class="card-body">
                <form method="post">
                    <div class="form-group">
                        <label for="name" class="form-label">名称</label>
                        <input type="text" id="name" name="name" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label for="description" class="form-label">描述</label>
                        <textarea id="description" name="description" class="form-control"></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">保存</button>
                    <a href="/admin/categories" class="btn btn-secondary">取消</a>
                </form>
            </div>
        </div>
    {% endblock %}
    """
    
    context = {
        'username': username,
        'messages': [],
        'active_page': 'categories'  # 新建分类页面使用categories标记
    }
    
    return render_template_string(category_new_template, **context, base=base_template)

# 添加处理/admin/category/ID/edit URL重定向的路由（兼容处理）
@app.route('/admin/category/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_category_singular(category_id):
    # 重定向到正确的URL格式
    return redirect(url_for('edit_category', category_id=category_id))

# 添加删除分类的路由
@app.route('/admin/categories/<int:category_id>/delete')
def delete_category(category_id):
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 查找并删除对应ID的分类
    global categories
    categories = [c for c in categories if c['id'] != category_id]
    
    return redirect(url_for('admin_categories'))

# 添加处理/admin/category/ID/delete URL重定向的路由（兼容处理）
@app.route('/admin/category/<int:category_id>/delete')
def delete_category_singular(category_id):
    # 重定向到正确的URL格式
    return redirect(url_for('delete_category', category_id=category_id))

@app.route('/admin/tags')
def admin_tags():
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    context = {
        'username': username,
        'tags': tags,
        'messages': [],
        'active_page': 'tags'  # 添加活动页面标记
    }
    
    return render_template_string(tags_template, **context, base=base_template)

@app.route('/admin/users')
def admin_users():
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 示例用户数据
    user_list = [
        {
            'id': 1,
            'username': 'admin',
            'email': 'admin@example.com',
            'role': '管理员',
            'created_at': datetime(2025, 3, 20, 10, 0)
        },
        {
            'id': 2,
            'username': 'editor',
            'email': 'editor@example.com',
            'role': '编辑',
            'created_at': datetime(2025, 3, 21, 14, 30)
        },
        {
            'id': 3,
            'username': 'user1',
            'email': 'user1@example.com',
            'role': '普通用户',
            'created_at': datetime(2025, 3, 22, 9, 15)
        }
    ]
    
    # 用户管理模板
    users_template = """
    {% extends 'base' %}
    
    {% block title %}用户管理 - 管理后台{% endblock %}
    
    {% block content %}
        <h2>用户管理</h2>
        <div style="margin-bottom: 20px;">
            <a href="/admin/users/new" class="btn btn-primary">新建用户</a>
        </div>
        
        <div class="card">
            <div class="card-body">
                <table class="table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>用户名</th>
                            <th>邮箱</th>
                            <th>角色</th>
                            <th>创建时间</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for user in user_list %}
                        <tr>
                            <td>{{ user.id }}</td>
                            <td>{{ user.username }}</td>
                            <td>{{ user.email }}</td>
                            <td>{{ user.role }}</td>
                            <td>{{ user.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                            <td class="actions">
                                <a href="/admin/users/{{ user.id }}/edit" class="btn btn-sm btn-success">编辑</a>
                                <a href="#" onclick="if(confirm('确定要删除用户「{{ user.username }}」吗?')) window.location.href='/admin/users/{{ user.id }}/delete';" class="btn btn-sm btn-danger">删除</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    {% endblock %}
    """
    
    context = {
        'username': username,
        'user_list': user_list,
        'messages': [],
        'active_page': 'users'  # 添加活动页面标记
    }
    
    return render_template_string(users_template, **context, base=base_template)

# 添加用户编辑的路由
@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])  # 兼容旧URL
def edit_user(user_id):
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 示例用户数据
    user_data = {
        1: {
            'id': 1,
            'username': 'admin',
            'email': 'admin@example.com',
            'role': '管理员',
            'created_at': datetime(2025, 3, 20, 10, 0)
        },
        2: {
            'id': 2,
            'username': 'editor',
            'email': 'editor@example.com',
            'role': '编辑',
            'created_at': datetime(2025, 3, 21, 14, 30)
        },
        3: {
            'id': 3,
            'username': 'user1',
            'email': 'user1@example.com',
            'role': '普通用户',
            'created_at': datetime(2025, 3, 22, 9, 15)
        }
    }
    
    # 查找对应ID的用户
    user = user_data.get(user_id)
    if not user:
        return "用户不存在", 404
    
    if request.method == 'POST':
        # 这里只是模拟更新，实际不会保存
        return redirect(url_for('admin_users'))
    
    # 用户编辑模板
    user_edit_template = """
    {% extends 'base' %}
    
    {% block title %}编辑用户 - 管理后台{% endblock %}
    
    {% block content %}
        <div style="margin-bottom: 20px;">
            <a href="/admin/users" class="btn btn-secondary">返回用户列表</a>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2>编辑用户</h2>
            </div>
            <div class="card-body">
                <form method="post">
                    <div class="form-group">
                        <label for="username" class="form-label">用户名</label>
                        <input type="text" id="username" name="username" class="form-control" value="{{ user.username }}" required>
                    </div>
                    <div class="form-group">
                        <label for="email" class="form-label">邮箱</label>
                        <input type="email" id="email" name="email" class="form-control" value="{{ user.email }}" required>
                    </div>
                    <div class="form-group">
                        <label for="role" class="form-label">角色</label>
                        <select id="role" name="role" class="form-control">
                            <option value="管理员" {% if user.role == '管理员' %}selected{% endif %}>管理员</option>
                            <option value="编辑" {% if user.role == '编辑' %}selected{% endif %}>编辑</option>
                            <option value="普通用户" {% if user.role == '普通用户' %}selected{% endif %}>普通用户</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="password" class="form-label">密码</label>
                        <input type="password" id="password" name="password" class="form-control" placeholder="留空则不修改">
                    </div>
                    <button type="submit" class="btn btn-primary">保存</button>
                    <a href="/admin/users" class="btn btn-secondary">取消</a>
                </form>
            </div>
        </div>
    {% endblock %}
    """
    
    context = {
        'username': username,
        'user': user,
        'messages': [],
        'active_page': 'users'  # 用户编辑页面使用users标记
    }
    
    return render_template_string(user_edit_template, **context, base=base_template)

# 添加评论拒绝的路由
@app.route('/admin/comment/reject/<int:comment_id>', methods=['POST'])
def reject_comment(comment_id):
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 这里只是模拟拒绝评论的操作，实际不会保存
    return redirect(url_for('admin_comments'))

@app.route('/admin/comment/approve/<int:comment_id>', methods=['POST'])
def approve_comment(comment_id):
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 这里只是模拟审核通过评论的操作，实际不会保存
    return redirect(url_for('admin_comments'))

@app.route('/admin/settings')
def admin_settings():
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    context = {
        'username': username,
        'messages': [],
        'active_page': 'settings'  # 添加活动页面标记
    }
    
    return render_template_string("系统设置页面 - 建设中", **context, base=base_template)

@app.route('/admin/profile')
def admin_profile():
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    context = {
        'username': username,
        'messages': [],
        'active_page': 'profile'  # 添加活动页面标记
    }
    
    return render_template_string("个人资料页面 - 建设中", **context, base=base_template)

@app.route('/favicon.ico')
def favicon():
    """处理favicon请求，避免404错误"""
    # 使用Flask应用的静态文件夹路径
    return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/admin/posts/<int:post_id>')
def view_post(post_id):
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 查找对应ID的文章
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return "文章不存在", 404
    
    context = {
        'username': username,
        'post': post,
        'messages': [],
        'active_page': 'posts'  # 文章详情页面使用posts标记
    }
    
    return render_template_string(post_view_template, **context, base=base_template)

@app.route('/admin/posts/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 查找对应ID的文章
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return "文章不存在", 404
    
    if request.method == 'POST':
        # 更新文章信息
        post['title'] = request.form.get('title')
        post['content'] = request.form.get('content')
        post['status'] = request.form.get('status')
        
        return redirect(url_for('view_post', post_id=post_id))
    
    context = {
        'username': username,
        'post': post,
        'messages': [],
        'active_page': 'posts'  # 编辑文章页面使用posts标记
    }
    
    return render_template_string(post_edit_template, **context, base=base_template)

@app.route('/admin/posts/new', methods=['GET', 'POST'])
def new_post():
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # 创建新文章
        new_id = max(post['id'] for post in posts) + 1 if posts else 1
        new_post = {
            'id': new_id,
            'title': request.form.get('title'),
            'content': request.form.get('content'),
            'status': request.form.get('status'),
            'created_at': datetime.now(),
            'view_count': 0
        }
        posts.append(new_post)
        
        return redirect(url_for('view_post', post_id=new_id))
    
    context = {
        'username': username,
        'post': None,
        'messages': [],
        'active_page': 'posts'  # 新建文章页面使用posts标记
    }
    
    return render_template_string(post_edit_template, **context, base=base_template)

@app.route('/admin/posts/<int:post_id>/delete')
def delete_post(post_id):
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 查找并删除对应ID的文章
    global posts
    posts = [p for p in posts if p['id'] != post_id]
    
    return redirect(url_for('admin_posts'))

@app.route('/admin/comments')
def admin_comments():
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 示例评论数据
    comments = [
        {
            'id': 1,
            'post_title': '欢迎使用博客系统',
            'author': '张三',
            'content': '这个博客系统非常好用！',
            'created_at': datetime(2025, 3, 23, 15, 30),
            'status': '已审核'
        },
        {
            'id': 2,
            'post_title': '如何编写优质博客文章',
            'author': '李四',
            'content': '文章写得很详细，学到了很多！',
            'created_at': datetime(2025, 3, 24, 9, 15),
            'status': '待审核'
        },
        {
            'id': 3,
            'post_title': '欢迎使用博客系统',
            'author': '王五',
            'content': '期待更多功能的更新！',
            'created_at': datetime(2025, 3, 24, 10, 45),
            'status': '已审核'
        }
    ]
    
    comments_template = """
    {% extends 'base' %}
    
    {% block title %}评论管理 - 管理后台{% endblock %}
    
    {% block content %}
        <h2>评论管理</h2>
        
        <div class="card">
            <div class="card-body">
                <table class="table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>文章</th>
                            <th>作者</th>
                            <th>内容</th>
                            <th>时间</th>
                            <th>状态</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for comment in comments %}
                        <tr>
                            <td>{{ comment.id }}</td>
                            <td>{{ comment.post_title }}</td>
                            <td>{{ comment.author }}</td>
                            <td>{{ comment.content[:30] }}{% if comment.content|length > 30 %}...{% endif %}</td>
                            <td>{{ comment.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                            <td>{{ comment.status }}</td>
                            <td class="actions">
                                <a href="#" class="btn btn-sm btn-success">审核</a>
                                <a href="#" onclick="if(confirm('确定要删除此评论吗?')) alert('评论已删除');" class="btn btn-sm btn-danger">删除</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    {% endblock %}
    """
    
    context = {
        'username': username,
        'comments': comments,
        'messages': [],
        'active_page': 'comments'  # 添加活动页面标记
    }
    
    return render_template_string(comments_template, **context, base=base_template)

# 添加评论详情路由处理函数
@app.route('/admin/comment/<int:comment_id>')
def view_comment(comment_id):
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 根据评论ID获取评论
    comment = {
        'id': comment_id,
        'post_title': '欢迎使用博客系统',
        'post_id': 1,
        'author': '张三',
        'content': '这个博客系统非常好用！期待更多功能的更新。',
        'created_at': datetime(2025, 3, 23, 15, 30),
        'status': '已审核'
    }
    
    comment_view_template = """
    {% extends 'base' %}
    
    {% block title %}评论详情 - 管理后台{% endblock %}
    
    {% block content %}
        <div style="margin-bottom: 20px;">
            <a href="/admin/comments" class="btn btn-secondary">返回评论列表</a>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2>评论详情</h2>
                <div style="color: #666;">
                    文章: {{ comment.post_title }} | 作者: {{ comment.author }} | 
                    时间: {{ comment.created_at.strftime('%Y-%m-%d %H:%M') }} | 状态: {{ comment.status }}
                </div>
            </div>
            <div class="card-body">
                <div style="line-height: 1.6;">
                    {{ comment.content }}
                </div>
                <div style="margin-top: 20px;">
                    <a href="/admin/comments" class="btn btn-secondary">返回列表</a>
                    <a href="#" class="btn btn-success">审核评论</a>
                    <a href="#" onclick="if(confirm('确定要删除此评论吗?')) alert('评论已删除');" class="btn btn-danger">删除评论</a>
                </div>
            </div>
        </div>
    {% endblock %}
    """
    
    context = {
        'username': username,
        'comment': comment,
        'messages': [],
        'active_page': 'comments'  # 添加活动页面标记，确保评论详情页面高亮评论菜单
    }
    
    return render_template_string(comment_view_template, **context, base=base_template)

# 添加标签编辑的路由
@app.route('/admin/tags/<int:tag_id>/edit', methods=['GET', 'POST'])
def edit_tag(tag_id):
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 查找对应ID的标签
    tag = next((t for t in tags if t['id'] == tag_id), None)
    if not tag:
        return "标签不存在", 404
    
    if request.method == 'POST':
        # 更新标签信息
        tag['name'] = request.form.get('name')
        tag['description'] = request.form.get('description')
        
        return redirect(url_for('admin_tags'))
    
    # 标签编辑模板
    tag_edit_template = """
    {% extends 'base' %}
    
    {% block title %}编辑标签 - 管理后台{% endblock %}
    
    {% block content %}
        <div style="margin-bottom: 20px;">
            <a href="/admin/tags" class="btn btn-secondary">返回标签列表</a>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2>编辑标签</h2>
            </div>
            <div class="card-body">
                <form method="post">
                    <div class="form-group">
                        <label for="name" class="form-label">名称</label>
                        <input type="text" id="name" name="name" class="form-control" value="{{ tag.name }}" required>
                    </div>
                    <div class="form-group">
                        <label for="description" class="form-label">描述</label>
                        <textarea id="description" name="description" class="form-control">{{ tag.description }}</textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">保存</button>
                    <a href="/admin/tags" class="btn btn-secondary">取消</a>
                </form>
            </div>
        </div>
    {% endblock %}
    """
    
    context = {
        'username': username,
        'tag': tag,
        'messages': [],
        'active_page': 'tags'  # 编辑标签页面使用tags标记
    }
    
    return render_template_string(tag_edit_template, **context, base=base_template)

# 添加创建新标签的路由
@app.route('/admin/tags/new', methods=['GET', 'POST'])
@app.route('/admin/tag/create', methods=['GET', 'POST'])  # 兼容旧URL
def new_tag():
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # 创建新标签
        new_id = max(tag['id'] for tag in tags) + 1 if tags else 1
        new_tag = {
            'id': new_id,
            'name': request.form.get('name'),
            'description': request.form.get('description')
        }
        tags.append(new_tag)
        
        return redirect(url_for('admin_tags'))
    
    # 新建标签模板
    tag_new_template = """
    {% extends 'base' %}
    
    {% block title %}新建标签 - 管理后台{% endblock %}
    
    {% block content %}
        <div style="margin-bottom: 20px;">
            <a href="/admin/tags" class="btn btn-secondary">返回标签列表</a>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2>新建标签</h2>
            </div>
            <div class="card-body">
                <form method="post">
                    <div class="form-group">
                        <label for="name" class="form-label">名称</label>
                        <input type="text" id="name" name="name" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label for="description" class="form-label">描述</label>
                        <textarea id="description" name="description" class="form-control"></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">保存</button>
                    <a href="/admin/tags" class="btn btn-secondary">取消</a>
                </form>
            </div>
        </div>
    {% endblock %}
    """
    
    context = {
        'username': username,
        'messages': [],
        'active_page': 'tags'  # 新建标签页面使用tags标记
    }
    
    return render_template_string(tag_new_template, **context, base=base_template)

# 添加删除标签的路由
@app.route('/admin/tags/<int:tag_id>/delete')
def delete_tag(tag_id):
    username = request.cookies.get('username')
    if not username or username not in users:
        return redirect(url_for('login'))
    
    # 查找并删除对应ID的标签
    global tags
    tags = [t for t in tags if t['id'] != tag_id]
    
    return redirect(url_for('admin_tags'))

# 添加处理/admin/tag/ID/edit URL重定向的路由（兼容处理）
@app.route('/admin/tag/<int:tag_id>/edit', methods=['GET', 'POST'])
def edit_tag_singular(tag_id):
    # 重定向到正确的URL格式
    return redirect(url_for('edit_tag', tag_id=tag_id))

# 添加处理/admin/tag/ID/delete URL重定向的路由（兼容处理）
@app.route('/admin/tag/<int:tag_id>/delete')
def delete_tag_singular(tag_id):
    # 重定向到正确的URL格式
    return redirect(url_for('delete_tag', tag_id=tag_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 