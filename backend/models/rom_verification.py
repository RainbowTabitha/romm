from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from models.base import BaseModel
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from models.rom import Rom
    from models.user import User


class VerificationStatus(enum.Enum):
    """Status of ROM ownership verification"""
    PENDING = "pending"  # ROM uploaded, waiting for verification
    VERIFIED = "verified"  # ROM hash matches, ownership confirmed
    REJECTED = "rejected"  # ROM hash doesn't match, ownership denied
    EXPIRED = "expired"  # Verification link expired


class RomVerification(BaseModel):
    """Model for tracking ROM ownership verification"""
    __tablename__ = "rom_verifications"
    __table_args__ = (
        UniqueConstraint("rom_id", "user_id", name="unique_rom_user_verification"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Foreign keys
    rom_id: Mapped[int] = mapped_column(ForeignKey("roms.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    # Verification details
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.PENDING
    )
    
    # User uploaded ROM details
    uploaded_file_name: Mapped[str] = mapped_column(String(255))
    uploaded_file_size: Mapped[int] = mapped_column(default=0)
    uploaded_md5_hash: Mapped[str] = mapped_column(String(32))  # MD5 is 32 chars
    uploaded_sha1_hash: Mapped[str] = mapped_column(String(40))  # SHA1 is 40 chars
    
    # Verification metadata
    verification_notes: Mapped[str | None] = mapped_column(Text, default=None)
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    verified_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    
    # Expiration
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)
    )
    
    # Relationships
    rom: Mapped[Rom] = relationship(lazy="joined", back_populates="verifications")
    user: Mapped[User] = relationship(lazy="joined", back_populates="rom_verifications", foreign_keys=[user_id])
    verifier: Mapped[User | None] = relationship(
        "User", 
        foreign_keys=[verified_by], 
        lazy="joined"
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if verification has expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def can_verify(self) -> bool:
        """Check if verification can still be processed"""
        return (
            self.status == VerificationStatus.PENDING 
            and not self.is_expired
        )
    
    def verify_ownership(self, verifier_user_id: int, notes: str | None = None) -> None:
        """Mark ROM ownership as verified"""
        self.status = VerificationStatus.VERIFIED
        self.verified_at = datetime.now(timezone.utc)
        self.verified_by = verifier_user_id
        self.verification_notes = notes
    
    def reject_verification(self, verifier_user_id: int, notes: str | None = None) -> None:
        """Mark ROM ownership verification as rejected"""
        self.status = VerificationStatus.REJECTED
        self.verified_at = datetime.now(timezone.utc)
        self.verified_by = verifier_user_id
        self.verification_notes = notes
    
    def mark_expired(self) -> None:
        """Mark verification as expired"""
        self.status = VerificationStatus.EXPIRED
