from mi_plataforma_formacion_app.extensions import db
from dateutil.relativedelta import relativedelta
from datetime import date

class AlumnoFormacion(db.Model):
    __tablename__ = 'alumno_formacion'
    id           = db.Column(db.Integer, primary_key=True)
    alumno_id    = db.Column(db.Integer, db.ForeignKey('alumno.id'))
    formacion_id = db.Column(db.Integer, db.ForeignKey('formacion.id'))
    aprobado     = db.Column(db.Boolean, default=False)
    nota         = db.Column(db.Float)
    alumno       = db.relationship('Alumno', backref='alumno_formaciones')
    examen = db.relationship('ExamenAlumno', backref='alumno_formacion', uselist=False)

    @property
    def fecha_realizacion(self):
        return self.formacion.fecha1 if self.formacion and self.formacion.fecha1 else None

    @property
    def validez_meses(self):
        if self.formacion and self.formacion.tipo_curso:
            return self.formacion.tipo_curso.validez_meses
        return 0

    @property
    def fecha_caducidad(self):
        if self.validez_meses and self.validez_meses > 0 and self.fecha_realizacion:
            return self.fecha_realizacion + relativedelta(months=self.validez_meses)
        return None

    @property
    def estado_validez(self):
        if not self.formacion or not self.formacion.tipo_curso:
            return "Sin datos"
        if self.validez_meses == 0:
            return 'Permanente'
        elif self.fecha_caducidad:
            hoy = date.today()
            dias_restantes = (self.fecha_caducidad - hoy).days
            if self.fecha_caducidad < hoy:
                return 'Caducado'
            elif dias_restantes < 90:
                return 'Próxima a caducar'
            else:
                return 'Vigente'
        return 'Sin fecha'
