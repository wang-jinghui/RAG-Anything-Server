"""
Authentication middleware for FastAPI.
"""
from fastapi import Request, HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from functools import wraps

from server.services.auth_service import decode_token, validate_api_key
from server.models.user import User
from server.models.database import get_db_session


# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Authentication dependency that validates JWT tokens or API keys.
    
    Supports dual authentication:
    1. JWT tokens via Authorization: Bearer <token> header
    2. API keys via X-API-Key header
    
    Args:
        request: FastAPI request object
        credentials: Optional HTTP bearer credentials
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get database session from dependency instead of request.state
    # db: AsyncSession = request.state.db
    
    # Try API key first (from X-API-Key header)
    api_key = request.headers.get("X-API-Key")
    if api_key:
        user = await validate_api_key(db, api_key)
        if user:
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive"
                )
            request.state.user = user
            request.state.auth_method = "api_key"
            return user
    
    # Try JWT token
    if credentials:
        try:
            payload = decode_token(credentials.credentials)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
            
            # Check token type
            token_type = payload.get("type")
            if token_type != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Get user from database
            from sqlalchemy import select
            from server.models.user import User
            
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            request.state.user = user
            request.state.auth_method = "jwt"
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication error: {str(e)}"
            )
    
    # No authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either Bearer token or X-API-Key header."
    )


def require_super_admin(func):
    """
    Decorator to require super admin access for an endpoint.
    
    Usage:
        @router.delete("/admin/users/{user_id}")
        @require_super_admin
        async def admin_delete_user(user_id: UUID, current_user: User = Depends(get_current_user)):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract current_user from kwargs or request state
        current_user = None
        
        # Try to get from kwargs first
        if 'current_user' in kwargs:
            current_user = kwargs['current_user']
        else:
            # Try to get from request state
            for arg in args:
                if isinstance(arg, Request) and hasattr(arg.state, 'user'):
                    current_user = arg.state.user
                    break
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if not current_user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin access required"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper


async def get_optional_user(request: Request) -> Optional[User]:
    """
    Optional authentication dependency - returns user if authenticated, None otherwise.
    
    Useful for endpoints that work differently for authenticated vs anonymous users.
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None
