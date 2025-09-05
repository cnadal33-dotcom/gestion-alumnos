from datetime import datetime
from mi_plataforma_formacion_app.extensions import db


class PlantillaActa(db.Model):
    __tablename__ = 'plantilla_acta'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    ruta_pdf = db.Column(db.String(512), nullable=True)

    def __repr__(self):
        return f"<PlantillaActa id={self.id} nombre={self.nombre!r}>"
