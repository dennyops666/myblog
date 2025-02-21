"""
文件名：errors.py
描述：API错误处理
作者：denny
创建日期：2024-03-21
"""

from flask import jsonify
from . import api_bp
import logging

logger = logging.getLogger('app')

def error_response(status_code, message):
    """通用错误响应"""
    response = jsonify({
        'error': {
            'code': status_code,
            'message': message
        }
    })
    response.status_code = status_code
    return response

@api_bp.app_errorhandler(400)
def bad_request(e):
    """400错误处理"""
    logger.warning(f"400错误: {str(e)}")
    return error_response(400, str(e) or "无效的请求")

@api_bp.app_errorhandler(401)
def unauthorized(e):
    """401错误处理"""
    logger.warning(f"401错误: {str(e)}")
    return error_response(401, str(e) or "未授权访问")

@api_bp.app_errorhandler(403)
def forbidden(e):
    """403错误处理"""
    logger.warning(f"403错误: {str(e)}")
    return error_response(403, str(e) or "禁止访问")

@api_bp.app_errorhandler(404)
def not_found(e):
    """404错误处理"""
    logger.warning(f"404错误: {str(e)}")
    return error_response(404, str(e) or "资源不存在")

@api_bp.app_errorhandler(405)
def method_not_allowed(e):
    """405错误处理"""
    logger.warning(f"405错误: {str(e)}")
    return error_response(405, str(e) or "不允许的请求方法")

@api_bp.app_errorhandler(429)
def too_many_requests(e):
    """429错误处理"""
    logger.warning(f"429错误: {str(e)}")
    return error_response(429, str(e) or "请求过于频繁")

@api_bp.app_errorhandler(500)
def internal_server_error(e):
    """500错误处理"""
    logger.error(f"500错误: {str(e)}")
    return error_response(500, "服务器内部错误")