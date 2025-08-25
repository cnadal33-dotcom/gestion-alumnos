# mi_plataforma_formacion_app/blueprints/alumnos/forms_codigo.py
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class CodigoFormacionForm(FlaskForm):
    codigo = StringField('Código de formación', validators=[DataRequired()])
    submit = SubmitField('Acceder')
