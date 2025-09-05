from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm

# Archivo de salida
output = "AYUDA_CAMPOS_ACTA.pdf"

# Datos de la tabla
fields = [
    ("NOMBRE_ALUMNO", "nombre_alumno", "Nombre completo del alumno"),
    ("DNI_ALUMNO", "dni_alumno", "DNI del alumno"),
    ("EMPRESA", "empresa", "Nombre de la empresa"),
    ("CURSO", "curso", "Nombre del curso"),
    ("FECHA", "fecha", "Fecha del curso (dd/mm/aaaa)"),
    ("ALUMNOS", "alumnos", "Lista de alumnos concatenada"),
    ("HORARIO", "horario", "Horario del curso"),
    ("LUGAR", "lugar", "Lugar/aula del curso"),
    ("DIRECCION_AULA", "direccion_aula", "Dirección del aula"),
    ("REFERENCIA", "referencia", "Referencia del curso"),
    ("POBLACION", "poblacion", "Población/ciudad"),
    ("FUNDAE", "fundae", "Sí/No según fundae"),
    ("FORMADOR", "formador", "Nombre del formador"),
    ("FIRMA_FORMADOR", "FIRMA_FORMADOR", "Firma digital del formador (imagen)"),
    ("ESPECIALIDAD", "especialidad", "Especialidad del formador/alumno"),
    ("RESULTADO", "resultado", "Resultado del examen/acta"),
    ("OBSERVACIONES", "observaciones", "Observaciones adicionales")
]

c = canvas.Canvas(output, pagesize=A4)
width, height = A4

c.setFont("Helvetica-Bold", 18)
c.drawString(2*cm, height-2*cm, "Campos para plantillas de actas PDF")
c.setFont("Helvetica", 12)
c.drawString(2*cm, height-2.7*cm, "Puedes usar estos nombres en tu plantilla PDF. El sistema los normaliza (minúsculas y sin acentos).")

# Tabla
x0, y0 = 2*cm, height-4*cm
row_height = 1*cm
col_widths = [6*cm, 5*cm, 7*cm]
c.setFont("Helvetica-Bold", 12)
c.setFillColor(colors.lightgrey)
c.rect(x0, y0-row_height, sum(col_widths), row_height, fill=1)
c.setFillColor(colors.black)
c.drawString(x0+0.2*cm, y0-0.7*cm, "Campo en PDF (ejemplo)")
c.drawString(x0+col_widths[0]+0.2*cm, y0-0.7*cm, "Nombre seguro (backend)")
c.drawString(x0+col_widths[0]+col_widths[1]+0.2*cm, y0-0.7*cm, "Contenido que se rellena")
c.setFont("Helvetica", 12)
for i, (campo, seguro, contenido) in enumerate(fields):
    y = y0-(i+2)*row_height
    c.setFillColor(colors.whitesmoke if i%2==0 else colors.lightyellow)
    c.rect(x0, y, sum(col_widths), row_height, fill=1)
    c.setFillColor(colors.black)
    c.drawString(x0+0.2*cm, y+0.3*cm, campo)
    c.drawString(x0+col_widths[0]+0.2*cm, y+0.3*cm, seguro)
    c.drawString(x0+col_widths[0]+col_widths[1]+0.2*cm, y+0.3*cm, contenido)

# Notas
c.setFont("Helvetica-Oblique", 11)
notas = [
    "Puedes escribir los nombres en mayúsculas, minúsculas o con acentos. El sistema los normaliza automáticamente.",
    "Ejemplo: DNI_ALUMNO, dni_alumno, Dni_Alumno o dni alumno funcionarán igual.",
    "Para la firma, el campo debe estar preparado para recibir una imagen (no como campo de texto).",
    "Usa estos nombres para los campos en tu plantilla PDF y el sistema los rellenará automáticamente."
]
for i, nota in enumerate(notas):
    c.drawString(2*cm, 4*cm-(i*0.7*cm), nota)

c.save()
