from datetime import datetime
from typing import NotRequired, TypedDict

from models.rom_verification import VerificationStatus

from .base import BaseModel


class RomVerificationSchema(BaseModel):
    """Schema for ROM verification responses"""
    id: int
    rom_id: int
    user_id: int
    status: VerificationStatus
    uploaded_file_name: str
    uploaded_file_size: int
    uploaded_md5_hash: str
    uploaded_sha1_hash: str
    verification_notes: str | None
    verified_at: datetime | None
    verified_by: int | None
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RomVerificationStatusSchema(BaseModel):
    """Schema for ROM verification status responses"""
    status: str
    message: str
    uploaded_at: datetime | None = None
    expires_at: datetime | None = None
    verified_at: datetime | None = None
    notes: str | None = None
    can_verify: bool | None = None
    is_expired: bool | None = None

    class Config:
        from_attributes = True


class PendingVerificationSchema(BaseModel):
    """Schema for pending verification responses (admin view)"""
    id: int
    rom_id: int
    rom_name: str
    platform: str
    user_id: int
    username: str
    uploaded_file_name: str
    uploaded_file_size: int
    uploaded_md5_hash: str
    uploaded_sha1_hash: str
    uploaded_at: datetime
    expires_at: datetime
    can_verify: bool
    is_expired: bool

    class Config:
        from_attributes = True


class VerifiedRomSchema(BaseModel):
    """Schema for verified ROM responses (user view)"""
    rom_id: int
    rom_name: str
    platform: str
    verified_at: datetime
    verifier: str | None
    notes: str | None

    class Config:
        from_attributes = True


class VerificationStatsSchema(BaseModel):
    """Schema for verification statistics"""
    total: int
    pending: int
    verified: int
    rejected: int
    expired: int

    class Config:
        from_attributes = True
