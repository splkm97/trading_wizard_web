"""JWT token creation and validation."""

from datetime import datetime, timedelta

import jwt
from jwt.exceptions import InvalidTokenError

from src.core.config import settings
from src.core.exceptions import AuthenticationError


def create_access_token(user_id: str, fingerprint: str) -> str:
    """Create JWT access token.

    Args:
        user_id: User's UUID
        fingerprint: User's public key fingerprint

    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "fingerprint": fingerprint,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return token


def decode_access_token(token: str) -> dict:
    """Decode and validate JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict with 'sub' (user_id) and 'fingerprint'

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        user_id = payload.get("sub")
        fingerprint = payload.get("fingerprint")

        if not user_id or not fingerprint:
            raise AuthenticationError("Invalid token payload")

        return {"user_id": user_id, "fingerprint": fingerprint}

    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {e}")
