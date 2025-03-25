#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
import requests
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试评论拒绝功能
print("开始测试评论拒绝功能...")

# 1. 检查数据库中评论的状态
db_path = "/data/myblog/instance/blog-dev.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\n1. 检查数据库中的评论状态")
cursor.execute("SELECT id, post_id, content, status FROM comments ORDER BY id")
comments = cursor.fetchall()
for comment in comments:
    comment_id, post_id, content, status = comment
    status_text = ["待审核", "已审核", "已拒绝"][status] if status in [0, 1, 2] else f"未知状态({status})"
    print(f"评论ID: {comment_id}, 文章ID: {post_id}, 状态: {status_text}, 内容: {content[:30]}...")

# 2. 测试拒绝评论API
print("\n2. 测试拒绝评论API")

# 获取一个已审核的评论进行拒绝测试
cursor.execute("SELECT id FROM comments WHERE status = 1 LIMIT 1")
result = cursor.fetchone()

if not result:
    print("没有找到已审核的评论用于测试")
    sys.exit(1)

comment_id = result[0]
print(f"使用评论ID {comment_id} 进行拒绝测试")

# 先登录获取会话
login_data = {"username": "admin", "password": "123456"}
session = requests.Session()
login_response = session.post(
    "http://localhost:5000/auth/login", 
    json=login_data
)

if login_response.status_code != 200:
    print(f"登录失败: {login_response.text}")
    sys.exit(1)

print("登录成功")

# 拒绝评论
reject_data = {"reject_replies": False}
# 尝试两个可能的URL路径
reject_urls = [
    f"http://localhost:5000/admin/comments/{comment_id}/reject",
    f"http://localhost:5000/comments/{comment_id}/reject"
]

success = False
for reject_url in reject_urls:
    print(f"尝试URL: {reject_url}")
    reject_response = session.post(
        reject_url,
        json=reject_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"状态码: {reject_response.status_code}")
    print(f"响应内容: {reject_response.text[:200]}...")  # 只显示前200个字符
    
    # 检查响应是否有效
    if reject_response.status_code == 200:
        try:
            response_data = reject_response.json()
            if response_data.get('success') == True:
                print(f"请求成功: {response_data}")
                success = True
                break
        except:
            print("响应不是有效的JSON格式")
    
    print(f"尝试的URL {reject_url} 请求失败")

if not success:
    print("所有尝试的URL都失败了")

# 3. 检查评论是否已被拒绝
print("\n3. 检查评论是否已被拒绝")
cursor.execute(f"SELECT status FROM comments WHERE id = {comment_id}")
status = cursor.fetchone()[0]
status_text = ["待审核", "已审核", "已拒绝"][status] if status in [0, 1, 2] else f"未知状态({status})"
print(f"评论 {comment_id} 当前状态: {status_text}")

# 4. 检查API是否正确过滤已拒绝的评论
print("\n4. 检查API是否正确过滤已拒绝的评论")
cursor.execute(f"SELECT post_id FROM comments WHERE id = {comment_id}")
post_id = cursor.fetchone()[0]

api_response = requests.get(f"http://localhost:5000/api/posts/{post_id}/comments")
if api_response.status_code == 200:
    api_data = api_response.json()
    if "data" in api_data:
        comments_data = api_data["data"]
        print(f"API返回的评论数量: {len(comments_data)}")
        
        # 检查是否包含被拒绝的评论
        rejected_comment_found = False
        for comment in comments_data:
            if comment.get('id') == comment_id:
                rejected_comment_found = True
                break
        
        if rejected_comment_found:
            print(f"错误: API仍然返回了已拒绝的评论 (ID: {comment_id})")
        else:
            print(f"成功: API正确过滤了已拒绝的评论 (ID: {comment_id})")
    else:
        print(f"错误: API响应格式不符合预期: {api_data}")
else:
    print(f"获取API评论失败: {api_response.status_code}, {api_response.text}")

conn.close()
print("\n测试完成") 