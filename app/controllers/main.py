"""
文件名：main.py
描述：主页路由控制器
作者：denny
"""

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """主页路由"""
    return render_template('index.html') 