from flask import Blueprint, render_template, request, redirect, url_for, flash
import importlib.util
import os
from mi_plataforma_formacion_app.forms.email_config_form import EmailConfigForm

email_config_bp = Blueprint('email_config_bp', __name__, url_prefix='/config_email')

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config_email.py')

# Utilidad para cargar config actual
def load_config():
    spec = importlib.util.spec_from_file_location('config_email', CONFIG_PATH)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config

# Utilidad para guardar config
def save_config(form):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        f.write(f"""
SMTP_SERVER = '{form.smtp_server.data}'
SMTP_PORT = {form.smtp_port.data}
SMTP_USE_TLS = {form.smtp_use_tls.data}
SMTP_USE_SSL = {form.smtp_use_ssl.data}
SMTP_USERNAME = '{form.smtp_username.data}'
SMTP_PASSWORD = '{form.smtp_password.data}'
EMAIL_FROM = '{form.email_from.data}'
EMAIL_REPLY_TO = '{form.email_reply_to.data}'
EMAIL_ADMIN = '{form.email_admin.data}'
""")

@email_config_bp.route('/', methods=['GET', 'POST'])
def config_email():
    config = load_config()
    form = EmailConfigForm(
        smtp_server=getattr(config, 'SMTP_SERVER', ''),
        smtp_port=getattr(config, 'SMTP_PORT', 587),
        smtp_use_tls=getattr(config, 'SMTP_USE_TLS', True),
        smtp_use_ssl=getattr(config, 'SMTP_USE_SSL', False),
        smtp_username=getattr(config, 'SMTP_USERNAME', ''),
        smtp_password=getattr(config, 'SMTP_PASSWORD', ''),
        email_from=getattr(config, 'EMAIL_FROM', ''),
        email_reply_to=getattr(config, 'EMAIL_REPLY_TO', ''),
        email_admin=getattr(config, 'EMAIL_ADMIN', '')
    )
    if form.validate_on_submit():
        save_config(form)
        flash('Configuración de email guardada correctamente.', 'success')
        return redirect(url_for('email_config_bp.config_email'))
    return render_template('config_email.html', form=form)
