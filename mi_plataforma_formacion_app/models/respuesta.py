from mi_plataforma_formacion_app.extensions import db

class Respuesta(db.Model):
    __tablename__ = 'respuesta'
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    correcta = db.Column(db.Boolean, default=False)
    es_correcta = db.Column(db.Boolean, default=False)
    pregunta_id = db.Column(db.Integer, db.ForeignKey('pregunta.id'))
    # separa respuestas del modelo (NULL) de respuestas de alumnos (tienen examen_alumno_id)
    examen_alumno_id = db.Column(db.Integer, db.ForeignKey('examen_alumno.id'), nullable=True)

    __table_args__ = (
        db.Index('ix_respuesta_pregunta_modelo', 'pregunta_id', 'examen_alumno_id'),
    )
