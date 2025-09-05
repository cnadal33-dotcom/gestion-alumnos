from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Optional

class EmpresaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    cif = StringField('CIF', validators=[DataRequired()])
    direccion = StringField('Dirección', validators=[Optional()])
    poblacion = StringField('Población', validators=[Optional()])
    ciudad = StringField('Ciudad', validators=[Optional()])
    contacto = StringField('Persona de contacto', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email()])
    telefono = StringField('Teléfono', validators=[Optional()])
    comercial_id = SelectField('Comercial', coerce=int, validators=[Optional()])
    submit = SubmitField('Guardar')
