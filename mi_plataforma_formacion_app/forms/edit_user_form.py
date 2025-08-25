from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Optional

class EditUserForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Nueva contraseña', validators=[Optional()])
    role = SelectField('Rol', choices=[('user', 'Usuario'), ('admin', 'Administrador')], validators=[DataRequired()])
    submit = SubmitField('Guardar cambios')
