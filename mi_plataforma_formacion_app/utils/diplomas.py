# utils_diploma.py
# Requisitos:
#   pip install pdfrw reportlab Pillow
# Guardado:
#   static/diplomas/<empresa>/<YYYY-MM-DD>/diploma_<alumno>.pdf

import os
import re
import unicodedata
from datetime import datetime
from flask import current_app
from io import BytesIO

from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image


def normaliza_nombre_archivo(txt: str) -> str:
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode('utf-8')
    txt = re.sub(r'[^\w\s-]', '', txt).strip().lower()
    txt = re.sub(r'[-\s]+', '_', txt)
    return txt


def _tam_pagina(pdf_page):
    m = pdf_page.MediaBox  # [llx, lly, urx, ury]
    return (float(m[2]) - float(m[0]), float(m[3]) - float(m[1]))


def _campos_por_pagina(pdf_doc):
    """
    Devuelve {page_index: [ {'name': str, 'rect': (x,y,w,h)} , ... ]}
    usando los /Rect de los campos del AcroForm.
    """
    resultado = {}
    for idx, page in enumerate(pdf_doc.pages):
        annots = getattr(page, 'Annots', None)
        campos = []
        if annots:
            for a in annots:
                t = str(a.T)
                nombre = t[1:-1] if t.startswith('(') and t.endswith(')') else t
                rect = a.Rect
                x1, y1, x2, y2 = [float(r) for r in rect]
                campos.append({
                    "name": nombre,
                    "rect": (x1, y1, x2-x1, y2-y1)
                })
        resultado[idx] = campos
    return resultado


def rellenar_y_aplanar_pdf(ruta_plantilla, data, firma_path=None, font_name="Helvetica", font_size=12):
    if not os.path.exists(ruta_plantilla):
        print(f"❌ Plantilla no encontrada: {ruta_plantilla}")
        return None

    try:
        pdf = PdfReader(ruta_plantilla)
        fields_by_page = _campos_por_pagina(pdf)

        FONT_NAME = font_name
        FONT_SIZE = font_size

        for idx, page in enumerate(pdf.pages):
            w, h = _tam_pagina(page)
            overlay_buf = BytesIO()
            c = canvas.Canvas(overlay_buf, pagesize=(w, h))
            c.setFont(FONT_NAME, FONT_SIZE)


            # Prepara diccionario de datos insensible a mayúsculas/minúsculas
            import unicodedata
            def quitar_acentos(s):
                return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('utf-8').lower()
            data_lower = {quitar_acentos(k): v for k, v in data.items()}
            for f in fields_by_page.get(idx, []):
                name = f["name"]
                x, y, fw, fh = f["rect"]
                # Buscar el campo original en el PDF para extraer /DA
                campo_annot = None
                annots = getattr(page, 'Annots', None)
                if annots:
                    for a in annots:
                        t = str(a.T)
                        nombre = t[1:-1] if t.startswith('(') and t.endswith(')') else t
                        if nombre == name:
                            campo_annot = a
                            break

                # Detectar fuente y tamaño desde /DA si existe
                campo_font = font_name
                campo_size = font_size
                if campo_annot and hasattr(campo_annot, 'DA') and campo_annot.DA:
                    da = str(campo_annot.DA)
                    m = re.search(r'/([A-Za-z]+)\s+(\d+(?:\.\d+)?)\s+Tf', da)
                    if m:
                        campo_font = {
                            'Helv': 'Helvetica',
                            'Cour': 'Courier',
                            'Ti': 'Times-Roman',
                            'Times': 'Times-Roman',
                            'Arial': 'Arial',
                        }.get(m.group(1), font_name)
                        campo_size = float(m.group(2))

                # Firma del formador si existe el campo FIRMA_FORMADOR
                if name == 'FIRMA_FORMADOR' and firma_path and os.path.isfile(firma_path):
                    try:
                        img = Image.open(firma_path)
                        iw, ih = img.size if img.size != (0, 0) else (1, 1)
                        ratio = min(fw / iw, fh / ih)
                        dw, dh = iw * ratio, ih * ratio
                        dx = x + (fw - dw) / 2.0
                        dy = y + (fh - dh) / 2.0
                        c.drawImage(ImageReader(img), dx, dy, width=dw, height=dh,
                                    preserveAspectRatio=True, mask='auto')
                    except Exception as e:
                        print(f"[DEBUG] Firma no insertada: {e}")
                    continue

                # Texto normal: soporta {{ campo }} y campo en minúsculas
                campo_key = quitar_acentos(name)
                if campo_key.startswith('{{') and campo_key.endswith('}}'):
                    campo_key = quitar_acentos(campo_key[2:-2].strip())
                if campo_key in data_lower and data_lower[campo_key] is not None:
                    valor = str(data_lower[campo_key])
                    c.setFont(campo_font, campo_size)
                    tx = x + 2
                    ty = y + (fh - campo_size) / 2.0 + 2
                    c.drawString(tx, ty, valor)

            c.showPage()
            c.save()
            overlay_buf.seek(0)

            # Fusionar overlay con la página
            overlay_pdf = PdfReader(fdata=overlay_buf.getvalue())
            PageMerge(page).add(overlay_pdf.pages[0]).render()

            # Eliminar campos para aplanar
            if getattr(page, 'Annots', None):
                page.Annots = []

        # Eliminar AcroForm solo en la raíz del PDF principal (ignorar si no existe)
        try:
            if hasattr(pdf, 'Root') and hasattr(pdf.Root, 'AcroForm'):
                del pdf.Root.AcroForm
        except Exception as acro_err:
            print(f"[DEBUG] No se pudo eliminar AcroForm: {acro_err}")

        out_mem = BytesIO()
        PdfWriter().write(out_mem, pdf)
        return out_mem.getvalue()
    except Exception as e:
        print(f"❌ Error rellenando/aplanando (overlay): {e}")
        return None


