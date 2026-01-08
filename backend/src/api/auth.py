"""Authentication API endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.auth.crypto import validate_public_key_pem, compute_fingerprint, verify_signature_base64
from src.auth.jwt import create_access_token
from src.auth.challenge_store import challenge_store
from src.auth.middleware import get_current_user
from src.models.user import User
from src.models.user_settings import UserSettings
from src.models.portfolio import Portfolio
from src.core.exceptions import InvalidKeyError, InvalidSignatureError
from src.core.logging import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Request/Response models
class RegisterRequest(BaseModel):
    """Registration request with public key."""

    public_key: str = Field(..., description="ECDSA P-256 public key in PEM format")
    nickname: str | None = Field(None, max_length=50, description="Optional display nickname")


class RegisterResponse(BaseModel):
    """Registration response."""

    user_id: str
    fingerprint: str
    message: str


class ChallengeRequest(BaseModel):
    """Challenge request."""

    fingerprint: str = Field(..., min_length=64, max_length=64, description="Public key SHA-256 fingerprint")


class ChallengeResponse(BaseModel):
    """Challenge response."""

    challenge: str
    expires_at: str


class VerifyRequest(BaseModel):
    """Verification request with signed challenge."""

    fingerprint: str = Field(..., min_length=64, max_length=64)
    challenge: str = Field(..., description="Base64-encoded challenge")
    signature: str = Field(..., description="Base64-encoded signature")


class VerifyResponse(BaseModel):
    """Verification response with access token."""

    access_token: str
    token_type: str = "bearer"


class LogoutResponse(BaseModel):
    """Logout response."""

    message: str


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user with ECDSA P-256 public key.

    The public key must be in PEM format. A fingerprint (SHA-256 hash) is computed
    and used as the user identifier. No personal information is collected.
    """
    try:
        # Validate the public key format
        validate_public_key_pem(request.public_key)

        # Compute fingerprint
        fingerprint = compute_fingerprint(request.public_key)

        # Check if user already exists
        existing = db.query(User).filter(User.fingerprint == fingerprint).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this public key already exists",
            )

        # Create user
        user = User(
            public_key=request.public_key,
            fingerprint=fingerprint,
            nickname=request.nickname,
        )
        db.add(user)
        db.flush()  # Get the user ID

        # Create default settings
        settings = UserSettings(user_id=user.id)
        db.add(settings)

        # Create portfolio with default initial capital
        portfolio = Portfolio(user_id=user.id)
        db.add(portfolio)

        db.commit()

        logger.info(f"New user registered: {fingerprint[:16]}...")

        return RegisterResponse(
            user_id=user.id,
            fingerprint=fingerprint,
            message="Registration successful. Please save your private key securely.",
        )

    except InvalidKeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.message))


@router.post("/challenge", response_model=ChallengeResponse)
async def request_challenge(request: ChallengeRequest, db: Session = Depends(get_db)):
    """Request a challenge for signature-based login.

    The challenge must be signed with the user's private key and submitted
    to the /verify endpoint within 5 minutes.
    """
    # Check if user exists
    user = db.query(User).filter(User.fingerprint == request.fingerprint).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Create challenge
    challenge = challenge_store.create_challenge(request.fingerprint)
    expires_at = challenge_store.get_challenge_expiry(request.fingerprint)

    return ChallengeResponse(
        challenge=challenge,
        expires_at=expires_at.isoformat() if expires_at else "",
    )


@router.post("/verify", response_model=VerifyResponse)
async def verify_signature_endpoint(request: VerifyRequest, db: Session = Depends(get_db)):
    """Verify signature and issue access token.

    The client must sign the challenge received from /challenge with their
    private key and submit the signature here.
    """
    # Get user
    user = db.query(User).filter(User.fingerprint == request.fingerprint).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Verify challenge is valid and not expired
    if not challenge_store.verify_and_consume(request.fingerprint, request.challenge):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired challenge",
        )

    try:
        # Verify signature
        verify_signature_base64(user.public_key, request.challenge, request.signature)

        # Update last login
        user.update_last_login()
        db.commit()

        # Create access token
        token = create_access_token(user.id, user.fingerprint)

        logger.info(f"User logged in: {user.fingerprint[:16]}...")

        return VerifyResponse(access_token=token)

    except InvalidSignatureError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e.message))


@router.post("/logout", response_model=LogoutResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """Logout current user.

    This endpoint invalidates the current session. Since we use stateless JWT,
    the client should discard the token.
    """
    logger.info(f"User logged out: {current_user.fingerprint[:16]}...")

    return LogoutResponse(message="Logged out successfully")
