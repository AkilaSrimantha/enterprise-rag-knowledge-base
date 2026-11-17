from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_token
from app.schemas.models import UserResponse, UserRole

security_scheme = HTTPBearer(auto_error=False)

MOCK_USERS = {}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> UserResponse:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("sub", "")
    role_str = payload.get("role", "viewer")
    user_id = payload.get("user_id", "usr-custom")

    try:
        user_role = UserRole(role_str)
    except Exception:
        user_role = UserRole.VIEWER

    return UserResponse(
        id=user_id,
        email=email,
        full_name=email.split("@")[0].capitalize(),
        role=user_role,
        is_active=True
    )


def require_role(allowed_roles: List[UserRole]):
    """
    Enforces Role-Based Access Control (RBAC).
    Admin automatically inherits all lower role permissions.
    """
    async def role_checker(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        # Admin has superuser access to all routes
        if current_user.role == UserRole.ADMIN:
            return current_user

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {[r.value for r in allowed_roles]}, your role: {current_user.role.value}"
            )
        return current_user

    return role_checker
