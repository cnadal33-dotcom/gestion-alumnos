
"""
Revision ID: add_ruta_pdf_to_plantilla_acta
Revises: ec495e6cf783
Create Date: 2025-08-08 19:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_ruta_pdf_to_plantilla_acta'
down_revision = 'ec495e6cf783'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('plantilla_acta', sa.Column('ruta_pdf', sa.String(length=255), nullable=True))

def downgrade():
    op.drop_column('plantilla_acta', 'ruta_pdf')
