from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import Usuario
from app.forms import TrocarSenhaForm
from app.utils import check_rate_limit, reset_failed_attempts, record_failed_attempt, password_strong_enough
from app.extensions import db, csrf
from app.auth.decorators import login_required
import secrets
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        allowed, wait_seconds = check_rate_limit()
        if not allowed:
            flash(f'Tentativas excedidas. Tente novamente em {int(wait_seconds // 60)+1} minutos.', 'error')
            return render_template('login.html')

        username = request.form.get('username', '').strip()
        senha = request.form.get('senha', '')

        if not username or not senha:
            flash('Usuário e senha são obrigatórios.', 'error')
            return render_template('login.html')

        usuario = Usuario.query.filter_by(username=username).first()
        if usuario and usuario.ativo and usuario.check_password(senha):
            reset_failed_attempts()

            token = secrets.token_urlsafe(32)
            usuario.session_token = token
            usuario.ultimo_login = datetime.utcnow()
            db.session.commit()

            session.clear()
            session['user_id'] = usuario.id
            session['session_token'] = token

            flash(f'Bem-vindo, {usuario.nome_completo}!', 'success')

            if usuario.must_reset_password:
                return redirect(url_for('auth.trocar_senha'))

            return redirect(url_for('dashboard.dashboard'))
        else:
            record_failed_attempt()
            flash('Usuário ou senha inválidos.', 'error')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    from app.utils import get_current_user
    usuario = get_current_user()
    nome = usuario.nome_completo if usuario else 'Usuário'
    if usuario:
        usuario.session_token = None
        db.session.commit()
    session.clear()
    flash(f'Até logo, {nome}!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/trocar_senha', methods=['GET', 'POST'])
@login_required
def trocar_senha():
    from app.utils import get_current_user
    usuario = get_current_user()
    if not usuario:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('auth.login'))

    form = TrocarSenhaForm()

    if form.validate_on_submit():
        senha_atual = form.senha_atual.data
        nova_senha = form.nova_senha.data

        if not usuario.check_password(senha_atual):
            flash('Senha atual incorreta.', 'error')
            return render_template('trocar_senha.html', form=form)

        ok, msg = password_strong_enough(nova_senha)
        if not ok:
            flash(msg, 'error')
            return render_template('trocar_senha.html', form=form)

        usuario.set_password(nova_senha)
        usuario.must_reset_password = False
        usuario.session_token = secrets.token_urlsafe(32)
        db.session.commit()

        session['session_token'] = usuario.session_token
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('dashboard.dashboard'))

    return render_template('trocar_senha.html', form=form)