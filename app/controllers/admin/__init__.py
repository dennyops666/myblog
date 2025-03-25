"""
文件名：__init__.py
描述：后台管理模块初始化文件
作者：denny
创建日期：2024-03-21
"""

import logging
import traceback
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify, flash
from flask_login import login_required, current_user
from app.extensions import db

# 导入服务类
from app.services.post import PostService
from app.services.category import CategoryService
from app.services.tag import TagService
from app.services.comment import CommentService
from app.services.user import UserService
from app.services.notification import NotificationService
from app.services.operation_log import operation_log_service
from app.services import get_post_service, get_category_service, get_tag_service, get_comment_service, get_user_service
from app.models.post import PostStatus

# 初始化服务实例
post_service = get_post_service()
category_service = get_category_service()
tag_service = get_tag_service()
comment_service = get_comment_service()
user_service = get_user_service()
notification_service = NotificationService()

# 创建蓝图
admin_bp = Blueprint('admin_dashboard', __name__, template_folder='../../templates')

# 添加调试日志
import logging
current_logger = logging.getLogger('current_app')
current_logger.setLevel(logging.DEBUG)
current_logger.info("===== 调试信息：admin_dashboard蓝图已创建 =====")

# 先导入index模块，确保首页路由先注册
from . import index

# 添加调试日志
current_logger.info("===== 调试信息：admin_dashboard.index已导入 =====")

# 导入各个控制器
from . import category, post, comment, tag, user, settings

# 注册各个控制器
admin_bp.register_blueprint(post.post_bp, url_prefix='/post')
admin_bp.register_blueprint(category.category_bp, url_prefix='/category')
admin_bp.register_blueprint(tag.tag_bp, url_prefix='/tag')
admin_bp.register_blueprint(comment.comment_bp, url_prefix='/comment')
admin_bp.register_blueprint(user.user_bp, url_prefix='/user')
admin_bp.register_blueprint(settings.settings_bp, url_prefix='/settings')

# 初始化上下文处理器
@admin_bp.context_processor
def inject_template_context():
    """注入模板上下文变量"""
    return {
        'current_year': datetime.now().year,
        'now': datetime.now
    }

# 注册请求钩子
@admin_bp.before_request
def before_request():
    """所有管理后台请求的预处理"""
    # 排除登录页面的检查
    if request.endpoint == 'admin_dashboard.login' or \
       request.endpoint == 'admin_dashboard.logout' or \
       request.endpoint == 'admin_dashboard.public_stats' or \
       request.path.startswith('/static/') or \
       '/api/stats' in request.path:
        return None
    
    # 检查用户是否已登录
    if not current_user.is_authenticated:
        # 将以下API请求视为AJAX请求，即使它们没有设置相应的请求头
        is_api_request = (request.is_json or 
                        request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                        request.endpoint == 'admin_dashboard.get_stats' or
                        'get_stats' in request.path)
        
        # AJAX或API请求返回JSON
        if is_api_request:
            return jsonify({
                'success': False,
                'message': '请先登录再访问此页面',
                'redirect': url_for('auth.login')
            }), 401
        
        # 普通请求重定向到登录页面
        return redirect(url_for('auth.login'))
    
    # 检查用户是否有管理员权限
    if not user_service.is_admin(current_user):
        # AJAX请求返回JSON
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': '您没有管理员权限',
                'redirect': url_for('blog.index')
            }), 403
        
        # 普通请求重定向到首页
        return redirect(url_for('blog.index'))

