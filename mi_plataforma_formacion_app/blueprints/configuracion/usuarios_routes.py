from flask import Blueprint, render_template, redirect, url_for, request, flash
from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.user import User
from werkzeug.security import generate_password_hash
from flask_login import login_required

usuarios_bp = Blueprint('usuarios_bp', __name__, url_prefix='/configuracion/usuarios')

@usuarios_bp.route('/')
@login_required
def lista_usuarios():
    usuarios = User.query.all()
    return render_template('configuracion/usuarios/lista.html', usuarios=usuarios)

@usuarios_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_usuario():
    from mi_plataforma_formacion_app.models.permission import Permission
    permisos = Permission.query.all()
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')
        if User.query.filter_by(username=username).first():
            flash('El usuario ya existe', 'danger')
            return redirect(url_for('usuarios_bp.nuevo_usuario'))
        user = User(username=username, email=email, role=role)
        user.set_password(password)
    # No se asignan permisos, solo datos básicos y rol
        db.session.add(user)
        db.session.commit()
        flash('Usuario creado correctamente', 'success')
        return redirect(url_for('usuarios_bp.lista_usuarios'))
    return render_template('configuracion/usuarios/nuevo.html')

@usuarios_bp.route('/editar/<int:user_id>', methods=['GET', 'POST'])
def editar_usuario(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.role = request.form.get('role', user.role)
        if request.form['password']:
            user.set_password(request.form['password'])
        db.session.commit()
        flash('Usuario actualizado', 'success')
        return redirect(url_for('usuarios_bp.lista_usuarios'))
    return render_template('configuracion/usuarios/editar.html', user=user)

@usuarios_bp.route('/eliminar/<int:user_id>', methods=['POST'])
def eliminar_usuario(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado', 'success')
    return redirect(url_for('usuarios_bp.lista_usuarios'))
