# MyBlog API设计文档

## 1. API概述

本文档描述了MyBlog系统的API接口设计，包括后台管理API和前台展示API。所有API都遵循RESTful设计规范。

## 2. 通用说明

### 2.1 基础URL
- 开发环境：`http://localhost:5000`
- 生产环境：`http://my.blog.com`

### 2.2 请求格式
- Content-Type: application/json
- 请求方法：GET, POST, PUT, DELETE

### 2.3 响应格式
```json
{
    "code": 200,          // 状态码
    "message": "success", // 状态信息
    "data": {}           // 响应数据
}
```

### 2.4 通用状态码
- 200: 成功
- 400: 请求参数错误
- 401: 未授权
- 403: 禁止访问
- 404: 资源不存在
- 500: 服务器错误

## 3. 认证接口

### 3.1 管理员登录
- 请求路径：`/api/auth/login`
- 请求方法：POST
- 请求参数：
```json
{
    "username": "admin",
    "password": "password"
}
```
- 响应数据：
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com"
        }
    }
}
```

### 3.2 退出登录
- 请求路径：`/api/auth/logout`
- 请求方法：POST
- 请求头：`Authorization: Bearer <token>`
- 响应数据：
```json
{
    "code": 200,
    "message": "success",
    "data": null
}
```

## 4. 文章管理接口

### 4.1 创建文章
- 请求路径：`/api/posts`
- 请求方法：POST
- 请求头：`Authorization: Bearer <token>`
- 请求参数：
```json
{
    "title": "文章标题",
    "content": "文章内容",
    "category_id": 1,
    "tags": [1, 2],
    "status": 1
}
```
- 响应数据：
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "title": "文章标题",
        "content": "文章内容",
        "category_id": 1,
        "author_id": 1,
        "status": 1,
        "created_at": "2024-03-20 10:00:00"
    }
}
```

### 4.2 获取文章列表
- 请求路径：`/api/posts`
- 请求方法：GET
- 请求参数：
  - page: 页码（默认1）
  - per_page: 每页数量（默认10）
  - category_id: 分类ID（可选）
  - tag_id: 标签ID（可选）
  - status: 状态（可选）
- 响应数据：
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "id": 1,
                "title": "文章标题",
                "summary": "文章摘要...",
                "category": {
                    "id": 1,
                    "name": "分类名称"
                },
                "author": {
                    "id": 1,
                    "username": "admin"
                },
                "created_at": "2024-03-20 10:00:00"
            }
        ],
        "total": 100,
        "page": 1,
        "per_page": 10
    }
}
```

### 4.3 获取文章详情
- 请求路径：`/api/posts/<int:id>`
- 请求方法：GET
- 响应数据：
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "title": "文章标题",
        "content": "文章内容",
        "category": {
            "id": 1,
            "name": "分类名称"
        },
        "tags": [
            {
                "id": 1,
                "name": "标签1"
            }
        ],
        "author": {
            "id": 1,
            "username": "admin"
        },
        "created_at": "2024-03-20 10:00:00",
        "updated_at": "2024-03-20 10:00:00"
    }
}
```

## 5. 分类管理接口

### 5.1 创建分类
- 请求路径：`/api/categories`
- 请求方法：POST
- 请求头：`Authorization: Bearer <token>`
- 请求参数：
```json
{
    "name": "分类名称",
    "description": "分类描述"
}
```

### 5.2 获取分类列表
- 请求路径：`/api/categories`
- 请求方法：GET
- 响应数据：
```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 1,
            "name": "分类名称",
            "description": "分类描述",
            "post_count": 10
        }
    ]
}
```

## 6. 评论管理接口

### 6.1 发表评论
- 请求路径：`/api/comments`
- 请求方法：POST
- 请求参数：
```json
{
    "post_id": 1,
    "parent_id": null,
    "content": "评论内容",
    "author_name": "访客名称",
    "author_email": "visitor@example.com"
}
```

### 6.2 获取文章评论
- 请求路径：`/api/posts/<int:post_id>/comments`
- 请求方法：GET
- 请求参数：
  - page: 页码（默认1）
  - per_page: 每页数量（默认10）
- 响应数据：
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "id": 1,
                "content": "评论内容",
                "author_name": "访客名称",
                "created_at": "2024-03-20 10:00:00",
                "replies": []
            }
        ],
        "total": 100,
        "page": 1,
        "per_page": 10
    }
}
```

## 7. 搜索接口

### 7.1 搜索文章
- 请求路径：`/api/search`
- 请求方法：GET
- 请求参数：
  - keyword: 搜索关键词
  - page: 页码（默认1）
  - per_page: 每页数量（默认10）
- 响应数据：
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "id": 1,
                "title": "文章标题",
                "summary": "文章摘要...",
                "created_at": "2024-03-20 10:00:00"
            }
        ],
        "total": 100,
        "page": 1,
        "per_page": 10
    }
}
```

## 8. 错误处理

### 8.1 参数验证错误
```json
{
    "code": 400,
    "message": "参数验证失败",
    "data": {
        "title": ["标题不能为空"],
        "content": ["内容长度不能小于10个字符"]
    }
}
```

### 8.2 认证错误
```json
{
    "code": 401,
    "message": "未授权访问",
    "data": null
}
```

### 8.3 权限错误
```json
{
    "code": 403,
    "message": "禁止访问",
    "data": null
}
```

## 9. API版本控制
- 当前版本：v1
- URL前缀：`/api/v1`
- 后续版本更新时，将在URL中体现版本号，确保向后兼容 