from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

class GenerarActaForm(FlaskForm):
    formacion_id = SelectField('Formación', coerce=int, validators=[DataRequired()])
    formador_id = SelectField('Formador', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Generar Acta')