def guardar_diploma_pdf(alumno, formacion, pdf_bytes: bytes) -> str | None:
    if not alumno or not formacion or not formacion.empresa or not formacion.fecha1 or not pdf_bytes:
        print("❌ guardar_diploma_pdf: datos incompletos")
        return None

    empresa_normalizada = normaliza_nombre_archivo(formacion.empresa.nombre)
    fecha_str = formacion.fecha1.strftime("%Y-%m-%d")
    alumno_normalizado = normaliza_nombre_archivo(alumno.nombre)
    nombre_archivo = f"diploma_{alumno_normalizado}.pdf"

    carpeta = os.path.join(current_app.static_folder, 'diplomas', empresa_normalizada, fecha_str)
    os.makedirs(carpeta, exist_ok=True)
    ruta_completa = os.path.join(carpeta, nombre_archivo)

    try:
        with open(ruta_completa, 'wb') as f:
            f.write(pdf_bytes)
        print(f"✅ Diploma guardado: {ruta_completa}")
        return ruta_completa
    except Exception as e:
        print(f"❌ Error al guardar diploma: {e}")
        return None


def crear_y_guardar_diploma(alumno, formacion, plantilla=None) -> str | None:
    """
    Genera el diploma con datos del alumno/formación y lo guarda en /static/diplomas/...
    Devuelve la ruta absoluta del PDF guardado o None si falla.
    """
    # Si no se proporciona plantilla, intentar obtenerla desde el tipo de curso asociado a la formación
    if not plantilla:
        try:
            plantilla = formacion.tipo_curso.plantilla_diploma if formacion and getattr(formacion, 'tipo_curso', None) else None
        except Exception:
            plantilla = None

    if not plantilla or not getattr(plantilla, 'ruta_pdf', None):
        print("❌ No hay plantilla PDF definida")
        return None

    ruta_plantilla = os.path.join(current_app.static_folder, plantilla.ruta_pdf)
    if not os.path.exists(ruta_plantilla):
        print(f"❌ Plantilla no encontrada: {ruta_plantilla}")
        return None

    datos = {
        'nombre_alumno': (alumno.nombre or '').title(),
        'dni_alumno': alumno.dni or '',
        'empresa': formacion.empresa.nombre if formacion.empresa else '',
        'curso': formacion.tipo_curso.nombre if formacion.tipo_curso else '',
        'fecha': formacion.fecha1.strftime("%d/%m/%Y") if formacion.fecha1 else '',
        'alumnos': '\n'.join([
            f"{rel.alumno.nombre} | {rel.alumno.dni}" for rel in getattr(formacion, 'alumnos_rel', [])
        ]) if hasattr(formacion, 'alumnos_rel') else '',
        'horario': getattr(formacion, 'horario', '') or '',
        'lugar': getattr(formacion, 'direccion_aula', '') or '',
        'direccion_aula': getattr(formacion, 'direccion_aula', '') or '',
        'referencia': getattr(formacion, 'referencia', '') or '',
        'poblacion': getattr(formacion, 'poblacion', '') or '',
        'fundae': 'Sí' if getattr(formacion, 'fundae', False) else 'No',
        'formador': formacion.formador.nombre if formacion.formador else '',
    }
    print("==== DATOS QUE SE ENVIAN AL PDF (DIPLOMA) ====")
    print(f"DNI: {datos['dni_alumno']}")
    print(f"INSTRUCTOR: {datos['formador']}")
    print("==== FIN DATOS PDF ====")

    # Ruta firma (opcional)
    firma_path = None
    if getattr(formacion, 'formador', None) and getattr(formacion.formador, 'firma', None):
        if not formacion.formador.firma.startswith('firmas_formadores/'):
            firma_path = os.path.join(current_app.static_folder, 'firmas_formadores', formacion.formador.firma)
        else:
            firma_path = os.path.join(current_app.static_folder, formacion.formador.firma)

    pdf_bytes = rellenar_y_aplanar_pdf(ruta_plantilla, datos, firma_path)
    if not pdf_bytes:
        print("❌ No se pudo generar el PDF")
        return None

    return guardar_diploma_pdf(alumno, formacion, pdf_bytes)