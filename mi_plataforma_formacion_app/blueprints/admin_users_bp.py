from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from mi_plataforma_formacion_app.models.user import User
from mi_plataforma_formacion_app.extensions import db

# Definir el Blueprint antes de usarlo
admin_users_bp = Blueprint('admin_users_bp', __name__, url_prefix='/admin/users')

def admin_required(f):
    from functools import wraps
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Acceso solo para administradores.', 'danger')
            # auth handled by nginx proxy; redirect to main index (nginx will add /app)
            return redirect(url_for('main_bp.index'))
        return f(*args, **kwargs)
    return wraps(f)(decorated_function)

@admin_users_bp.route('/block/<int:user_id>')
@admin_required
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('No puedes bloquear administradores.', 'warning')
    else:
        user.is_active = False
        db.session.commit()
        flash('Usuario bloqueado.', 'success')
    return redirect(url_for('admin_users_bp.list_users'))

@admin_users_bp.route('/unblock/<int:user_id>')
@admin_required
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    flash('Usuario desbloqueado.', 'success')
    return redirect(url_for('admin_users_bp.list_users'))
from mi_plataforma_formacion_app.forms.edit_user_form import EditUserForm
@admin_users_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('Usuario actualizado.', 'success')
        return redirect(url_for('admin_users_bp.list_users'))
    return render_template('edit_user.html', form=form, user=user)

@admin_users_bp.route('/')
@admin_required
def list_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@admin_users_bp.route('/delete/<int:user_id>')
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('No puedes eliminar administradores.', 'warning')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('Usuario eliminado.', 'success')
    return redirect(url_for('admin_users_bp.list_users'))

@admin_users_bp.route('/make_admin/<int:user_id>')
@admin_required
def make_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.role = 'admin'
    db.session.commit()
    flash('Usuario ahora es administrador.', 'success')
    return redirect(url_for('admin_users_bp.list_users'))
