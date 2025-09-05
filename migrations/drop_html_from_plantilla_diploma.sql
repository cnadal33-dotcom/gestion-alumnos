-- SQL para SQLite: eliminar la columna `html` de la tabla plantilla_diploma
-- IMPORTANTE: Haz una copia de seguridad de instance/formacion.db antes de ejecutar.
-- Ejecución sugerida:
--   cp instance/formacion.db instance/formacion.db.bak
--   sqlite3 instance/formacion.db < migrations/drop_html_from_plantilla_diploma.sql

PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

-- Si la tabla ya está sin la columna `html`, esto no hace cambios.
-- 1) Renombrar tabla actual
ALTER TABLE plantilla_diploma RENAME TO plantilla_diploma_old;

-- 2) Crear nueva tabla sin la columna 'html'
CREATE TABLE plantilla_diploma (
  id INTEGER PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  ruta_pdf VARCHAR(255)
);

-- 3) Copiar datos de la tabla antigua a la nueva (seleccionando columnas existentes)
INSERT INTO plantilla_diploma (id, nombre, ruta_pdf)
SELECT id, nombre, ruta_pdf FROM plantilla_diploma_old;

-- 4) Borrar tabla antigua
DROP TABLE plantilla_diploma_old;

COMMIT;
PRAGMA foreign_keys = ON;

-- Nota: Si existen claves foráneas que referencien plantilla_diploma, adapta el script para recrear los indices y constraints necesarios.
