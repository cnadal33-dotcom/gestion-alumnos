import os
from pdfrw import PdfReader, PdfWriter

def rellenar_pdf(template_path, output_path, data_dict):
    import unicodedata
    from pdfrw import PdfDict, PdfObject

    def normaliza(txt):
        if not isinstance(txt, str):
            txt = ""
        txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode('utf-8')
        return txt.lower().strip()

    # Normalizar claves del diccionario para búsquedas insensibles
    try:
        data_dict_norm = {normaliza(k): v for k, v in data_dict.items()}
    except Exception:
        data_dict_norm = {}

    # Input validation: template path must exist
    if not template_path or not os.path.exists(template_path):
        print(f"❌ Plantilla PDF no encontrada para rellenar: {template_path}")
        return None

    try:
        pdf = PdfReader(template_path)
    except Exception as e:
        print(f"❌ Error leyendo plantilla PDF: {e}")
        return None

    try:
        for page in getattr(pdf, 'pages', []) or []:
            annotations = getattr(page, 'Annots', None)
            if annotations:
                for annotation in annotations:
                    if not getattr(annotation, 'T', None):
                        continue
                    # annotation.T puede tener paréntesis o ser un PdfString
                    t = str(annotation.T)
                    key = t[1:-1] if t.startswith('(') and t.endswith(')') else t
                    key_norm = normaliza(key)
                    if key_norm in data_dict_norm:
                        try:
                            val = data_dict_norm[key_norm]
                            print(f"Rellenando campo '{key}' con valor: {val}")
                            annotation.V = f'{val}'
                            annotation.AP = None
                        except Exception:
                            pass

        # Añadir flag NeedAppearances al AcroForm si es posible
        try:
            acroform = getattr(pdf.Root, 'AcroForm', None)
            if acroform is not None:
                acroform.update(PdfDict(NeedAppearances=PdfObject('true')))
            else:
                pdf.Root.AcroForm = PdfDict(NeedAppearances=PdfObject('true'))
        except Exception:
            pass

        # Guardar resultado
        PdfWriter(output_path, trailer=pdf).write()
        return True
    except Exception as e:
        print(f"❌ Error rellenando PDF: {e}")
        return None