# 全局错误处理器
def handle_error(e, error_code):
    """统一的错误处理函数"""
    # 错误信息和恢复建议
    error_info = {
        400: {
            'message': '请求参数错误',
            'suggestion': '请检查输入的参数是否符合要求'
        },
        401: {
            'message': '未登录或登录已过期',
            'suggestion': '请重新登录后再试'
        },
        403: {
            'message': '没有权限访问该页面',
            'suggestion': '请确保您已经登录并且具有管理员权限'
        },
        404: {
            'message': '请求的页面不存在',
            'suggestion': '请检查URL是否正确，或者返回上一页'
        },
        405: {
            'message': '不支持的请求方法',
            'suggestion': '请检查请求方法是否正确'
        },
        500: {
            'message': '服务器内部错误',
            'suggestion': '请稍后再试，如果问题仍然存在，请联系管理员'
        },
        502: {
            'message': '服务器网关错误',
            'suggestion': '服务器可能正在维护，请稍后再试'
        },
        503: {
            'message': '服务暂时不可用',
            'suggestion': '服务器可能超载，请稍后再试'
        },
        504: {
            'message': '服务器响应超时',
            'suggestion': '请检查网络连接，或者稍后再试'
        }
    }
    
    error_detail = error_info.get(error_code, {
        'message': str(e) or '未知错误',
        'suggestion': '如果问题仍然存在，请联系管理员'
    })
    
    # 记录错误上下文
    error_context = {
        'error': str(e),
        'code': error_code,
        'action': f'handle_{error_code}_error',
        'request_info': {
            'endpoint': request.endpoint,
            'method': request.method,
            'path': request.path,
            'args': dict(request.args),
            'form': dict(request.form) if request.form else None,
            'json': request.get_json(silent=True),
            'user_agent': request.user_agent.string,
            'remote_addr': request.remote_addr
        },
        'user_info': {
            'id': current_user.id if current_user.is_authenticated else None,
            'is_authenticated': current_user.is_authenticated,
            'is_admin': current_user.is_admin if current_user.is_authenticated else False
        },
        'error_info': {
            'type': type(e).__name__,
            'message': error_detail['message'],
            'suggestion': error_detail['suggestion'],
            'original_error': str(e),
            'traceback': traceback.format_exc()
        }
    }
    
    # 根据错误类型选择日志级别和消息
    if error_code >= 500:
        current_app.logger.error(f'服务器错误 ({error_code}): {error_detail["message"]}', extra=error_context)
    elif error_code >= 400:
        current_app.logger.warning(f'客户端错误 ({error_code}): {error_detail["message"]}', extra=error_context)
    else:
        current_app.logger.info(f'其他错误 ({error_code}): {error_detail["message"]}', extra=error_context)
    
    # 准备错误详情
    error_details = None
    if current_app.debug and current_user.is_authenticated and current_user.is_admin:
        error_details = {
            'type': type(e).__name__,
            'message': str(e),
            'traceback': traceback.format_exc(),
            'request_info': error_context['request_info'],
            'user_info': error_context['user_info']
        }
    
    # 根据请求类型返回响应
    if request.is_xhr:
        from app.utils.response import ApiResponse
        return jsonify(ApiResponse.error(
            message=error_detail['message'],
            error_code=error_code,
            error_details=error_details
        )), error_code
    
    return render_template('admin/error.html', 
        error=error_detail['message'],
        suggestion=error_detail['suggestion'],
        error_code=error_code,
        error_details=error_details
    ), error_code

@admin_bp.errorhandler(403)
def forbidden(e):
    return handle_error(e, 403)

@admin_bp.errorhandler(404)
def page_not_found(e):
    return handle_error(e, 404)

@admin_bp.errorhandler(500)
def internal_server_error(e):
    return handle_error(e, 500)

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """个人资料页面"""
    try:
        if request.method == 'POST':
            # 获取表单数据 - 支持JSON和表单提交两种方式
            if request.is_json:
                data = request.get_json()
                email = data.get('email')
                password = data.get('password')
                confirm_password = data.get('confirm_password')
            else:
                email = request.form.get('email')
                password = request.form.get('password')
                confirm_password = request.form.get('confirm_password')
            
            # 验证邮箱
            if not email:
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'message': '邮箱不能为空'
                    })
                else:
                    flash('邮箱不能为空', 'danger')
                    return render_template('admin/profile.html',
                        user=current_user,
                        title='个人资料'
                    )
            
            try:
                # 更新邮箱
                current_user.email = email
                
                # 如果提供了新密码，则更新密码
                if password:
                    if password != confirm_password:
                        if request.is_json:
                            return jsonify({
                                'success': False,
                                'message': '两次输入的密码不一致'
                            })
                        else:
                            flash('两次输入的密码不一致', 'danger')
                            return render_template('admin/profile.html',
                                user=current_user,
                                title='个人资料'
                            )
                        
                    current_user.set_password(password)
                
                # 保存更改
                db.session.commit()
                
                # 记录日志
                current_app.logger.info('用户更新个人资料成功', extra={
                    'user_id': current_user.id,
                    'email': email
                })
                
                # 根据请求类型返回不同响应
                if request.is_json:
                    return jsonify({
                        'success': True,
                        'message': '个人资料更新成功'
                    })
                else:
                    flash('个人资料更新成功', 'success')
                    return redirect(url_for('admin_dashboard.profile'))
                
            except Exception as e:
                # 回滚事务
                db.session.rollback()
                
                # 记录错误日志
                current_app.logger.error(f'更新个人资料失败: {str(e)}')
                
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'message': '更新个人资料失败，请稍后再试'
                    })
                else:
                    flash('更新个人资料失败，请稍后再试', 'danger')
                    return render_template('admin/profile.html',
                        user=current_user,
                        title='个人资料'
                    )
            
        return render_template('admin/profile.html',
            user=current_user,
            title='个人资料'
        )
        
    except Exception as e:
        # 记录错误日志
        current_app.logger.error(f'访问个人资料页面失败: {str(e)}')
        
        # 对于GET请求返回错误页面，对于POST请求返回对应格式的响应
        if request.method == 'POST':
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': '访问个人资料页面失败，请稍后再试'
                })
            else:
                flash('访问个人资料页面失败，请稍后再试', 'danger')
                return redirect(url_for('admin_dashboard.dashboard'))

