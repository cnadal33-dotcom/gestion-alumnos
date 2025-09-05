"""merge heads bd04513a6f2f and 20250829_add_examen_alumno_id

Revision ID: merge_bd04513a6f2f_20250829
Revises: bd04513a6f2f, 20250829_add_examen_alumno_id
Create Date: 2025-08-29 02:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_bd04513a6f2f_20250829'
down_revision = ('bd04513a6f2f', '20250829_add_examen_alumno_id')
branch_labels = None
depends_on = None


def upgrade():
    # merge migration - no DB changes
    pass


def downgrade():
    # cannot safely downgrade a merge
    pass
