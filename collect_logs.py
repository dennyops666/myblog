#!/usr/bin/env python3
"""
日志收集脚本，用于收集和显示所有日志文件的内容
"""
import os
import glob
import sys

def collect_logs():
    """收集所有日志文件的内容"""
    log_dir = '/data/myblog/logs'
    if not os.path.exists(log_dir):
        print(f"日志目录不存在: {log_dir}")
        return False
    
    log_files = glob.glob(os.path.join(log_dir, '*.log'))
    if not log_files:
        print(f"未找到日志文件在: {log_dir}")
        return False
    
    print(f"找到 {len(log_files)} 个日志文件:")
    for log_file in log_files:
        print(f"\n{'=' * 50}")
        print(f"文件: {log_file}")
        print(f"大小: {os.path.getsize(log_file)} 字节")
        print(f"{'=' * 50}\n")
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content:
                    # 只显示最后1000个字符
                    if len(content) > 1000:
                        print(f"[显示最后1000个字符...]\n{content[-1000:]}")
                    else:
                        print(content)
                else:
                    print("文件为空")
        except Exception as e:
            print(f"读取文件时出错: {str(e)}")
    
    return True

def check_app_directory():
    """检查应用目录结构"""
    print("\n检查应用目录结构:")
    essential_dirs = [
        '/data/myblog/app',
        '/data/myblog/instance',
        '/data/myblog/logs',
        '/data/myblog/venv'
    ]
    
    for directory in essential_dirs:
        if os.path.exists(directory):
            print(f"{directory} - 存在")
        else:
            print(f"{directory} - 不存在")
    
    # 检查关键文件
    key_files = [
        '/data/myblog/manage.sh',
        '/data/myblog/instance/blog-dev.db',
        '/data/myblog/app/__init__.py',
        '/data/myblog/app/utils/logging.py'
    ]
    
    print("\n检查关键文件:")
    for file_path in key_files:
        if os.path.exists(file_path):
            print(f"{file_path} - 存在，大小: {os.path.getsize(file_path)} 字节")
        else:
            print(f"{file_path} - 不存在")

if __name__ == '__main__':
    print("开始收集日志信息...")
    result = collect_logs()
    
    if not result:
        print("\n日志收集失败，检查应用目录...")
        check_app_directory()
        
    print("\n日志收集完成.") 