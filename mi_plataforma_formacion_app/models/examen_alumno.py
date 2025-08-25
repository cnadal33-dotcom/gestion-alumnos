from mi_plataforma_formacion_app.extensions import db

class ExamenAlumno(db.Model):
    __tablename__ = 'examen_alumno'
    id = db.Column(db.Integer, primary_key=True)
    alumno_formacion_id = db.Column(db.Integer, db.ForeignKey('alumno_formacion.id', name='fk_examen_alumno_alumno_formacion'))
    examen_modelo_id = db.Column(db.Integer, db.ForeignKey('examen_modelo.id', name='fk_examen_alumno_examen_modelo'))
    nota = db.Column(db.Float)
    fecha = db.Column(db.Date)
