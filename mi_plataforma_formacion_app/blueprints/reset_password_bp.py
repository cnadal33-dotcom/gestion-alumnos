from flask import Blueprint, render_template, redirect, url_for, flash, request
from mi_plataforma_formacion_app.forms.reset_password_form import ResetPasswordForm
from mi_plataforma_formacion_app.models.user import User
from mi_plataforma_formacion_app.extensions import db

reset_password_bp = Blueprint('reset_password_bp', __name__, url_prefix='/reset_password')

@reset_password_bp.route('/', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash('No existe usuario con ese email.', 'danger')
        else:
            user.set_password(form.password.data)
            db.session.commit()
            flash('Contraseña restablecida correctamente.', 'success')
            # auth_bp may be unregistered (nginx handles auth) -> send to main index
            # Use url_for() so Flask emits a root-relative URL; nginx will rewrite
            # Location headers to include the /app prefix via proxy_redirect.
            return redirect(url_for('main_bp.index'))
    return render_template('reset_password.html', form=form)
