# Decorador para acceso solo de administradores
def admin_required(f):
    from functools import wraps
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Acceso solo para administradores.', 'danger')
            # redirect to main index; nginx will rewrite to /app/
            return redirect(url_for('main_bp.index'))
        return f(*args, **kwargs)
    return wraps(f)(decorated_function)
from flask import Blueprint, render_template, session, flash, redirect, url_for
import os

login_attempts_bp = Blueprint('login_attempts_bp', __name__, url_prefix='/admin/login_attempts')

@login_attempts_bp.route('/clear', methods=['POST'])
@admin_required
def clear_attempts():
    log_path = os.path.join(os.path.dirname(__file__), '../../login_attempts.log')
    if os.path.exists(log_path):
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write('')
            flash('Registro de intentos limpiado.', 'success')
        except Exception:
            flash('No se pudo limpiar el registro.', 'danger')
    else:
        flash('No hay registro para limpiar.', 'info')
    return redirect(url_for('login_attempts_bp.view_attempts'))
def admin_required(f):
    from functools import wraps
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Acceso solo para administradores.', 'danger')
            # redirect to main index; nginx will rewrite to /app/
            return redirect(url_for('main_bp.index'))
        return f(*args, **kwargs)
    return wraps(f)(decorated_function)

@login_attempts_bp.route('/')
@admin_required
def view_attempts():
    log_path = os.path.join(os.path.dirname(__file__), '../../login_attempts.log')
    attempts = []
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            attempts = f.readlines()
    return render_template('login_attempts.html', attempts=attempts)
