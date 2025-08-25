from mi_plataforma_formacion_app.extensions import db

class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)  # <- UNIQUE!
    cif = db.Column(db.String(50), unique=True, nullable=False)      # <- UNIQUE y obligatorio
    direccion = db.Column(db.String(200))
    poblacion = db.Column(db.String(100))
    provincia = db.Column(db.String(100))
    contacto = db.Column(db.String(100))
    email = db.Column(db.String(100))
    telefono = db.Column(db.String(30))
    comercial_id = db.Column(db.Integer, db.ForeignKey('comercial.id'))
    comercial = db.relationship('Comercial', backref='empresas')
