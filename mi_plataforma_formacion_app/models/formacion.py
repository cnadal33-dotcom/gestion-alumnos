from mi_plataforma_formacion_app.extensions import db

class Formacion(db.Model):
    __tablename__ = 'formacion'
    id             = db.Column(db.Integer, primary_key=True)
    referencia = db.Column(db.String(32), nullable=True)
    tipo_curso_id  = db.Column(db.Integer, db.ForeignKey('tipo_curso.id'))
    empresa_id     = db.Column(db.Integer, db.ForeignKey('empresa.id'))
    dos_ediciones  = db.Column(db.Boolean, default=False)
    fecha1         = db.Column(db.Date)
    hora_inicio1   = db.Column(db.Time)
    hora_fin1      = db.Column(db.Time)
    fecha2         = db.Column(db.Date)
    hora_inicio2   = db.Column(db.Time)
    hora_fin2      = db.Column(db.Time)
    direccion_aula = db.Column(db.String(256))
    fundae         = db.Column(db.Boolean, default=False)
    formador_id    = db.Column(db.Integer, db.ForeignKey('formador.id'))
    observaciones  = db.Column(db.Text)
    alumno_formaciones = db.relationship('AlumnoFormacion', backref='formacion', lazy=True)
    cerrada = db.Column(db.Boolean, default=False)
    poblacion = db.Column(db.String(128))
