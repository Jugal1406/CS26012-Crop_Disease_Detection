"""clerk_auth_identity_mapping

Revision ID: d6a9eecc88cf
Revises: 40143822dc19
Create Date: 2026-10-10 12:22:23.834733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6a9eecc88cf'
down_revision: Union[str, None] = '40143822dc19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Explicit composite unique constraint guaranteeing idempotency for Clerk/external identities
    op.create_unique_constraint(
        'uq_users_auth_provider_uid',
        'users',
        ['auth_provider', 'auth_provider_user_id']
    )


def downgrade() -> None:
    op.drop_constraint('uq_users_auth_provider_uid', 'users', type_='unique')
