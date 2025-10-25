from functools import wraps
from flask import session, flash, redirect, url_for
from app.models import Usuario

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'session_token' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        usuario = Usuario.query.get(session.get('user_id'))
        if not usuario or usuario.session_token != session.get('session_token') or not usuario.ativo:
            session.clear()
            flash('Sessão inválida. Faça login novamente.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'session_token' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        usuario = Usuario.query.get(session.get('user_id'))
        if not usuario or usuario.session_token != session.get('session_token') or not usuario.is_admin():
            flash('Acesso negado. Esta área é restrita para administradores.', 'error')
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function