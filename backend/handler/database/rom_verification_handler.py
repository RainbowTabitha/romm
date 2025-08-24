from collections.abc import Sequence
from typing import TYPE_CHECKING

from decorators.database import begin_session
from models.rom_verification import RomVerification, VerificationStatus
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from .base_handler import DBBaseHandler

if TYPE_CHECKING:
    from models.user import User


class DBRomVerificationHandler(DBBaseHandler):
    @begin_session
    def add_verification(self, verification: RomVerification, session: Session = None) -> RomVerification:
        """Add a new ROM verification record"""
        return session.merge(verification)

    @begin_session
    def get_verification(self, id: int, session: Session = None) -> RomVerification | None:
        """Get verification by ID"""
        return session.get(RomVerification, id)

    @begin_session
    def get_verification_by_rom_and_user(
        self, rom_id: int, user_id: int, session: Session = None
    ) -> RomVerification | None:
        """Get verification by ROM ID and user ID"""
        return session.scalar(
            select(RomVerification)
            .filter(
                RomVerification.rom_id == rom_id,
                RomVerification.user_id == user_id
            )
            .limit(1)
        )

    @begin_session
    def get_verifications_by_user(
        self, user_id: int, session: Session = None
    ) -> Sequence[RomVerification]:
        """Get all verifications for a specific user"""
        return session.scalars(
            select(RomVerification)
            .filter(RomVerification.user_id == user_id)
            .order_by(RomVerification.created_at.desc())
        ).all()

    @begin_session
    def get_verifications_by_user_and_status(
        self, user_id: int, status: VerificationStatus, session: Session = None
    ) -> Sequence[RomVerification]:
        """Get verifications for a specific user and status"""
        return session.scalars(
            select(RomVerification)
            .filter(
                RomVerification.user_id == user_id,
                RomVerification.status == status
            )
            .order_by(RomVerification.created_at.desc())
        ).all()

    @begin_session
    def get_verifications_by_status(
        self, status: VerificationStatus, session: Session = None
    ) -> Sequence[RomVerification]:
        """Get all verifications with a specific status"""
        return session.scalars(
            select(RomVerification)
            .filter(RomVerification.status == status)
            .order_by(RomVerification.created_at.desc())
        ).all()

    @begin_session
    def get_verifications_by_rom(
        self, rom_id: int, session: Session = None
    ) -> Sequence[RomVerification]:
        """Get all verifications for a specific ROM"""
        return session.scalars(
            select(RomVerification)
            .filter(RomVerification.rom_id == rom_id)
            .order_by(RomVerification.created_at.desc())
        ).all()

    @begin_session
    def update_verification(
        self, id: int, data: dict, session: Session = None
    ) -> RomVerification:
        """Update verification record"""
        session.execute(
            update(RomVerification)
            .where(RomVerification.id == id)
            .values(**data)
            .execution_options(synchronize_session="evaluate")
        )
        return session.query(RomVerification).filter_by(id=id).one()

    @begin_session
    def delete_verification(self, id: int, session: Session = None):
        """Delete verification record"""
        return session.execute(
            delete(RomVerification)
            .where(RomVerification.id == id)
            .execution_options(synchronize_session="evaluate")
        )

    @begin_session
    def get_expired_verifications(self, session: Session = None) -> Sequence[RomVerification]:
        """Get all expired verifications that are still pending"""
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        return session.scalars(
            select(RomVerification)
            .filter(
                RomVerification.status == VerificationStatus.PENDING,
                RomVerification.expires_at < now
            )
        ).all()

    @begin_session
    def mark_expired_verifications(self, session: Session = None) -> int:
        """Mark expired verifications as expired and return count of updated records"""
        expired_verifications = self.get_expired_verifications(session)
        
        for verification in expired_verifications:
            verification.mark_expired()
            session.merge(verification)
        
        session.commit()
        return len(expired_verifications)

    @begin_session
    def get_verification_stats(self, session: Session = None) -> dict:
        """Get verification statistics"""
        total = session.scalar(select(func.count(RomVerification.id)))
        pending = session.scalar(
            select(func.count(RomVerification.id))
            .filter(RomVerification.status == VerificationStatus.PENDING)
        )
        verified = session.scalar(
            select(func.count(RomVerification.id))
            .filter(RomVerification.status == VerificationStatus.VERIFIED)
        )
        rejected = session.scalar(
            select(func.count(RomVerification.id))
            .filter(RomVerification.status == VerificationStatus.REJECTED)
        )
        expired = session.scalar(
            select(func.count(RomVerification.id))
            .filter(RomVerification.status == VerificationStatus.EXPIRED)
        )
        
        return {
            "total": total or 0,
            "pending": pending or 0,
            "verified": verified or 0,
            "rejected": rejected or 0,
            "expired": expired or 0
        }
