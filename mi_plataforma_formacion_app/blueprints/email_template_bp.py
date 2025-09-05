from flask import Blueprint, render_template, request, redirect, url_for, flash
import importlib.util
import os
from mi_plataforma_formacion_app.forms.email_template_form import EmailTemplateForm

email_template_bp = Blueprint('email_template_bp', __name__, url_prefix='/config_email_template')

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '../email_template.py')

def load_template():
    spec = importlib.util.spec_from_file_location('email_template', TEMPLATE_PATH)
    template = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(template)
    return template

def save_template(form):
    with open(TEMPLATE_PATH, 'w', encoding='utf-8') as f:
        f.write(f"""
EMAIL_SUBJECT = '{form.email_subject.data}'
EMAIL_BODY = '''{form.email_body.data}'''
""")

@email_template_bp.route('/', methods=['GET', 'POST'])
def config_email_template():
    template = load_template()
    form = EmailTemplateForm(
        email_subject=getattr(template, 'EMAIL_SUBJECT', ''),
        email_body=getattr(template, 'EMAIL_BODY', '')
    )
    if form.validate_on_submit():
        save_template(form)
        flash('Plantilla de email guardada correctamente.', 'success')
        return redirect(url_for('email_template_bp.config_email_template'))
    return render_template('config_email_template.html', form=form)
