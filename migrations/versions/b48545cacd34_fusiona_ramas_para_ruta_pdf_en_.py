"""Fusiona ramas para ruta_pdf en plantilla_acta

Revision ID: b48545cacd34
Revises: add_ruta_pdf_to_plantilla_acta, 5849cb749ac6
Create Date: 2025-08-08 19:32:04.136835

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b48545cacd34'
down_revision = ('add_ruta_pdf_to_plantilla_acta', '5849cb749ac6')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
