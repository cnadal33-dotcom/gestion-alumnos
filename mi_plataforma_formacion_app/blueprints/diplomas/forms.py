from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed

class PlantillaDiplomaForm(FlaskForm):
    nombre = StringField('Nombre de la plantilla', validators=[DataRequired()])
    archivo = FileField('Plantilla PDF autorrellenable', validators=[FileAllowed(['pdf'], 'Solo PDF')])
    submit = SubmitField('Guardar')
