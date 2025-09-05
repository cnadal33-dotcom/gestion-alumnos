from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Optional
from flask_wtf.file import FileField, FileAllowed

class FormadorForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional()])
    telefono = StringField('Teléfono', validators=[Optional()])
    tipos_curso = SelectMultipleField('Tipos de Curso', coerce=int, validators=[Optional()])
    firma = FileField('Firma (PNG o JPG)', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Solo imágenes')])
    submit = SubmitField('Guardar')
