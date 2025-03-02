"""
文件名：test.py
描述：测试视图
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, request, jsonify, session
from flask_wtf.csrf import generate_csrf
from app.services import SecurityService
from app.extensions import db
from app.models import User
from flask_wtf.csrf import csrf_protect
from app.utils import sql_injection_protect, xss_protect
from werkzeug.security import check_password_hash

test_bp = Blueprint('test', __name__)
security_service = SecurityService()

@test_bp.route('/login', methods=['GET', 'POST'])
@csrf_protect()
@sql_injection_protect()
def login():
    """测试登录路由"""
    if request.method == 'GET':
        csrf_token = generate_csrf()
        return f'''
            <form method="post">
                <input type="hidden" name="csrf_token" value="{csrf_token}">
                <input type="text" name="username">
                <input type="password" name="password">
                <button type="submit">登录</button>
            </form>
        '''
    
    username = request.form.get('username')
    password = request.form.get('password')
    
    # 清理输入
    username = security_service.sanitize_input(username)
    password = security_service.sanitize_input(password)
    
    # 检查密码强度
    if not security_service.check_password_strength(password):
        return jsonify({'error': '密码强度不足'}), 400
    
    # 使用参数化查询防止SQL注入
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    # 设置安全的会话
    session.permanent = True
    session['user_id'] = user.id
    session['_fresh'] = True
    
    return jsonify({'message': '登录成功'})

@test_bp.route('/api/posts', methods=['POST'])
@csrf_protect()
@xss_protect()
def create_post():
    """测试API创建文章"""
    if not security_service.validate_api_request(request):
        return jsonify({'error': '无效的API请求'}), 400
    
    if not request.is_json:
        return jsonify({'error': '需要JSON格式数据'}), 400
    
    data = request.get_json()
    # 清理输入
    clean_data = security_service.sanitize_input(data)
    # 保护敏感数据
    safe_data = security_service.protect_sensitive_data(clean_data)
    
    return jsonify({'message': '文章创建成功', 'data': safe_data}), 201

@test_bp.route('/upload', methods=['POST'])
@csrf_protect()
def upload_file():
    """测试文件上传"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
        
    if not security_service.validate_file_type(file.filename):
        return jsonify({'error': '不允许的文件类型'}), 400
    
    if not security_service.check_file_content(file):
        return jsonify({'error': '文件内容不安全'}), 400
        
    filename = security_service.sanitize_filename(file.filename)
    return jsonify({'message': '文件上传成功', 'filename': filename}), 200

@test_bp.route('/search')
@sql_injection_protect()
@xss_protect()
def search():
    """测试搜索功能"""
    query = request.args.get('q', '')
    # 清理输入
    clean_query = security_service.sanitize_input(query)
    
    # 模拟搜索结果
    results = [{'id': 1, 'title': f'搜索结果: {clean_query}'}]
    return jsonify({'results': results}), 200

@test_bp.route('/xss', methods=['POST'])
@xss_protect()
def test_xss():
    """测试XSS防护"""
    data = request.get_json()
    return jsonify({'data': data})

@test_bp.route('/sql', methods=['POST'])
@sql_injection_protect()
def test_sql():
    """测试SQL注入防护"""
    data = request.get_json()
    return jsonify({'data': data}) 