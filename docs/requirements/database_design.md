# MyBlog 数据库设计文档

## 1. 数据库概述

本系统采用SQLite数据库，主要包含用户、文章、分类、标签、评论等相关表。

## 2. 数据库表设计

### 2.1 用户表 (users)

| 字段名 | 类型 | 长度 | 允许空 | 主键 | 说明 |
|--------|------|------|--------|------|------|
| id | INTEGER | - | 否 | 是 | 用户ID |
| username | VARCHAR | 50 | 否 | 否 | 用户名 |
| password | VARCHAR | 128 | 否 | 否 | 密码（加密存储）|
| email | VARCHAR | 120 | 否 | 否 | 电子邮箱 |
| created_at | DATETIME | - | 否 | 否 | 创建时间 |
| updated_at | DATETIME | - | 否 | 否 | 更新时间 |

### 2.2 文章表 (posts)

| 字段名 | 类型 | 长度 | 允许空 | 主键 | 说明 |
|--------|------|------|--------|------|------|
| id | INTEGER | - | 否 | 是 | 文章ID |
| title | VARCHAR | 200 | 否 | 否 | 文章标题 |
| content | TEXT | - | 否 | 否 | 文章内容（Markdown格式）|
| category_id | INTEGER | - | 否 | 否 | 分类ID（外键）|
| author_id | INTEGER | - | 否 | 否 | 作者ID（外键）|
| status | TINYINT | - | 否 | 否 | 状态（0草稿，1发布）|
| view_count | INTEGER | - | 否 | 否 | 浏览次数 |
| created_at | DATETIME | - | 否 | 否 | 创建时间 |
| updated_at | DATETIME | - | 否 | 否 | 更新时间 |

### 2.3 分类表 (categories)

| 字段名 | 类型 | 长度 | 允许空 | 主键 | 说明 |
|--------|------|------|--------|------|------|
| id | INTEGER | - | 否 | 是 | 分类ID |
| name | VARCHAR | 50 | 否 | 否 | 分类名称 |
| description | VARCHAR | 200 | 是 | 否 | 分类描述 |
| created_at | DATETIME | - | 否 | 否 | 创建时间 |

### 2.4 标签表 (tags)

| 字段名 | 类型 | 长度 | 允许空 | 主键 | 说明 |
|--------|------|------|--------|------|------|
| id | INTEGER | - | 否 | 是 | 标签ID |
| name | VARCHAR | 50 | 否 | 否 | 标签名称 |
| created_at | DATETIME | - | 否 | 否 | 创建时间 |

### 2.5 文章标签关联表 (post_tags)

| 字段名 | 类型 | 长度 | 允许空 | 主键 | 说明 |
|--------|------|------|--------|------|------|
| post_id | INTEGER | - | 否 | 是 | 文章ID |
| tag_id | INTEGER | - | 否 | 是 | 标签ID |

### 2.6 评论表 (comments)

| 字段名 | 类型 | 长度 | 允许空 | 主键 | 说明 |
|--------|------|------|--------|------|------|
| id | INTEGER | - | 否 | 是 | 评论ID |
| post_id | INTEGER | - | 否 | 否 | 文章ID（外键）|
| parent_id | INTEGER | - | 是 | 否 | 父评论ID |
| content | TEXT | - | 否 | 否 | 评论内容 |
| author_name | VARCHAR | 50 | 否 | 否 | 评论者名称 |
| author_email | VARCHAR | 120 | 否 | 否 | 评论者邮箱 |
| status | TINYINT | - | 否 | 否 | 状态（0待审核，1通过）|
| created_at | DATETIME | - | 否 | 否 | 创建时间 |

## 3. 表关系说明

1. 文章表与用户表：多对一关系（一个用户可以发布多篇文章）
2. 文章表与分类表：多对一关系（一个分类可以包含多篇文章）
3. 文章表与标签表：多对多关系（通过post_tags关联表实现）
4. 评论表与文章表：多对一关系（一篇文章可以有多条评论）
5. 评论表自关联：实现评论的层级关系（回复功能）

## 4. 索引设计

1. 用户表：
   - username: UNIQUE索引
   - email: UNIQUE索引

2. 文章表：
   - category_id: 普通索引
   - created_at: 普通索引
   - status: 普通索引

3. 评论表：
   - post_id: 普通索引
   - status: 普通索引

## 5. 数据库维护建议

1. 定期备份数据库文件
2. 监控数据库大小
3. 定期清理无用数据
4. 适时进行数据库优化 