from flask import Blueprint, render_template, request, jsonify, current_app
from app.models import User, Role, db
from app.utils.auth import admin_required, login_required, current_user
from werkzeug.security import generate_password_hash

bp = Blueprint('admin.users', __name__)

def has_delete_permission(operator, target_user):
    """检查操作者是否有权限删除目标用户"""
    # 超级管理员可以删除任何用户（除了admin自己）
    if operator.is_super_admin:
        return not target_user.username == 'admin'
    
    # 普通管理员只能删除普通用户
    if operator.is_admin and not operator.is_super_admin:
        return not target_user.is_admin and not target_user.is_super_admin
    
    # 普通用户不能删除任何用户
    return False

def has_edit_permission(operator, target_user):
    """检查操作者是否有权限编辑目标用户"""
    # admin用户只能被自己编辑
    if target_user.username == 'admin':
        return operator.username == 'admin'
    
    # 超级管理员可以编辑任何用户
    if operator.is_super_admin:
        return True
    
    # 普通管理员可以编辑普通用户
    if operator.is_admin and not operator.is_super_admin:
        return not target_user.is_admin and not target_user.is_super_admin
    
    # 普通用户不能编辑任何用户
    return False

@bp.route('/')
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.id.asc()).paginate(
        page=page, per_page=10, error_out=False)
    return render_template('admin/users/list.html', 
                         pagination=pagination,
                         current_user=current_user)

@bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(user_id):
    user = User.query.get_or_404(user_id)
    
    # 检查编辑权限
    if not has_edit_permission(current_user, user):
        return jsonify({
            'success': False,
            'message': '您没有权限编辑此用户'
        }), 403

    if request.method == 'POST':
        try:
            # 获取表单数据
            email = request.form.get('email')
            nickname = request.form.get('nickname')
            password = request.form.get('password')
            role_ids = request.form.getlist('roles')
            is_active = request.form.get('is_active') == 'on'

            # 基本验证
            if not email or not nickname:
                raise ValueError('邮箱和昵称不能为空')

            # 更新基本信息
            user.email = email
            user.nickname = nickname

            # 处理密码更新
            if password:
                user.password_hash = generate_password_hash(password)

            # 特殊处理admin用户
            if user.username == 'admin':
                # admin用户必须保持超级管理员角色且只能有这一个角色
                super_admin_role = Role.query.filter_by(name='super_admin').first()
                user.roles = [super_admin_role]
                # admin用户必须保持激活状态
                user.is_active = True
            else:
                # 处理其他用户的角色更新
                if role_ids:
                    # 获取选中的角色
                    roles = Role.query.filter(Role.id.in_(role_ids)).all()
                    # 如果是超级管理员，确保保留super_admin角色
                    if user.is_super_admin:
                        super_admin_role = Role.query.filter_by(name='super_admin').first()
                        if super_admin_role not in roles:
                            roles.append(super_admin_role)
                    # 如果不是超级管理员，确保没有super_admin角色
                    elif not current_user.is_super_admin:
                        roles = [r for r in roles if r.name != 'super_admin']
                    user.roles = roles
                # 更新状态
                if not user.is_super_admin:
                    user.is_active = is_active

            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '保存成功'
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'更新用户失败: {str(e)}')
            return jsonify({
                'success': False,
                'message': '保存失败，请稍后重试'
            }), 500

    # GET请求处理
    # 获取所有角色
    roles = Role.query.order_by(Role.name).all()
    
    # 获取超级管理员角色ID（用于前端验证）
    super_admin_role = Role.query.filter_by(name='super_admin').first()
    super_admin_role_id = super_admin_role.id if super_admin_role else None
    
    # 调试日志
    current_app.logger.debug(f'用户角色: {[role.name for role in user.roles]}')
    current_app.logger.debug(f'可用角色: {[role.name for role in roles]}')
    
    return render_template(
        'admin/user/edit.html',
        user=user,
        roles=roles,
        super_admin_role_id=super_admin_role_id,
        current_user=current_user
    )

@bp.route('/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete(user_id):
    user = User.query.get_or_404(user_id)
    
    # 检查删除权限
    if not has_delete_permission(current_user, user):
        return jsonify({
            'success': False,
            'message': '您没有权限删除此用户'
        }), 403

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除用户失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': '删除失败，请稍后重试'
        }), 500 