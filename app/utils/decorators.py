from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'warning')
            return redirect(url_for('auth.login'))
        return func(*args, **kwargs)
    return decorated_view 