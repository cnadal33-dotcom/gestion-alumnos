from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Optional

class ComercialForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    telefono = StringField('Teléfono', validators=[Optional()])
    submit = SubmitField('Guardar')
