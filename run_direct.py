#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
直接运行Flask应用
"""

try:
    from app import create_app
    app = create_app()
    print("应用创建成功")
    app.run(host='0.0.0.0', port=5001, debug=True)
except Exception as e:
    print(f"创建应用时出错: {str(e)}")
    import traceback
    traceback.print_exc() 