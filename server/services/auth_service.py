"""
Authentication service for JWT and API key management.
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server.config import settings
from server.models.user import User
from server.models.api_key import APIKey


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token (typically {"sub": user_id})
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_api_key() -> tuple[str, str]:
    """
    Generate a new API key.
    
    Returns:
        Tuple of (plain_text_key, key_hash)
        The plain text key should be shown to user once, then discarded.
        Only the hash should be stored in the database.
    """
    # Generate a random key with prefix
    random_part = secrets.token_urlsafe(32)
    plain_key = f"{settings.API_KEY_PREFIX}{random_part}"
    
    # Hash the key for storage
    key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    
    return plain_key, key_hash


async def validate_api_key(db: AsyncSession, api_key: str) -> Optional[User]:
    """
    Validate an API key and return the associated user.
    
    Args:
        db: Database session
        api_key: Plain text API key to validate
        
    Returns:
        User object if valid, None otherwise
    """
    # Hash the provided key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Query database for this key
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        )
    )
    api_key_record = result.scalar_one_or_none()
    
    if not api_key_record:
        return None
    
    # Check if expired
    if api_key_record.is_expired:
        return None
    
    # Update last used timestamp
    api_key_record.last_used_at = datetime.utcnow()
    await db.commit()
    
    return api_key_record.user


async def create_api_key_for_user(
    db: AsyncSession,
    user_id: str,
    name: Optional[str] = None,
    kb_id: Optional[str] = None,
    expires_in_days: Optional[int] = None
) -> tuple[APIKey, str]:
    """
    Create a new API key for a user.
    
    Args:
        db: Database session
        user_id: User ID to create key for
        name: Optional name/description for the key
        kb_id: Optional KB ID to scope the key to
        expires_in_days: Optional expiration in days
        
    Returns:
        Tuple of (APIKey record, plain_text_key)
    """
    plain_key, key_hash = generate_api_key()
    
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    api_key = APIKey(
        key_hash=key_hash,
        user_id=user_id,
        knowledge_base_id=kb_id,
        name=name,
        expires_at=expires_at
    )
    
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    return api_key, plain_key


async def revoke_api_key(db: AsyncSession, key_id: str, user_id: str) -> bool:
    """
    Revoke an API key.
    
    Args:
        db: Database session
        key_id: API key ID to revoke
        user_id: User ID (for authorization check)
        
    Returns:
        True if revoked successfully, False if not found
    """
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        return False
    
    api_key.is_active = False
    await db.commit()
    return True
