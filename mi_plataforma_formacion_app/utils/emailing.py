from flask_mail import Message
from mi_plataforma_formacion_app.extensions import mail
from flask import current_app

def enviar_diploma_por_email(alumno, ruta_pdf):
    """
    Envía el diploma generado por email al alumno.
    """
    try:
        import importlib.util, os
        from flask_mail import Mail, Message
        from flask import current_app
        # Cargar configuración dinámica
        config_path = os.path.join(os.path.dirname(__file__), '../config_email.py')
        spec = importlib.util.spec_from_file_location('config_email', config_path)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)

        # Configurar Flask-Mail dinámicamente
        mail_settings = {
            'MAIL_SERVER': getattr(config, 'SMTP_SERVER', ''),
            'MAIL_PORT': getattr(config, 'SMTP_PORT', 587),
            'MAIL_USE_TLS': getattr(config, 'SMTP_USE_TLS', True),
            'MAIL_USE_SSL': getattr(config, 'SMTP_USE_SSL', False),
            'MAIL_USERNAME': getattr(config, 'SMTP_USERNAME', ''),
            'MAIL_PASSWORD': getattr(config, 'SMTP_PASSWORD', ''),
            'MAIL_DEFAULT_SENDER': getattr(config, 'EMAIL_FROM', ''),
            'MAIL_REPLY_TO': getattr(config, 'EMAIL_REPLY_TO', ''),
        }
        for k, v in mail_settings.items():
            current_app.config[k] = v
        mail = Mail(current_app)

        # Importar plantilla configurable
        template_path = os.path.join(os.path.dirname(__file__), '../email_template.py')
        spec = importlib.util.spec_from_file_location('email_template', template_path)
        template = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(template)
        asunto = getattr(template, 'EMAIL_SUBJECT', 'Tu diploma de formación')
        cuerpo = getattr(template, 'EMAIL_BODY', 'Adjuntamos tu diploma en PDF.')

        # Variables disponibles
        variables = {
            'nombre_alumno': getattr(alumno, 'nombre', ''),
            'dni_alumno': getattr(alumno, 'dni', ''),
            'curso': getattr(getattr(alumno, 'formacion', None), 'tipo_curso', None) and getattr(alumno.formacion.tipo_curso, 'nombre', '') or '',
            'fecha': getattr(getattr(alumno, 'formacion', None), 'fecha1', None) and alumno.formacion.fecha1.strftime('%d/%m/%Y') or '',
            'empresa': getattr(getattr(alumno, 'formacion', None), 'empresa', None) and getattr(alumno.formacion.empresa, 'nombre', '') or '',
            'formador': getattr(getattr(alumno, 'formacion', None), 'formador', None) and getattr(alumno.formacion.formador, 'nombre', '') or '',
        }
        # Sustituir variables en asunto y cuerpo
        asunto = asunto.format(**variables)
        cuerpo = cuerpo.format(**variables)

        msg = Message(
            subject=asunto,
            recipients=[alumno.email],
            body=cuerpo,
            reply_to=mail_settings['MAIL_REPLY_TO']
        )
        with open(ruta_pdf, "rb") as fp:
            msg.attach("diploma.pdf", "application/pdf", fp.read())
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Error enviando email a {alumno.email}: {str(e)}")
        return False
