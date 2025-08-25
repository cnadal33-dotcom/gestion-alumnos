# Campos para plantillas de actas PDF

Puedes usar estos nombres de campos en tu plantilla PDF de actas para que el sistema los rellene automáticamente. Los nombres se normalizan (minúsculas y sin acentos), así que puedes escribirlos en mayúsculas, minúsculas o con acentos.

| Campo en PDF (ejemplo)      | Nombre seguro (backend) | Contenido que se rellena                |
|----------------------------|-------------------------|-----------------------------------------|
| NOMBRE_ALUMNO              | nombre_alumno           | Nombre completo del alumno              |
| DNI_ALUMNO                 | dni_alumno              | DNI del alumno                          |
| EMPRESA                    | empresa                 | Nombre de la empresa                    |
| CURSO                      | curso                   | Nombre del curso                        |
| FECHA                      | fecha                   | Fecha del curso (dd/mm/aaaa)            |
| ALUMNOS                    | alumnos                 | Lista de alumnos concatenada            |
| HORARIO                    | horario                 | Horario del curso                       |
| LUGAR                      | lugar                   | Lugar/aula del curso                    |
| DIRECCION_AULA             | direccion_aula          | Dirección del aula                      |
| REFERENCIA                 | referencia              | Referencia del curso                    |
| POBLACION                  | poblacion               | Población/ciudad                        |
| FUNDAE                     | fundae                  | Sí/No según fundae                      |
| FORMADOR                   | formador                | Nombre del formador                     |
| FIRMA_FORMADOR             | FIRMA_FORMADOR          | Firma digital del formador (imagen)     |
| ESPECIALIDAD               | especialidad            | Especialidad del formador/alumno        |
| RESULTADO                  | resultado               | Resultado del examen/acta               |
| OBSERVACIONES              | observaciones           | Observaciones adicionales               |

**Notas importantes:**
- Puedes escribir los nombres de los campos en mayúsculas, minúsculas o con acentos. El sistema los normaliza automáticamente.
- Ejemplo: `DNI_ALUMNO`, `dni_alumno`, `Dni_Alumno` o `dni alumno` funcionarán igual.
- Para la firma, el campo debe estar preparado para recibir una imagen (no como campo de texto).
- Usa estos nombres para los campos en tu plantilla PDF y el sistema los rellenará automáticamente con los datos reales de cada alumno y formación.
