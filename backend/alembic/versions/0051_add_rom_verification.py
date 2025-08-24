"""Add ROM verification table

Revision ID: 0051_add_rom_verification
Revises: 0050_firmware_add_is_verified
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0051_add_rom_verification'
down_revision = '0050_firmware_add_is_verified'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create verification_status enum
    verification_status_enum = sa.Enum('pending', 'verified', 'rejected', 'expired', name='verificationstatus')
    verification_status_enum.create(op.get_bind())
    
    # Create rom_verifications table
    op.create_table(
        'rom_verifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('rom_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', verification_status_enum, nullable=False, default='pending'),
        sa.Column('uploaded_file_name', sa.String(length=255), nullable=False),
        sa.Column('uploaded_file_size', sa.BigInteger(), nullable=False, default=0),
        sa.Column('uploaded_md5_hash', sa.String(length=32), nullable=False),
        sa.Column('uploaded_sha1_hash', sa.String(length=40), nullable=False),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['rom_id'], ['roms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verified_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rom_id', 'user_id', name='unique_rom_user_verification')
    )
    
    # Create indexes
    op.create_index('idx_rom_verifications_rom_id', 'rom_verifications', ['rom_id'])
    op.create_index('idx_rom_verifications_user_id', 'rom_verifications', ['user_id'])
    op.create_index('idx_rom_verifications_status', 'rom_verifications', ['status'])
    op.create_index('idx_rom_verifications_expires_at', 'rom_verifications', ['expires_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_rom_verifications_expires_at', 'rom_verifications')
    op.drop_index('idx_rom_verifications_status', 'rom_verifications')
    op.drop_index('idx_rom_verifications_user_id', 'rom_verifications')
    op.drop_index('idx_rom_verifications_rom_id', 'rom_verifications')
    
    # Drop table
    op.drop_table('rom_verifications')
    
    # Drop enum
    verification_status_enum = sa.Enum(name='verificationstatus')
    verification_status_enum.drop(op.get_bind())
