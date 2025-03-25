from flask import Blueprint, request
from flask_login import login_required, current_user
from sqlalchemy import and_

from app.extensions import db
from app.services.notification import NotificationService
from app.models.notification import Notification
from app.utils.response import ApiResponse

notification_bp = Blueprint('notification', __name__)
notification_service = NotificationService()

@notification_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    search = request.args.get('search')
    limit = request.args.get('limit', type=int)
    include_read = request.args.get('include_read', type=bool, default=True)
    
    notifications = notification_service.get_notifications(
        user_id=current_user.id,
        search=search,
        limit=limit,
        include_read=include_read
    )
    
    return ApiResponse.success({
        'notifications': [n.to_dict() for n in notifications]
    })

@notification_bp.route('/notifications/unread/count', methods=['GET'])
@login_required
def get_unread_count():
    count = notification_service.get_unread_count(current_user.id)
    return ApiResponse.success({'count': count})

@notification_bp.route('/notifications/<int:notification_id>', methods=['GET'])
@login_required
def get_notification(notification_id):
    notification = notification_service.get_notification_by_id(notification_id)
    
    if not notification:
        return ApiResponse.error('通知不存在', 404)
        
    if notification.user_id != current_user.id:
        return ApiResponse.error('无权访问该通知', 403)
        
    return ApiResponse.success({
        'notification': notification.to_dict()
    })

@notification_bp.route('/notifications/recent', methods=['GET'])
@login_required
def get_recent_notifications():
    limit = request.args.get('limit', type=int, default=5)
    notifications = notification_service.get_notifications(
        user_id=current_user.id,
        limit=limit,
        include_read=True
    )
    
    return ApiResponse.success({
        'notifications': [n.to_dict() for n in notifications]
    })

@notification_bp.route('/notifications/system', methods=['POST'])
@login_required
def create_system_notification():
    content = request.json.get('content')
    if not content:
        return ApiResponse.error('通知内容不能为空', 400)
    
    notification = notification_service.notify_system(
        user_id=current_user.id,
        content=content
    )
    
    if not notification:
        return ApiResponse.error('创建通知失败', 500)
    
    return ApiResponse.success({
        'notification': notification.to_dict()
    })

@notification_bp.route('/notifications/search', methods=['GET'])
@login_required
def search_notifications():
    query = request.args.get('q')
    if not query:
        return ApiResponse.error('搜索关键词不能为空', 400)
    
    notifications = notification_service.get_notifications(
        user_id=current_user.id,
        search=query
    )
    
    return ApiResponse.success({
        'notifications': [n.to_dict() for n in notifications]
    })

@notification_bp.route('/notifications/types', methods=['GET'])
@login_required
def get_notification_types():
    from app.models.notification import NOTIFICATION_TYPES
    return ApiResponse.success({
        'types': NOTIFICATION_TYPES
    })

@notification_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    notification_ids = request.json.get('notification_ids', [])
    if not notification_ids:
        return ApiResponse.error('请选择要标记的通知', 400)
    
    # 只更新属于当前用户的通知
    notifications = Notification.query.filter(
        and_(
            Notification.id.in_(notification_ids),
            Notification.user_id == current_user.id,
            Notification.read == False
        )
    ).all()
    
    if not notifications:
        return ApiResponse.error('没有可标记的通知', 404)
    
    for notification in notifications:
        notification.read = True
    
    db.session.commit()
    
    return ApiResponse.success({
        'marked_count': len(notifications)
    })

@notification_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    # 更新所有未读通知
    result = Notification.query.filter_by(
        user_id=current_user.id,
        read=False
    ).update({'read': True})
    
    db.session.commit()
    
    return ApiResponse.success({
        'marked_count': result
    })

@notification_bp.route('/notifications/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    notification = notification_service.get_notification_by_id(notification_id)
    
    if not notification:
        return ApiResponse.error('通知不存在', 404)
        
    if notification.user_id != current_user.id:
        return ApiResponse.error('无权删除该通知', 403)
    
    db.session.delete(notification)
    db.session.commit()
    
    return ApiResponse.success()

@notification_bp.route('/notifications/clear', methods=['DELETE'])
@login_required
def clear_notifications():
    # 删除所有已读通知
    result = Notification.query.filter_by(
        user_id=current_user.id,
        read=True
    ).delete()
    
    db.session.commit()
    
    return ApiResponse.success({
        'deleted_count': result
    })
