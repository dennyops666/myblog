#!/usr/bin/env python3
"""
详细的调试服务器，显示所有错误
"""
import sys
import os
import traceback
from app import create_app

try:
    print("正在尝试启动调试服务器...")
    app = create_app()
    
    # 设置详细的错误处理
    @app.errorhandler(Exception)
    def handle_error(error):
        print(f"发生错误: {error}")
        traceback.print_exc()
        return f"""
        <h1>服务器错误</h1>
        <pre>{traceback.format_exc()}</pre>
        """, 500
    
    # 添加测试路由
    @app.route('/debug-test')
    def debug_test():
        return "调试服务器正常工作!"
    
    print("调试服务器已创建，正在启动...")
    app.run(host='0.0.0.0', port=5000, debug=True)

except Exception as e:
    print(f"启动过程中发生错误: {e}")
    traceback.print_exc() 