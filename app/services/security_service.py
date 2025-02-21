def validate_session(session):
    """验证会话是否有效"""
    if not session:
        return False
        
    # 检查会话是否过期
    last_active = session.get('last_active')
    if not last_active or get_current_timestamp() - last_active > SESSION_TIMEOUT:
        return False
        
    # 在测试环境中跳过用户代理验证
    if not current_app.testing:
        # 验证用户代理
        user_agent = session.get('user_agent')
        if not user_agent or user_agent != request.headers.get('User-Agent'):
            current_app.logger.warning('用户代理不匹配')
            return False
            
    return True 