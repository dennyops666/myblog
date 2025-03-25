#!/usr/bin/env python3
"""
调试脚本，用于检查应用启动错误
"""
import traceback
import sys

try:
    print("正在导入create_app函数...")
    from app import create_app
    print("导入成功，正在创建应用...")
    
    app = create_app()
    print("应用创建成功!")
    
except Exception as e:
    print(f"错误: {str(e)}")
    print("\n详细错误信息:")
    traceback.print_exc()
    sys.exit(1) 