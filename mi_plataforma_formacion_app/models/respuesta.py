from mi_plataforma_formacion_app.extensions import db

class Respuesta(db.Model):
    __tablename__ = 'respuesta'
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    correcta = db.Column(db.Boolean, default=False)
    pregunta_id = db.Column(db.Integer, db.ForeignKey('pregunta.id'))
