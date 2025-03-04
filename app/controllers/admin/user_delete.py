from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.decorators import admin_required
from app import db

bp = Blueprint('user_delete', __name__)

@bp.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        # 检查是否为超级管理员
        if user.is_super_admin:
            return jsonify({
                'success': False,
                'message': '超级管理员用户不能被删除'
            })
            
        # 检查是否为当前用户
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'message': '不能删除当前登录用户'
            })
            
        # 删除用户
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'用户 {user.username} 已成功删除'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除用户失败：{str(e)}'
        })
