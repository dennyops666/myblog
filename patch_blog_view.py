#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复博客视图中的问题
"""

import os
import sys
import re
from datetime import datetime

def log(message):
    with open('patch_view.log', 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")

log("开始修补博客视图...")

# 确定视图文件路径
view_paths = [
    '/data/myblog/app/blog/views.py',
    '/data/myblog/app/views/blog.py',
    '/data/myblog/app/controllers/blog/views.py'
]

view_file = None
for path in view_paths:
    if os.path.exists(path):
        view_file = path
        log(f"找到视图文件: {path}")
        break

if not view_file:
    log("未找到博客视图文件")
    sys.exit(1)

# 读取源文件
with open(view_file, 'r', encoding='utf-8') as f:
    content = f.read()
    log(f"读取视图文件，长度: {len(content)}")

# 备份原始文件
backup_file = f"{view_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
with open(backup_file, 'w', encoding='utf-8') as f:
    f.write(content)
    log(f"已创建备份文件: {backup_file}")

# 修复版本信息部分
def fix_version_info(content):
    # 查找version_info代码块
    version_info_pattern = r'version_info\s*=\s*\{[^}]*\}'
    version_info_matches = re.findall(version_info_pattern, content, re.DOTALL)
    
    if version_info_matches:
        log(f"找到 {len(version_info_matches)} 个version_info代码块")
        for match in version_info_matches:
            log(f"原始代码块: {match}")
            
            # 修复日期格式问题
            fixed_code = match
            # 防止updated_at为None
            fixed_code = re.sub(
                r"updated_at':\s*post\.updated_at\.strftime",
                r"updated_at': post.updated_at.strftime if post.updated_at else 'N/A'",
                fixed_code
            )
            # 替换原始代码块
            content = content.replace(match, fixed_code)
            log("已修复version_info代码块")
    else:
        log("未找到version_info代码块")
    
    return content

# 修复datetime问题
def fix_datetime_issues(content):
    # 处理datetime格式化
    datetime_pattern = r'datetime\w*\.now\(\)\.strftime\([^)]*\)'
    datetime_matches = re.findall(datetime_pattern, content)
    
    if datetime_matches:
        log(f"找到 {len(datetime_matches)} 个datetime格式化代码")
        # 不需要修改，但记录下来
    else:
        log("未找到datetime格式化代码")
    
    return content

# 修复post_detail视图函数
def fix_post_detail_function(content):
    # 查找post_detail函数定义
    post_detail_pattern = r"@\w+\.route\(['\"]\/post\/<int:post_id>['\"].*?\)\s*def post_detail\(post_id\):.*?return render_template\("
    match = re.search(post_detail_pattern, content, re.DOTALL)
    
    if match:
        log("找到post_detail函数")
        func_start, func_end = match.span()
        
        # 尝试注入错误处理代码
        safe_code = """
    # 添加错误处理
    try:
        # 获取版本信息，安全处理
        version_info = {
            'content_length': len(post.content or ''),
            'html_length': len(post.html_content or ''),
            'updated_at': post.updated_at.strftime('%Y-%m-%d %H:%M:%S') if post.updated_at else 'N/A',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') if 'datetime' in globals() else 'N/A'
        }
    except Exception as e:
        # 出错时使用安全的默认版本信息
        version_info = {
            'content_length': 0,
            'html_length': 0,
            'updated_at': 'N/A',
            'timestamp': 'N/A',
            'error': str(e)
        }
        
"""
        # 查找version_info代码位置
        version_info_pattern = r'version_info\s*=\s*\{'
        version_info_match = re.search(version_info_pattern, content[func_start:])
        
        if version_info_match:
            log("找到version_info代码，准备替换")
            vi_start = func_start + version_info_match.start()
            # 尝试找到代码块结束位置
            brace_count = 1
            for i in range(vi_start + len('version_info = {'), len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        vi_end = i + 1
                        break
            
            if 'vi_end' in locals():
                # 替换version_info代码块
                modified_content = content[:vi_start] + safe_code + content[vi_end:]
                log("已替换version_info代码块")
                return modified_content
            else:
                log("无法确定version_info代码块结束位置")
        else:
            log("未找到version_info代码")
    else:
        log("未找到post_detail函数定义")
    
    return content

# 执行修复
modified_content = content
modified_content = fix_version_info(modified_content)
modified_content = fix_datetime_issues(modified_content)
modified_content = fix_post_detail_function(modified_content)

# 如果有修改，保存文件
if modified_content != content:
    with open(view_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)
        log("已保存修改后的视图文件")
else:
    log("视图文件没有修改") 