# 登录页面路由
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理后台登录页"""
    # 如果用户已登录，则重定向到管理后台首页
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard.dashboard'))
    
    # 处理POST请求（AJAX登录）
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        remember_me = data.get('remember_me', False)
        
        user = user_service.get_user_by_username(username)
        if user is None or not user_service.check_password(user, password):
            return jsonify({
                'status': 'error',
                'message': '用户名或密码错误'
            })
        
        # 验证用户是否有管理员权限
        if not user_service.is_admin(user):
            return jsonify({
                'status': 'error',
                'message': '您没有管理员权限'
            })
        
        # 执行登录
        from flask_login import login_user
        login_user(user, remember=remember_me)
        
        # 获取next参数，确保安全重定向
        next_url = request.args.get('next')
        if next_url and 'admin' in next_url:
            return jsonify({
                'status': 'success',
                'message': '登录成功',
                'redirect': next_url
            })
        
        # 默认重定向到管理后台首页
        return jsonify({
            'status': 'success',
            'message': '登录成功',
            'redirect': url_for('admin_dashboard.dashboard')
        })
    
    # 处理GET请求
    return render_template('admin/login.html')

# 添加API端点，获取最新统计数据和文章列表
@admin_bp.route('/get_stats')
@login_required
def get_stats():
    """获取最新统计数据和文章列表（需要登录）"""
    return _get_stats_data()

# 增加一个公开API端点
@admin_bp.route('/api/stats', methods=['GET'])
def public_stats():
    """获取最新统计数据和文章列表（公开API）"""
    # 记录请求信息
    current_app.logger.info(f"公开API stats被访问: {request.path}")
    return _get_stats_data()

def _get_stats_data():
    """共用的获取统计数据和文章列表的函数"""
    try:
        current_app.logger.info("开始获取管理后台统计数据...")
        from app.models.post import Post, PostStatus
        from app.models.category import Category
        from app.models.tag import Tag
        from sqlalchemy import func, desc
        import traceback
        
        try:
            # 使用显式导入的PostStatus枚举
            post_count = Post.query.count()
            # 直接查询字符串状态值，而不是使用枚举对象
            published_count = Post.query.filter_by(status=PostStatus.PUBLISHED).count()
            draft_count = Post.query.filter_by(status=PostStatus.DRAFT).count()
            
            category_count = Category.query.count()
            tag_count = Tag.query.count()
            
            # 打印SQL日志
            current_app.logger.info(f"统计查询结果: 文章总数={post_count}, 已发布={published_count}, 草稿={draft_count}")
            current_app.logger.info(f"分类数={category_count}, 标签数={tag_count}")
        except Exception as e:
            current_app.logger.error(f"统计数据查询失败: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            post_count = published_count = draft_count = category_count = tag_count = 0
        
        # 获取最近文章
        posts_data = []
        try:
            # 直接使用字符串状态值列表
            status_list = [PostStatus.PUBLISHED.value, PostStatus.DRAFT.value]
            current_app.logger.info(f"查询状态列表: {status_list}")
            
            # 使用SQL日志记录查询
            current_app.logger.info("执行最近文章查询")
            recent_posts = Post.query.order_by(desc(Post.created_at)).limit(5).all()
            
            current_app.logger.info(f"查询到 {len(recent_posts)} 篇最近文章")
            
            # 格式化文章数据
            for post in recent_posts:
                try:
                    # 直接使用Post对象属性
                    status_value = post.status.value if hasattr(post.status, 'value') else str(post.status)
                    
                    post_data = {
                        'id': post.id,
                        'title': post.title,
                        'status': status_value,
                        'created_at': post.created_at.strftime('%Y-%m-%d %H:%M') if post.created_at else '',
                        'view_count': post.view_count or 0
                    }
                    posts_data.append(post_data)
                    current_app.logger.info(f"处理文章: ID={post.id}, 标题={post.title}, 状态={status_value}")
                except Exception as post_error:
                    current_app.logger.error(f"处理文章数据失败: {str(post_error)}")
                    current_app.logger.error(traceback.format_exc())
                    continue
        except Exception as e:
            current_app.logger.error(f"获取最近文章失败: {str(e)}")
            current_app.logger.error(traceback.format_exc())
        
        # 记录最终结果
        current_app.logger.info(f"API返回: 文章={post_count}, 分类={category_count}, 标签={tag_count}, 最近文章数={len(posts_data)}")
        
        # 返回JSON数据
        result = {
            'post_count': post_count,
            'category_count': category_count,
            'published_count': published_count,
            'draft_count': draft_count,
            'tag_count': tag_count,
            'recent_posts': posts_data
        }
        current_app.logger.info(f"统计数据API请求成功处理完成: {result}")
        return jsonify(result)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        current_app.logger.error(f"获取统计数据失败: {str(e)}")
        current_app.logger.error(f"错误详情: {error_trace}")
        
        return jsonify({
            'post_count': 0,
            'category_count': 0, 
            'published_count': 0,
            'draft_count': 0,
            'tag_count': 0,
            'recent_posts': []
        })

# 导入其他模块
from . import operation_log, upload, test



