from mi_plataforma_formacion_app.extensions import db

class PlantillaDiploma(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    ruta_pdf = db.Column(db.String(255), nullable=True)
