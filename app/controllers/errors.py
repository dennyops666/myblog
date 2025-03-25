"""
错误处理器模块
"""

from flask import jsonify, render_template, request

def register_error_handlers(app):
    """注册错误处理器"""

    @app.errorhandler(400)
    def bad_request(e):
        """处理400错误"""
        if request.is_json:
            return jsonify({
                'code': 400,
                'message': '请求参数错误',
                'data': None
            }), 400
        return render_template('errors/400.html'), 400

    @app.errorhandler(401)
    def unauthorized(e):
        """处理401错误"""
        if request.is_json:
            return jsonify({
                'code': 401,
                'message': '未授权访问',
                'data': None
            }), 401
        return render_template('errors/401.html'), 401

    @app.errorhandler(403)
    def forbidden(e):
        """处理403错误"""
        if request.is_json:
            return jsonify({
                'code': 403,
                'message': '禁止访问',
                'data': None
            }), 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        """处理404错误"""
        if request.is_json:
            return jsonify({
                'code': 404,
                'message': '页面不存在',
                'data': None
            }), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        """处理500错误"""
        if request.is_json:
            return jsonify({
                'code': 500,
                'message': '服务器内部错误',
                'data': None
            }), 500
        return render_template('errors/500.html'), 500

    return app 