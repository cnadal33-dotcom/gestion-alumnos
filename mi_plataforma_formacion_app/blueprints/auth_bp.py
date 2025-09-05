from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from mi_plataforma_formacion_app.forms.login_form import LoginForm
from mi_plataforma_formacion_app.forms.register_form import RegisterForm
from mi_plataforma_formacion_app.models.user import User
from mi_plataforma_formacion_app.extensions import db

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if not user.is_active:
                flash('Usuario bloqueado. Contacta con el administrador.', 'danger')
                try:
                    with open('login_attempts.log', 'a', encoding='utf-8') as log:
                        log.write(f"{user.username} intentó acceder estando bloqueado.\n")
                except Exception:
                    pass
            elif user.check_password(form.password.data):
                from flask_login import login_user
                login_user(user)
                flash('Bienvenido, {}!'.format(user.username), 'success')
                return redirect(url_for('main_bp.index'))
            else:
                flash('Usuario o contraseña incorrectos', 'danger')
                try:
                    with open('login_attempts.log', 'a', encoding='utf-8') as log:
                        log.write(f"Intento fallido de login para usuario: {form.username.data}\n")
                except Exception:
                    pass
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
def logout():
    from flask_login import logout_user
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth_bp.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('El usuario ya existe.', 'danger')
        elif User.query.filter_by(email=form.email.data).first():
            flash('El email ya está registrado.', 'danger')
        else:
            user = User(username=form.username.data, email=form.email.data, role='user')
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Usuario registrado correctamente.', 'success')
            return redirect(url_for('auth_bp.login'))
    return render_template('register.html', form=form)
