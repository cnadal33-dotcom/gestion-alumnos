from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Optional

class EmailConfigForm(FlaskForm):
    smtp_server = StringField('Servidor SMTP', validators=[DataRequired()])
    smtp_port = IntegerField('Puerto SMTP', validators=[DataRequired()])
    smtp_use_tls = BooleanField('Usar TLS (STARTTLS, puerto 587)')
    smtp_use_ssl = BooleanField('Usar SSL/TLS (puerto 465)')
    smtp_username = StringField('Usuario', validators=[DataRequired(), Email()])
    smtp_password = PasswordField('Contraseña', validators=[Optional()])
    email_from = StringField('Correo remitente', validators=[DataRequired(), Email()])
    email_reply_to = StringField('Correo de respuesta', validators=[Optional(), Email()])
    email_admin = StringField('Correo administrador', validators=[Optional(), Email()])
    submit = SubmitField('Guardar configuración')
