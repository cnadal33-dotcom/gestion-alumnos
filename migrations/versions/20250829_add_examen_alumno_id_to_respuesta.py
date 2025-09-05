"""add examen_alumno_id to respuesta

Revision ID: 20250829_add_examen_alumno_id
Revises: 
Create Date: 2025-08-29 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250829_add_examen_alumno_id'
down_revision = None
branch_labels = None
def upgrade():
    # Add column (nullable)
    op.add_column('respuesta', sa.Column('examen_alumno_id', sa.Integer(), nullable=True))
    # Create FK constraint
    op.create_foreign_key('fk_respuesta_examen_alumno', 'respuesta', 'examen_alumno', ['examen_alumno_id'], ['id'], ondelete='CASCADE')
    # Create index for faster queries filtering by pregunta_id and examen_alumno_id
    op.create_index('ix_respuesta_pregunta_modelo', 'respuesta', ['pregunta_id', 'examen_alumno_id'])


def downgrade():
    op.drop_index('ix_respuesta_pregunta_modelo', table_name='respuesta')
    op.drop_constraint('fk_respuesta_examen_alumno', 'respuesta', type_='foreignkey')
    op.drop_column('respuesta', 'examen_alumno_id')
