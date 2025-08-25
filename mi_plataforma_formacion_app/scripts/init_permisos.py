from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.permission import Permission
from mi_plataforma_formacion_app.models.user import User
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///formacion.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

permisos_basicos = [
    ('ver_alumnos', 'Acceso a alumnos'),
    ('ver_formaciones', 'Acceso a formaciones'),
    ('ver_empresas', 'Acceso a empresas'),
    ('ver_caducidades', 'Acceso a caducidades'),
    ('ver_calendario', 'Acceso a calendario'),
    ('ver_diplomas', 'Acceso a diplomas emitidos'),
]

with app.app_context():
    for nombre, descripcion in permisos_basicos:
        if not Permission.query.filter_by(name=nombre).first():
            db.session.add(Permission(name=nombre, description=descripcion))
    db.session.commit()
    print('Permisos básicos creados.')
