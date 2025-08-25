from pdfrw import PdfReader, PdfWriter

def rellenar_pdf(template_path, output_path, data_dict):
    import unicodedata
    def normaliza(txt):
        if not isinstance(txt, str):
            txt = ""
        txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode('utf-8')
        return txt.lower().strip()

    # Crear un nuevo diccionario normalizado para comparación robusta
    data_dict_norm = {normaliza(k): v for k, v in data_dict.items()}

    pdf = PdfReader(template_path)
    for page in pdf.pages:
        annotations = page.Annots
        if annotations:
            for annotation in annotations:
                if annotation.T:
                    key = annotation.T[1:-1]  # elimina paréntesis
                    key_norm = normaliza(key)
                    if key_norm in data_dict_norm:
                        print(f"Rellenando campo '{key}' con valor: {data_dict_norm[key_norm]}")
                        annotation.V = f'{data_dict_norm[key_norm]}'  # sin paréntesis
                        annotation.AP = None  # fuerza a refrescar el valor visual
    # Añadir flag NeedAppearances al AcroForm para que los valores se muestren correctamente
    from pdfrw import PdfDict, PdfObject
    # Manejo robusto de AcroForm y NeedAppearances
    acroform = getattr(pdf.Root, 'AcroForm', None)
    if acroform is not None:
        acroform.update(PdfDict(NeedAppearances=PdfObject('true')))
    else:
        pdf.Root.AcroForm = PdfDict(NeedAppearances=PdfObject('true'))
    PdfWriter(output_path, trailer=pdf).write()
