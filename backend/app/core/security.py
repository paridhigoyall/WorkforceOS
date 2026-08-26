from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from passlib.context import CryptContext

# CryptContext for password hashing and verification using bcrypt
# Passlib handles bcrypt under the hood
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
# Retrieve configurations from environment variables with sensible defaults for local development
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-dev-secret-key-replace-in-production-with-a-secure-32-byte-hex-string")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against its bcrypt hashed counterpart."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash of a plain text password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.
    
    * ``data`` – key-value pairs to encode in the JWT payload (e.g. sub, role).
    * ``expires_delta`` – optional override for default expiration duration.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Standard JWT Claims:
    # sub - subject (typically user ID as string)
    # exp - expiration time
    # iat - issued at time
    # nbf - not before time
    # type - token type classifier
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "type": "access"
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token.
    
    * ``data`` – key-value pairs to encode in the JWT payload (typically sub).
    * ``expires_delta`` – optional override for default expiration duration.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "type": "refresh"
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


import pyotp

# MFA / TOTP Configuration
MFA_ISSUER_NAME = os.getenv("MFA_ISSUER_NAME", "WorkforceOS")
MFA_CHALLENGE_EXPIRE_MINUTES = int(os.getenv("MFA_CHALLENGE_EXPIRE_MINUTES", "5"))


def generate_mfa_secret() -> str:
    """Generate a cryptographically random base32 TOTP secret key."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    """Generate an otpauth:// provisioning URI for QR code generation."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=MFA_ISSUER_NAME)


def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code against a base32 secret.
    
    Includes a 1-step window (±30s) to handle minor clock skew.
    """
    if not secret or not code:
        return False
    # Remove any whitespaces
    sanitized_code = code.strip().replace(" ", "")
    if len(sanitized_code) != 6 or not sanitized_code.isdigit():
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(sanitized_code, valid_window=1)


def create_mfa_challenge_token(data: Dict[str, Any]) -> str:
    """Create a short-lived temporary token for completing the 2FA login challenge."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=MFA_CHALLENGE_EXPIRE_MINUTES)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "type": "mfa_challenge"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT.
    
    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If token signature or structure is invalid.
    """
    # jwt.decode automatically validates expiration ('exp'), issued at ('iat'), and not before ('nbf')
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

