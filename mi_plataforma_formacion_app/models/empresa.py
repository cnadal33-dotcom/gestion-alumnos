from mi_plataforma_formacion_app.extensions import db

class Empresa(db.Model):
    __tablename__ = 'empresa'
    id           = db.Column(db.Integer, primary_key=True)
    nombre       = db.Column(db.String(128), unique=True, nullable=False)
    cif          = db.Column(db.String(32), unique=True, nullable=False)
    direccion    = db.Column(db.String(256))
    poblacion    = db.Column(db.String(64))
    provincia    = db.Column(db.String(64))
    contacto     = db.Column(db.String(128))
    email        = db.Column(db.String(128))
    telefono     = db.Column(db.String(32))
    comercial_id = db.Column(db.Integer, db.ForeignKey('comercial.id'), nullable=True)
    formaciones  = db.relationship('Formacion', backref='empresa', lazy=True)
    alumnos      = db.relationship('Alumno', backref='empresa', lazy=True)
