import hashlib
import tempfile
from pathlib import Path
from typing import Annotated

from decorators.auth import protected_route
from endpoints.responses.base import MessageResponse
from endpoints.responses.rom_verification import (
    PendingVerificationSchema,
    RomVerificationStatusSchema,
    VerifiedRomSchema,
    VerificationStatsSchema,
)
from fastapi import (
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from handler.database import db_rom_handler, db_rom_verification_handler
from handler.filesystem import fs_rom_handler
from logger.logger import log
from models.rom_verification import RomVerification, VerificationStatus
from utils.router import APIRouter

router = APIRouter(
    prefix="/rom-verification",
    tags=["rom-verification"],
)


@protected_route(
    router.post,
    "/upload/{rom_id}",
    [],
    status_code=status.HTTP_201_CREATED,
)
async def upload_rom_for_verification(
    request: Request,
    rom_id: int,
    background_tasks: BackgroundTasks,
    rom_file: UploadFile = File(...),
) -> MessageResponse:
    """Upload a ROM file for ownership verification
    
    Args:
        request: FastAPI request object
        rom_id: ID of the ROM to verify ownership for
        background_tasks: Background tasks for file processing
        rom_file: The ROM file to upload
        
    Returns:
        MessageResponse: Success/error message
    """
    user = request.auth.user
    
    # Check if ROM exists
    rom = db_rom_handler.get_rom(rom_id)
    if not rom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ROM not found"
        )
    
    # Check if user already has a verification for this ROM
    existing_verification = db_rom_verification_handler.get_verification_by_rom_and_user(
        rom_id, user.id
    )
    
    if existing_verification and existing_verification.status == VerificationStatus.VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ROM ownership already verified"
        )
    
    # Validate file type
    if not rom_file.filename.lower().endswith(rom.fs_extension.lower()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File must be a {rom.fs_extension} file"
        )
    
    # Save uploaded file temporarily and calculate hashes
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=rom.fs_extension) as temp_file:
            content = await rom_file.read()
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)
        
        # Calculate hashes
        md5_hash = hashlib.md5(content).hexdigest()
        sha1_hash = hashlib.sha1(content).hexdigest()
        
        # Create or update verification record
        verification_data = {
            "rom_id": rom_id,
            "user_id": user.id,
            "uploaded_file_name": rom_file.filename,
            "uploaded_file_size": len(content),
            "uploaded_md5_hash": md5_hash,
            "uploaded_sha1_hash": sha1_hash,
            "status": VerificationStatus.PENDING,
        }
        
        if existing_verification:
            # Update existing verification
            db_rom_verification_handler.update_verification(
                existing_verification.id, verification_data
            )
            verification = existing_verification
        else:
            # Create new verification
            verification = RomVerification(**verification_data)
            verification = db_rom_verification_handler.add_verification(verification)
        
        # Clean up temp file
        temp_file_path.unlink(missing_ok=True)
        
        log.info(
            f"ROM verification uploaded for user {user.username} - ROM: {rom.fs_name}"
        )
        
        return MessageResponse(
            message="ROM uploaded successfully for verification",
            data={"verification_id": verification.id}
        )
        
    except Exception as e:
        # Clean up temp file on error
        if 'temp_file_path' in locals():
            temp_file_path.unlink(missing_ok=True)
        log.error(f"Error uploading ROM for verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process uploaded file"
        )


@protected_route(
    router.get,
    "/status/{rom_id}",
    [],
    status_code=status.HTTP_200_OK,
)
async def get_verification_status(
    request: Request,
    rom_id: int,
) -> RomVerificationStatusSchema:
    """Get verification status for a specific ROM and user
    
    Args:
        request: FastAPI request object
        rom_id: ID of the ROM to check
        
    Returns:
        dict: Verification status information
    """
    user = request.auth.user
    
    verification = db_rom_verification_handler.get_verification_by_rom_and_user(
        rom_id, user.id
    )
    
    if not verification:
        return RomVerificationStatusSchema(
            status="none",
            message="No verification record found"
        )
    
    return RomVerificationStatusSchema(
        status=verification.status.value,
        message="Verification record found",
        uploaded_at=verification.created_at,
        expires_at=verification.expires_at,
        verified_at=verification.verified_at,
        notes=verification.verification_notes,
        can_verify=verification.can_verify,
        is_expired=verification.is_expired
    )


