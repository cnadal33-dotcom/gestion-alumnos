from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class EmailTemplateForm(FlaskForm):
    email_subject = StringField('Asunto del email', validators=[DataRequired()])
    email_body = TextAreaField('Texto del email', validators=[DataRequired()])
    submit = SubmitField('Guardar plantilla')
