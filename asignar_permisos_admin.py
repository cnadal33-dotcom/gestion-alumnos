from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.user import User
from mi_plataforma_formacion_app.models.permission import Permission
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///formacion.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    user = User.query.filter_by(username='admin').first()
    if not user:
        print('No existe el usuario admin.')
    else:
        permisos = Permission.query.all()
        user.permissions = permisos
        db.session.commit()
        print('Permisos asignados correctamente al usuario admin.')
