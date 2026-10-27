"""Draft -> review -> published for dimensions, metrics and glossary terms

Revision ID: 0004_review_flow
Revises: 0003_dimensions
Create Date: 2026-10-27 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '0004_review_flow'
down_revision = '0003_dimensions'
branch_labels = None
depends_on = None

# table -> (old unique constraint, new partial unique index, column it covers)
LIVE_UNIQUE = {
    'dimension': ('uq_dimension_key', 'uq_dimension_key_live', 'key'),
    'metric': ('uq_metric_name', 'uq_metric_name_live', 'name'),
    'glossary_term': ('uq_glossary_term_term', 'uq_glossary_term_live', 'term'),
}
LIVE_ONLY = sa.text('draft_of_id IS NULL')
# databases built by the old create_all() startup may hold unnamed UNIQUE constraints: name them like the models do
CONVENTION = {'uq': 'uq_%(table_name)s_%(column_0_name)s'}


def unique_name(table: str, column: str) -> str:
    """The name of the UNIQUE constraint on a single column (unnamed ones get the convention's name)."""
    for uc in sa.inspect(op.get_bind()).get_unique_constraints(table):
        if uc['column_names'] == [column]:
            return uc['name'] or CONVENTION['uq'] % {'table_name': table, 'column_0_name': column}
    raise RuntimeError(f'no unique constraint on {table}.{column}')


def upgrade() -> None:
    for table, (old, new, col) in LIVE_UNIQUE.items():
        old = unique_name(table, col)
        with op.batch_alter_table(table, schema=None, naming_convention=CONVENTION) as batch_op:
            if table == 'glossary_term':     # terms existed before the review flow: they are live
                batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=False, server_default='published'))
            batch_op.add_column(sa.Column('draft_of_id', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('review_note', sa.Text(), nullable=True))
            batch_op.add_column(sa.Column('submitted_by', sa.String(length=200), nullable=True))
            batch_op.add_column(sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True))
            batch_op.drop_constraint(old, type_='unique')
            batch_op.create_index(new, [col], unique=True, postgresql_where=LIVE_ONLY, sqlite_where=LIVE_ONLY)
    with op.batch_alter_table('dimension_binding', schema=None, naming_convention=CONVENTION) as batch_op:
        batch_op.drop_constraint(unique_name('dimension_binding', 'column_id'), type_='unique')


def downgrade() -> None:
    op.execute('DELETE FROM dimension_binding WHERE dimension_id IN (SELECT id FROM dimension WHERE draft_of_id IS NOT NULL)')
    op.execute('DELETE FROM dimension_value WHERE dimension_id IN (SELECT id FROM dimension WHERE draft_of_id IS NOT NULL)')
    for table in LIVE_UNIQUE:
        op.execute(f'DELETE FROM {table} WHERE draft_of_id IS NOT NULL')
    with op.batch_alter_table('dimension_binding', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_dimension_binding_column_id', ['column_id'])
    for table, (old, new, col) in LIVE_UNIQUE.items():
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_index(new, postgresql_where=LIVE_ONLY, sqlite_where=LIVE_ONLY)
            batch_op.create_unique_constraint(old, [col])
            for c in ('submitted_at', 'submitted_by', 'review_note', 'draft_of_id'):
                batch_op.drop_column(c)
            if table == 'glossary_term':
                batch_op.drop_column('status')
