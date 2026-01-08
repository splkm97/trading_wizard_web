"""In-memory challenge store with TTL for authentication."""

from __future__ import annotations

import secrets
import base64
from datetime import datetime, timedelta
from threading import Lock


class ChallengeStore:
    """Thread-safe in-memory store for authentication challenges."""

    def __init__(self, ttl_seconds: int = 300):
        """Initialize challenge store.

        Args:
            ttl_seconds: Time-to-live for challenges in seconds (default: 5 minutes)
        """
        self._challenges: dict[str, tuple[str, datetime]] = {}
        self._lock = Lock()
        self._ttl = timedelta(seconds=ttl_seconds)

    def create_challenge(self, fingerprint: str) -> str:
        """Create a new challenge for a fingerprint.

        Args:
            fingerprint: User's public key fingerprint

        Returns:
            Base64-encoded challenge string
        """
        # Generate 32 random bytes
        challenge_bytes = secrets.token_bytes(32)
        challenge_b64 = base64.b64encode(challenge_bytes).decode("utf-8")

        expires_at = datetime.utcnow() + self._ttl

        with self._lock:
            # Clean up expired challenges first
            self._cleanup()
            # Store the new challenge
            self._challenges[fingerprint] = (challenge_b64, expires_at)

        return challenge_b64

    def verify_and_consume(self, fingerprint: str, challenge: str) -> bool:
        """Verify challenge and remove it (single-use).

        Args:
            fingerprint: User's public key fingerprint
            challenge: Challenge string to verify

        Returns:
            True if challenge is valid and not expired
        """
        with self._lock:
            stored = self._challenges.get(fingerprint)

            if not stored:
                return False

            stored_challenge, expires_at = stored

            # Remove the challenge regardless (single-use)
            del self._challenges[fingerprint]

            # Check expiration
            if datetime.utcnow() > expires_at:
                return False

            # Check match
            return secrets.compare_digest(stored_challenge, challenge)

    def get_challenge_expiry(self, fingerprint: str) -> datetime | None:
        """Get expiry time for a challenge if it exists."""
        with self._lock:
            stored = self._challenges.get(fingerprint)
            if stored:
                return stored[1]
            return None

    def _cleanup(self):
        """Remove expired challenges. Must be called with lock held."""
        now = datetime.utcnow()
        expired = [fp for fp, (_, exp) in self._challenges.items() if now > exp]
        for fp in expired:
            del self._challenges[fp]


# Global challenge store instance
challenge_store = ChallengeStore(ttl_seconds=300)  # 5 minute TTL
