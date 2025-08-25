# mi_plataforma_formacion_app/blueprints/alumnos/forms_dni.py
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError

import re

def validar_dni_nie(form, field):
    value = field.data.upper()
    # DNI: 8 dígitos y una letra
    dni_regex = r'^[0-9]{8}[A-Z]$'
    # NIE: empieza por X, Y o Z, seguido de 7 dígitos y una letra
    nie_regex = r'^[XYZ][0-9]{7}[A-Z]$'
    if not (re.match(dni_regex, value) or re.match(nie_regex, value)):
        raise ValidationError('Introduce un DNI o NIE válido (ej: 12345678A o X1234567B)')

class DniForm(FlaskForm):
    dni = StringField('DNI', validators=[DataRequired(), validar_dni_nie])
    submit = SubmitField('Acceder')
