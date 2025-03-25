"""
文件名：site.py
描述：站点设置工具
作者：denny
创建日期：2024-03-25
"""

from flask import current_app
from app.extensions import db

def ensure_default_settings():
    """确保默认站点设置存在"""
    try:
        # 检查是否已有设置表
        from app.models.setting import Setting
        
        default_settings = [
            {
                'key': 'site_name',
                'value': '我的博客系统',
                'description': '站点名称'
            },
            {
                'key': 'site_description',
                'value': '一个简单的博客系统',
                'description': '站点描述'
            },
            {
                'key': 'site_keywords',
                'value': '博客,Python,Flask',
                'description': '站点关键词'
            },
            {
                'key': 'site_url',
                'value': 'http://localhost:5000',
                'description': '站点URL'
            },
            {
                'key': 'admin_email',
                'value': 'admin@example.com',
                'description': '管理员邮箱'
            },
            {
                'key': 'posts_per_page',
                'value': '10',
                'description': '每页文章数'
            },
            {
                'key': 'allow_registration',
                'value': 'true',
                'description': '是否允许注册'
            },
            {
                'key': 'enable_comments',
                'value': 'true',
                'description': '是否启用评论'
            }
        ]
        
        # 遍历默认设置，如果不存在则创建
        for setting in default_settings:
            if not Setting.query.filter_by(key=setting['key']).first():
                new_setting = Setting(
                    key=setting['key'],
                    value=setting['value'],
                    description=setting['description']
                )
                db.session.add(new_setting)
                current_app.logger.info(f'创建默认设置: {setting["key"]} = {setting["value"]}')
        
        # 提交更改
        db.session.commit()
        current_app.logger.info('成功确保默认站点设置存在')
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'确保默认站点设置存在失败: {str(e)}')
        return False

def get_setting(key, default=None):
    """获取站点设置"""
    try:
        from app.models.setting import Setting
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            return setting.value
        return default
    except Exception as e:
        current_app.logger.error(f'获取站点设置失败: {str(e)}')
        return default

def set_setting(key, value, description=None):
    """设置站点设置"""
    try:
        from app.models.setting import Setting
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = Setting(
                key=key,
                value=value,
                description=description or key
            )
            db.session.add(setting)
        db.session.commit()
        current_app.logger.info(f'设置站点设置: {key} = {value}')
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'设置站点设置失败: {str(e)}')
        return False 