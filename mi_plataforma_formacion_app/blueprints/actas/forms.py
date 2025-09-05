from flask_wtf import FlaskForm
from wtforms import StringField, FileField
from wtforms.validators import DataRequired


class PlantillaActaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    archivo = FileField('Plantilla PDF autorrellenable')
