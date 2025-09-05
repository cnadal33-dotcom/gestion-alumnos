"""añade plantilla_diploma_id a TipoCurso

Revision ID: 5f78a22b66eb
Revises: acc80a25ac51
Create Date: 2025-07-18 00:55:10.878378

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5f78a22b66eb'
down_revision = 'acc80a25ac51'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('tipo_curso', schema=None) as batch_op:
        batch_op.add_column(sa.Column('plantilla_diploma_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_tipo_curso_plantilla_diploma',  # NOMBRE OBLIGATORIO
            'plantilla_diploma',                # tabla referenciada
            ['plantilla_diploma_id'],           # columna local
            ['id']                              # columna remota
        )

def downgrade():
    with op.batch_alter_table('tipo_curso', schema=None) as batch_op:
        batch_op.drop_constraint('fk_tipo_curso_plantilla_diploma', type_='foreignkey')
        batch_op.drop_column('plantilla_diploma_id')
