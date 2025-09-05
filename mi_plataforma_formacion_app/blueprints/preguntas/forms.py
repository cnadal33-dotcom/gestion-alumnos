from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class PreguntaForm(FlaskForm):
    texto = StringField('Pregunta', validators=[DataRequired()])
    submit = SubmitField('Guardar')

class RespuestaForm(FlaskForm):
    texto = StringField('Respuesta', validators=[DataRequired()])
    es_correcta = BooleanField('¿Es correcta?')
    submit = SubmitField('Guardar')
