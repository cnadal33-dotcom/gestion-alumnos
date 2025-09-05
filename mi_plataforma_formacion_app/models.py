from .extensions import db
from sqlalchemy import and_
from mi_plataforma_formacion_app.models.formador_tipo_curso import formador_tipo_curso
from datetime import date
from dateutil.relativedelta import relativedelta


class ExamenModelo(db.Model):
    __tablename__ = 'examen_modelo'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(128), nullable=False)
    descripcion = db.Column(db.Text)
    preguntas = db.relationship('Pregunta', backref='examen_modelo', lazy=True, cascade="all, delete-orphan")
    tipos_curso = db.relationship('TipoCurso', back_populates='examen_modelo')

class TipoCurso(db.Model):
    __tablename__ = 'tipo_curso'
    id            = db.Column(db.Integer, primary_key=True)
    nombre        = db.Column(db.String(128), nullable=False)
    duracion_horas= db.Column(db.Integer)
    temario       = db.Column(db.Text)
    objetivos     = db.Column(db.Text)
    pdf_temario   = db.Column(db.String(255))  # Campo PDF
    pdf_objetivos = db.Column(db.String(255))  # PDF de objetivos
    validez_meses = db.Column(db.Integer, nullable=False, default=0)  # 0 = permanente
    color = db.Column(db.String(20), default="#FFA500")  # Color hexadecimal, por defecto naranja
    requiere_renovacion = db.Column(db.Boolean, nullable=False, default=False)
    formaciones   = db.relationship('Formacion', backref='tipo_curso', lazy=True)
    formadores    = db.relationship('Formador', secondary=formador_tipo_curso, back_populates='tipos_curso')
    examen_modelo_id = db.Column(db.Integer, db.ForeignKey('examen_modelo.id'))
    examen_modelo = db.relationship('ExamenModelo', back_populates='tipos_curso', uselist=False)
    plantilla_diploma_id = db.Column(db.Integer, db.ForeignKey('plantilla_diploma.id'), nullable=True)
    plantilla_diploma = db.relationship('PlantillaDiploma', foreign_keys=[plantilla_diploma_id])
    plantilla_acta_id = db.Column(db.Integer, db.ForeignKey('plantilla_acta.id'), nullable=True)
    plantilla_acta = db.relationship('PlantillaActa', foreign_keys=[plantilla_acta_id])

    @property
    def es_permanente(self):
        return self.validez_meses == 0

    @property
    def mostrar_validez(self):
        return "Permanente" if self.es_permanente else f"{self.validez_meses} meses"

    def calcular_requiere_renovacion(self):
        return self.validez_meses > 0

class Comercial(db.Model):
    __tablename__ = 'comercial'
    id       = db.Column(db.Integer, primary_key=True)
    nombre   = db.Column(db.String(128), nullable=False)
    email    = db.Column(db.String(128))
    telefono = db.Column(db.String(32))
    empresas = db.relationship('Empresa', backref='comercial', lazy=True)

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

class Alumno(db.Model):
    __tablename__ = 'alumno'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    dni = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(30))
    interesado_mas_cursos = db.Column(db.Boolean, default=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'))
    observaciones = db.Column(db.Text)

class Formador(db.Model):
    __tablename__ = 'formador'
    id       = db.Column(db.Integer, primary_key=True)
    nombre   = db.Column(db.String(128), nullable=False)
    email    = db.Column(db.String(128))
    telefono = db.Column(db.String(32))
    firma = db.Column(db.String(200))
    formaciones = db.relationship('Formacion', backref='formador', lazy=True)
    tipos_curso  = db.relationship('TipoCurso', secondary=formador_tipo_curso, back_populates='formadores')

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
    poblacion = db.Column(db.String(128))  # Campo para la población


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

class Pregunta(db.Model):
    __tablename__ = 'pregunta'
    id                = db.Column(db.Integer, primary_key=True)
    texto             = db.Column(db.String(512), nullable=False)
    examen_modelo_id  = db.Column(db.Integer, db.ForeignKey('examen_modelo.id'), nullable=False)
    # `respuestas` should represent the model's options only (examen_alumno_id IS NULL).
    # Student answers are stored in the same table but must not be exposed via this relationship.
    respuestas        = db.relationship(
        'Respuesta',
        backref='pregunta',
        cascade="all, delete-orphan",
        primaryjoin="and_(Respuesta.pregunta_id==Pregunta.id, Respuesta.examen_alumno_id==None)",
        lazy=True
    )
    # Separate read-only relationship to access student answers for this question
    respuestas_alumno = db.relationship(
        'Respuesta',
        primaryjoin="and_(Respuesta.pregunta_id==Pregunta.id, Respuesta.examen_alumno_id!=None)",
        viewonly=True,
        lazy=True
    )

class Respuesta(db.Model):
    __tablename__ = 'respuesta'
    id          = db.Column(db.Integer, primary_key=True)
    texto       = db.Column(db.String(256), nullable=False)
    es_correcta = db.Column(db.Boolean, default=False)
    pregunta_id = db.Column(db.Integer, db.ForeignKey('pregunta.id'))
    
class ExamenAlumno(db.Model):
    __tablename__ = 'examen_alumno'
    id = db.Column(db.Integer, primary_key=True)
    alumno_formacion_id = db.Column(db.Integer, db.ForeignKey('alumno_formacion.id'))
    respuestas_json = db.Column(db.Text)
    nota_automatica = db.Column(db.Float)

from mi_plataforma_formacion_app.extensions import db

class PlantillaDiploma(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    ruta_pdf = db.Column(db.String(255), nullable=True)  # Ruta al PDF autorrellenable


class PlantillaActa(db.Model):
    __tablename__ = 'plantilla_acta'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200))
    # html = db.Column(db.Text)  # Eliminado: ya no se usa código HTML
    acta_docx = db.Column(db.String(255))   # <-- ESTE CAMPO ES IMPRESCINDIBLE
    ruta_pdf = db.Column(db.String(255), nullable=True)  # Ruta al PDF autorrellenable
