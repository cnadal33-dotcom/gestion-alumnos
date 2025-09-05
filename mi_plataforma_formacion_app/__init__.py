import os
from flask import Flask
from mi_plataforma_formacion_app.extensions import db
from flask_migrate import Migrate

# Inicializa Migrate
migrate = Migrate()

def create_app():
    # ...extensiones y configuración...
    # Ensure Flask serves the top-level project's `static/` directory
    # (by default Flask will look for a `static` folder inside the package,
    # which in this project is not where the repo-level static assets live).
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    static_dir = os.path.join(project_root, 'static')
    app = Flask(__name__, static_folder=static_dir)

    # Context processor para usuario actual (solo autenticación)
    @app.context_processor
    def inject_user_authenticated():
        from flask_login import current_user
        # current_user may be a proxy that is None outside of request; be defensive
        try:
            return dict(current_user_authenticated=getattr(current_user, 'is_authenticated', False))
        except Exception:
            return dict(current_user_authenticated=False)

    # Blueprints de configuración y autenticación eliminados porque el usuario
    # solicitó quitar la funcionalidad que estaba causando errores.

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
    # auth_bp was intentionally removed; send unauthenticated users to the main index
    # (nginx provides basic auth at /app/ so Flask login view is not required).
    login_manager.login_view = 'main_bp.index'
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

    # Actas (plantillas de actas) - similar UX to Diplomas
    from mi_plataforma_formacion_app.blueprints.actas.routes import actas_bp
    app.register_blueprint(actas_bp, url_prefix='/actas')

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

    # Nota: el blueprint `plantillas_acta_bp` contenía rutas/plantillas heredadas
    # que entraban en conflicto con la nueva implementación `actas_bp`.
    # Se omite su registro para evitar duplicidades.


    from mi_plataforma_formacion_app.blueprints.config_email_bp import email_config_bp
    app.register_blueprint(email_config_bp)
    from mi_plataforma_formacion_app.blueprints.email_template_bp import email_template_bp
    app.register_blueprint(email_template_bp)
    # Cuando la app está detrás de nginx en /app/, exponer el prefijo para las plantillas
    # y fijar SCRIPT_NAME para que url_for() genere URLs con el prefijo.
    app.config.setdefault('APP_ROOT_PREFIX', '/app')
    @app.context_processor
    def inject_app_prefix():
        return dict(app_prefix=app.config.get('APP_ROOT_PREFIX', ''))

    # Helper to preserve current query string parameters when building links
    # Usage in templates: {{ url_keep('formaciones_bp.gestion_formaciones', page=2) }}
    @app.context_processor
    def inject_qs_helpers():
        from flask import request, url_for
        from urllib.parse import urlencode

        def url_keep(endpoint, **new_params):
            args = request.args.to_dict(flat=True)
            # remove empty values in new_params
            for k in list(new_params.keys()):
                v = new_params.get(k)
                if v is None or v == "":
                    new_params.pop(k, None)
            args.update(new_params)
            try:
                base = url_for(endpoint)
            except Exception:
                return '#'
            return f"{base}?{urlencode(args)}" if args else base

        return dict(url_keep=url_keep)

    # Middleware simple que fija environ['SCRIPT_NAME'] para que Flask genere URLs
    class PrefixMiddleware:
        def __init__(self, app, prefix):
            self.app = app
            self.prefix = prefix or ''
        def __call__(self, environ, start_response):
            try:
                environ['SCRIPT_NAME'] = self.prefix
            except Exception:
                pass
            return self.app(environ, start_response)

    # NOTE: we DO NOT wrap the WSGI app with PrefixMiddleware here.
    # Reason: if nginx is configured to rewrite Location headers (proxy_redirect),
    # having Flask already emit URLs prefixed with /app can lead to double prefixes
    # like /app/app/... . Instead we keep the Jinja helper `u()` (prefixed_url_for)
    # which templates use to generate URLs with the /app prefix, while allowing
    # Flask redirects to send plain-root locations (nginx will add the /app prefix
    # at proxy level). This is more robust when you don't control nginx or when
    # proxy_redirect is in use.
    # If you prefer the other behavior, re-enable the middleware by assigning:
    # app.wsgi_app = PrefixMiddleware(app.wsgi_app, app.config.get('APP_ROOT_PREFIX', ''))

    # Jinja helper: prefixed url_for (use in templates as {{ u('endpoint') }})
    from flask import url_for
    def prefixed_url_for(endpoint, **values):
        # generate URL with Flask, then prefix if not already
        try:
            url = url_for(endpoint, **values)
        except Exception:
            # If URL cannot be built (endpoint missing or wrong name), return a
            # harmless placeholder so templates don't raise during rendering.
            return '#'
        # don't prefix absolute/external URLs (including protocol-relative //)
        if isinstance(url, str) and (url.startswith('http://') or url.startswith('https://') or url.startswith('//')):
            return url
        prefix = app.config.get('APP_ROOT_PREFIX', '') or ''
        # avoid double-prefix if url already startswith prefix
        if prefix and not url.startswith(prefix):
            return prefix + url
        return url
    app.jinja_env.globals['u'] = prefixed_url_for
    # Make prefixed_url_for the default `url_for` inside templates so existing
    # templates continue to work without mass edits.
    app.jinja_env.globals['url_for'] = prefixed_url_for
    # Expose the Flask `app` object to templates as `current_app` and `app_obj`
    # for checks from templates. Use `app_obj` in templates to avoid interacting
    # with Flask's request-bound proxy when rendering outside a request.
    app.jinja_env.globals['current_app'] = app
    app.jinja_env.globals['app_obj'] = app
    # Middleware to normalize duplicated prefix in PATH_INFO: if nginx or a
    # client accidentally produces requests like /app/app/..., strip the
    # duplicate so Flask routes work as expected.
    class DeduplicatePrefixMiddleware:
        def __init__(self, app, prefix):
            self.app = app
            # ensure prefix starts with / and has no trailing slash (unless it's just '/')
            if not prefix:
                prefix = ''
            if prefix and not prefix.startswith('/'):
                prefix = '/' + prefix
            if prefix.endswith('/') and prefix != '/':
                prefix = prefix.rstrip('/')
            self.prefix = prefix

        def __call__(self, environ, start_response):
            try:
                path = environ.get('PATH_INFO', '') or ''
                pref = self.prefix or ''
                # Strip all leading occurrences of the prefix so that
                # '/app/app/xyz' -> '/xyz' and '/app/xyz' -> '/xyz'.
                if pref:
                    while path.startswith(pref):
                        path = path[len(pref):]
                    if not path.startswith('/'):
                        path = '/' + path
                    environ['PATH_INFO'] = path
            except Exception:
                pass
            return self.app(environ, start_response)

    app.wsgi_app = DeduplicatePrefixMiddleware(app.wsgi_app, app.config.get('APP_ROOT_PREFIX', '/app'))

    # --- Disable caching on all responses ---
    # This sets HTTP headers to prevent browsers from caching dynamic responses.
    # Note: static files served by nginx are controlled by nginx config; to
    # prevent caching of static assets you should adjust your nginx headers or
    # use cache-busting query strings on asset URLs.
    @app.after_request
    def add_no_cache_headers(response):
        try:
            # Prevent caching in the browser and intermediary caches
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        except Exception:
            pass
        return response

    # --- Student mode flag (for public flows) ---
    # g.student_mode will be True when session['student_mode'] is set by
    # public student flows (acceso/registro/examen). Templates can check
    # g.student_mode to hide admin chrome.
    from flask import g
    @app.before_request
    def load_student_mode():
        try:
            g.student_mode = bool(session.get('student_mode'))
        except Exception:
            g.student_mode = False

    # Default authentication enforcement is handled by Flask-Login and by
    # nginx basic-auth for the /app/ area; application-level global guards
    # were removed to avoid accidental bypasses of admin-only views.
    return app
