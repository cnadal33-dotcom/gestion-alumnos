from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional  # ← añade Optional

from flask_wtf.file import FileField, FileAllowed

class PlantillaActaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()], render_kw={"class": "form-control"})
    # html = TextAreaField('Código HTML', validators=[Optional()], render_kw={"class": "form-control", "rows": 14, "style": "font-family: monospace; font-size:1em;"})  # Eliminado
    archivo_pdf = FileField('Plantilla PDF', validators=[Optional(), FileAllowed(['pdf'], 'Solo se permiten archivos PDF')], render_kw={"class": "form-control"})
    submit = SubmitField('Guardar', render_kw={"class": "btn btn-primary"})
