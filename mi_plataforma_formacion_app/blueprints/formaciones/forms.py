from flask_wtf import FlaskForm
from wtforms import SelectField, BooleanField, StringField, TextAreaField, DateField, TimeField, SubmitField
from wtforms.validators import DataRequired, Optional, ValidationError

def not_zero(form, field):
    if field.data == 0:
        raise ValidationError('Selecciona una opción válida.')

class FormacionForm(FlaskForm):
    referencia = StringField('Referencia', validators=[Optional()])
    tipo_curso_id = SelectField('Tipo de curso', coerce=int, validators=[not_zero])
    empresa_id = SelectField('Cliente', coerce=int, validators=[not_zero])
    formador_id = SelectField('Formador', coerce=int, validators=[not_zero])
    dos_ediciones = BooleanField('¿Formación en 2 ediciones?')
    
    fecha1 = DateField('1ª Fecha', validators=[DataRequired()])
    hora_inicio1 = TimeField('Hora inicio 1ª edición', validators=[DataRequired()])
    hora_fin1 = TimeField('Hora fin 1ª edición', validators=[DataRequired()])
    
    fecha2 = DateField('2ª Fecha', validators=[Optional()])
    hora_inicio2 = TimeField('Hora inicio 2ª edición', validators=[Optional()])
    hora_fin2 = TimeField('Hora fin 2ª edición', validators=[Optional()])
    
    direccion_aula = StringField('Dirección del aula', render_kw={"class": "form-control"})
    poblacion = StringField('Población', render_kw={"class": "form-control"})
    fundae = BooleanField('¿Va por FUNDAE?')
    observaciones = TextAreaField('Observaciones', validators=[Optional()])
    
    submit = SubmitField('Guardar')
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed # Importar FileField y FileAllowed
from wtforms import StringField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Optional, Email, Length # Añadir Email y Length para buena práctica

class FormadorForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=128)]) # Añadir Length
    email = StringField('Email', validators=[Optional(), Email(), Length(max=128)]) # Añadir Email y Length
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=32)]) # Añadir Length
    tipos_curso = SelectMultipleField('Tipos de Curso que Imparte', coerce=int, validators=[Optional()])
    firma = FileField('Firma (opcional)', validators=[ # Nuevo campo para la firma
        FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes (JPG, JPEG, PNG)')
    ])
    submit = SubmitField('Guardar')