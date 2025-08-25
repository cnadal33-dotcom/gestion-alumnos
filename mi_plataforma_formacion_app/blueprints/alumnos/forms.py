from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, SelectField, TextAreaField, FileField
from flask_wtf.file import FileAllowed, FileRequired
class ImportarAlumnosExcelForm(FlaskForm):
    archivo = FileField('Archivo Excel', validators=[FileRequired(), FileAllowed(['xls', 'xlsx'], 'Solo archivos Excel (.xls, .xlsx)')])
    submit = SubmitField('Importar alumnos')
from wtforms.validators import DataRequired, Email, Optional

class AlumnoForm(FlaskForm):
    nombre = StringField('Nombre completo', validators=[DataRequired()])
    dni = StringField('DNI', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telefono = StringField('Teléfono', validators=[Optional()])
    empresa_id = SelectField('Empresa', coerce=int, validators=[Optional()])
    interesado_mas_cursos = BooleanField('¿Interesado en más cursos?')
    submit = SubmitField('Guardar')
    observaciones = TextAreaField("Observaciones") 