@protected_route(
    router.get,
    "/pending",
    [],
    status_code=status.HTTP_200_OK,
)
async def get_pending_verifications(
    request: Request,
) -> list[PendingVerificationSchema]:
    """Get all pending verifications (admin only)
    
    Args:
        request: FastAPI request object
        
    Returns:
        list: List of pending verifications
    """
    # Check if user is admin
    if request.auth.user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    pending_verifications = db_rom_verification_handler.get_verifications_by_status(
        VerificationStatus.PENDING
    )
    
    return [
        PendingVerificationSchema(
            id=v.id,
            rom_id=v.rom_id,
            rom_name=v.rom.fs_name,
            platform=v.rom.platform.name,
            user_id=v.user_id,
            username=v.user.username,
            uploaded_file_name=v.uploaded_file_name,
            uploaded_file_size=v.uploaded_file_size,
            uploaded_md5_hash=v.uploaded_md5_hash,
            uploaded_sha1_hash=v.uploaded_sha1_hash,
            uploaded_at=v.created_at,
            expires_at=v.expires_at,
            can_verify=v.can_verify,
            is_expired=v.is_expired
        )
        for v in pending_verifications
    ]


@protected_route(
    router.post,
    "/verify/{verification_id}",
    [],
    status_code=status.HTTP_200_OK,
)
async def verify_rom_ownership(
    request: Request,
    verification_id: int,
    approved: bool = Form(...),
    notes: str = Form(None),
) -> MessageResponse:
    """Verify or reject ROM ownership (admin only)
    
    Args:
        request: FastAPI request object
        verification_id: ID of the verification to process
        approved: Whether to approve or reject the verification
        notes: Optional notes about the verification
        
    Returns:
        MessageResponse: Success/error message
    """
    # Check if user is admin
    if request.auth.user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    verification = db_rom_verification_handler.get_verification(verification_id)
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification not found"
        )
    
    if not verification.can_verify:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification cannot be processed (expired or already processed)"
        )
    
    # Process verification
    if approved:
        # Check if uploaded ROM hash matches the master ROM hash
        rom = db_rom_handler.get_rom(verification.rom_id)
        if not rom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ROM not found"
            )
        
        # Compare hashes (check both MD5 and SHA1)
        hash_matches = (
            (rom.md5_hash and rom.md5_hash.lower() == verification.uploaded_md5_hash.lower()) or
            (rom.sha1_hash and rom.sha1_hash.lower() == verification.uploaded_sha1_hash.lower())
        )
        
        if hash_matches:
            verification.verify_ownership(request.auth.user.id, notes)
            message = "ROM ownership verified successfully"
        else:
            verification.reject_verification(request.auth.user.id, notes or "Hash mismatch")
            message = "ROM ownership verification rejected - hash mismatch"
    else:
        verification.reject_verification(request.auth.user.id, notes or "Rejected by admin")
        message = "ROM ownership verification rejected"
    
    # Update verification in database
    db_rom_verification_handler.update_verification(
        verification.id,
        {
            "status": verification.status,
            "verified_at": verification.verified_at,
            "verified_by": verification.verified_by,
            "verification_notes": verification.verification_notes
        }
    )
    
    log.info(
        f"ROM verification {verification.status.value} for user {verification.user.username} - ROM: {verification.rom.fs_name}"
    )
    
    return MessageResponse(message=message)


@protected_route(
    router.get,
    "/stats",
    [],
    status_code=status.HTTP_200_OK,
)
async def get_verification_stats(
    request: Request,
) -> VerificationStatsSchema:
    """Get verification statistics (admin only)
    
    Args:
        request: FastAPI request object
        
    Returns:
        VerificationStatsSchema: Verification statistics
    """
    # Check if user is admin
    if request.auth.user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    stats = db_rom_verification_handler.get_verification_stats()
    return VerificationStatsSchema(**stats)


@protected_route(
    router.get,
    "/my-verified",
    [],
    status_code=status.HTTP_200_OK,
)
async def get_my_verified_roms(
    request: Request,
) -> list[VerifiedRomSchema]:
    """Get all ROMs verified as owned by the current user
    
    Args:
        request: FastAPI request object
        
    Returns:
        list: List of verified ROMs
    """
    user = request.auth.user
    
    verified_roms = db_rom_verification_handler.get_verifications_by_user_and_status(
        user.id, VerificationStatus.VERIFIED
    )
    
    return [
        VerifiedRomSchema(
            rom_id=v.rom_id,
            rom_name=v.rom.fs_name,
            platform=v.rom.platform.name,
            verified_at=v.verified_at,
            verifier=v.verifier.username if v.verifier else None,
            notes=v.verification_notes
        )
        for v in verified_roms
    ]
