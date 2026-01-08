"""ECDSA P-256 cryptographic operations for PEM key authentication."""

import hashlib
import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
from cryptography.x509 import load_pem_x509_certificate

from src.core.exceptions import InvalidKeyError, InvalidSignatureError


def validate_public_key_pem(pem_data: str) -> ec.EllipticCurvePublicKey:
    """Validate and parse ECDSA P-256 public key from PEM format.

    Args:
        pem_data: Public key in PEM format

    Returns:
        Parsed public key object

    Raises:
        InvalidKeyError: If key is invalid or not ECDSA P-256
    """
    try:
        pem_bytes = pem_data.encode("utf-8")

        # Try loading as SPKI format (SubjectPublicKeyInfo)
        public_key = serialization.load_pem_public_key(pem_bytes, backend=default_backend())

        # Verify it's an EC key with P-256 curve
        if not isinstance(public_key, ec.EllipticCurvePublicKey):
            raise InvalidKeyError("Key is not an ECDSA key")

        if not isinstance(public_key.curve, ec.SECP256R1):
            raise InvalidKeyError("Key must use P-256 (secp256r1) curve")

        return public_key

    except ValueError as e:
        raise InvalidKeyError(f"Invalid PEM format: {e}")
    except Exception as e:
        raise InvalidKeyError(f"Failed to parse public key: {e}")


def compute_fingerprint(public_key_pem: str) -> str:
    """Compute SHA-256 fingerprint of a public key.

    Args:
        public_key_pem: Public key in PEM format

    Returns:
        64-character hex string (SHA-256 hash)
    """
    # Normalize the PEM data
    pem_bytes = public_key_pem.strip().encode("utf-8")

    # Hash the PEM data
    sha256 = hashlib.sha256(pem_bytes)

    return sha256.hexdigest()


def verify_signature(public_key_pem: str, challenge: bytes, signature: bytes) -> bool:
    """Verify ECDSA signature.

    Args:
        public_key_pem: Public key in PEM format
        challenge: Original challenge data
        signature: Signature to verify (DER format)

    Returns:
        True if signature is valid

    Raises:
        InvalidSignatureError: If signature verification fails
        InvalidKeyError: If public key is invalid
    """
    try:
        public_key = validate_public_key_pem(public_key_pem)

        # Verify signature
        public_key.verify(signature, challenge, ec.ECDSA(hashes.SHA256()))

        return True

    except InvalidSignature:
        raise InvalidSignatureError("Signature verification failed")
    except InvalidKeyError:
        raise
    except Exception as e:
        raise InvalidSignatureError(f"Signature verification error: {e}")


def verify_signature_base64(public_key_pem: str, challenge_b64: str, signature_b64: str) -> bool:
    """Verify ECDSA signature with base64-encoded inputs.

    Args:
        public_key_pem: Public key in PEM format
        challenge_b64: Base64-encoded challenge
        signature_b64: Base64-encoded signature

    Returns:
        True if signature is valid
    """
    try:
        challenge = base64.b64decode(challenge_b64)
        signature = base64.b64decode(signature_b64)
        return verify_signature(public_key_pem, challenge, signature)
    except Exception as e:
        raise InvalidSignatureError(f"Failed to decode base64 data: {e}")
