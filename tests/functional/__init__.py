"""
文件名：__init__.py
描述：测试包初始化文件
作者：denny
创建日期：2025-02-18
"""

import pytest
import logging

# 配置测试日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
) 