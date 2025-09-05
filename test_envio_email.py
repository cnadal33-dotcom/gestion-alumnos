from mi_plataforma_formacion_app.utils.emailing import enviar_diploma_por_email

class AlumnoTest:
    def __init__(self, nombre, email, dni, formacion=None):
        self.nombre = nombre
        self.email = email
        self.dni = dni
        self.formacion = formacion

class FormacionTest:
    def __init__(self, tipo_curso, fecha1, empresa, formador):
        self.tipo_curso = tipo_curso
        self.fecha1 = fecha1
        self.empresa = empresa
        self.formador = formador

class TipoCursoTest:
    def __init__(self, nombre):
        self.nombre = nombre

class EmpresaTest:
    def __init__(self, nombre):
        self.nombre = nombre

class FormadorTest:
    def __init__(self, nombre):
        self.nombre = nombre

if __name__ == "__main__":
    import datetime
    alumno = AlumnoTest(
        nombre="Carlos Nadal",
        email="tu_email_de_prueba@tudominio.com",
        dni="12345678A",
        formacion=FormacionTest(
            tipo_curso=TipoCursoTest("Curso de Prueba"),
            fecha1=datetime.date.today(),
            empresa=EmpresaTest("Empresa Demo"),
            formador=FormadorTest("Formador Demo")
        )
    )
    ruta_pdf = "diploma_demo.pdf"  # Debe existir un PDF de prueba en la ruta
    print("Enviando email de prueba...")
    ok = enviar_diploma_por_email(alumno, ruta_pdf)
    print("Email enviado" if ok else "Error en el envío")
