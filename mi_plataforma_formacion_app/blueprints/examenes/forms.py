from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class ExamenModeloForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción')
    submit = SubmitField('Guardar')

class PreguntaForm(FlaskForm):
    texto = StringField('Texto de la pregunta', validators=[DataRequired()])
    submit = SubmitField('Guardar')

class RespuestaForm(FlaskForm):
    texto = StringField('Texto de la respuesta', validators=[DataRequired()])
    es_correcta = BooleanField('Es la correcta')
    submit = SubmitField('Guardar')
