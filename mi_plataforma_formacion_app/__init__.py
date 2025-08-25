from flask import Flask
from mi_plataforma_formacion_app.extensions import db
from flask_migrate import Migrate

# Inicializa Migrate
migrate = Migrate()

def create_app():
    # ...extensiones y configuración...
    app = Flask(__name__)

    # Context processor para usuario actual (solo autenticación)
    @app.context_processor
    def inject_user_authenticated():
        from flask_login import current_user
        return dict(current_user_authenticated=current_user.is_authenticated)

    from mi_plataforma_formacion_app.blueprints.configuracion.usuarios_routes import usuarios_bp
    app.register_blueprint(usuarios_bp)
    from mi_plataforma_formacion_app.blueprints.configuracion.permisos_routes import permisos_bp
    app.register_blueprint(permisos_bp)
    from mi_plataforma_formacion_app.blueprints.login_attempts_bp import login_attempts_bp
    app.register_blueprint(login_attempts_bp)
    from mi_plataforma_formacion_app.blueprints.reset_password_bp import reset_password_bp
    app.register_blueprint(reset_password_bp)
    from mi_plataforma_formacion_app.blueprints.admin_users_bp import admin_users_bp
    app.register_blueprint(admin_users_bp)
    from mi_plataforma_formacion_app.blueprints.auth_bp import auth_bp
    app.register_blueprint(auth_bp)

    # 🔴 NECESARIO PARA FORMULARIOS WTForms/Flask-WTF
    app.config['SECRET_KEY'] = 'unaclaveultrasecretasupersegura2025'  # Cambia por otra si quieres

    # Configuración de base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///formacion.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 🔴 NECESARIO PARA GENERAR PDF CON WKHTMLTOPDF
    app.config['WKHTMLTOPDF_PATH'] = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    # (Si tu wkhtmltopdf está en otra ruta, ajústalo aquí)

    # Inicializa extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    from mi_plataforma_formacion_app.extensions import login_manager
    from mi_plataforma_formacion_app.models.user import User
    login_manager.init_app(app)
    login_manager.login_view = 'auth_bp.login'
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints de entidades principales
    from mi_plataforma_formacion_app.blueprints.empresas.routes import empresas_bp
    app.register_blueprint(empresas_bp, url_prefix='/empresas')

    from mi_plataforma_formacion_app.blueprints.alumnos.routes import alumnos_bp
    app.register_blueprint(alumnos_bp, url_prefix='/alumnos')

    from mi_plataforma_formacion_app.blueprints.comerciales.routes import comerciales_bp
    app.register_blueprint(comerciales_bp, url_prefix='/comerciales')

    from mi_plataforma_formacion_app.blueprints.tipo_curso.routes import tipo_curso_bp
    app.register_blueprint(tipo_curso_bp, url_prefix='/tipo_curso')

    from mi_plataforma_formacion_app.blueprints.formadores.routes import formadores_bp
    app.register_blueprint(formadores_bp, url_prefix='/formadores')

    from mi_plataforma_formacion_app.blueprints.formaciones.routes import formaciones_bp
    app.register_blueprint(formaciones_bp, url_prefix='/formaciones')

    from mi_plataforma_formacion_app.blueprints.diplomas.routes import diplomas_bp
    app.register_blueprint(diplomas_bp, url_prefix='/diplomas')

    from mi_plataforma_formacion_app.blueprints.preguntas.routes import preguntas_bp
    app.register_blueprint(preguntas_bp, url_prefix='/preguntas')

    # Blueprint de EXÁMENES (el que necesitabas)
    from mi_plataforma_formacion_app.blueprints.examenes.routes import examenes_bp
    app.register_blueprint(examenes_bp, url_prefix='/examenes')

    # Blueprint página principal (home)
    from mi_plataforma_formacion_app.blueprints.main_bp import main_bp
    app.register_blueprint(main_bp)  # Sin prefix, será la raíz "/"

    # Blueprint API
    from mi_plataforma_formacion_app.blueprints.api_bp import api_bp
    app.register_blueprint(api_bp)

    # Blueprint Panel Admin
    from mi_plataforma_formacion_app.blueprints.admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from mi_plataforma_formacion_app.blueprints.renovaciones.routes import renovaciones_bp
    app.register_blueprint(renovaciones_bp)

    from mi_plataforma_formacion_app.blueprints.caducidades.routes import caducidades_bp
    app.register_blueprint(caducidades_bp)

    from mi_plataforma_formacion_app.blueprints.plantillas_acta.routes import plantillas_acta_bp
    app.register_blueprint(plantillas_acta_bp)


    from mi_plataforma_formacion_app.blueprints.config_email_bp import email_config_bp
    app.register_blueprint(email_config_bp)
    from mi_plataforma_formacion_app.blueprints.email_template_bp import email_template_bp
    app.register_blueprint(email_template_bp)
    return app
