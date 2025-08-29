from enum import Enum
from typing import List, Optional, Annotated
from fastapi import Depends, HTTPException, status
from functools import wraps
from authentication import get_current_user
from sqlalchemy.orm import Session
from database import SessionLocal
import models

class Role(str, Enum):
    """User roles enumeration"""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    GUEST = "guest"

class Permission(str, Enum):
    """Permission enumeration"""
    READ_USERS = "read_users"
    WRITE_USERS = "write_users"
    DELETE_USERS = "delete_users"
    READ_OWN_DATA = "read_own_data"
    WRITE_OWN_DATA = "write_own_data"
    MODERATE_CONTENT = "moderate_content"
    ADMIN_ACCESS = "admin_access"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.READ_USERS,
        Permission.WRITE_USERS,
        Permission.DELETE_USERS,
        Permission.READ_OWN_DATA,
        Permission.WRITE_OWN_DATA,
        Permission.MODERATE_CONTENT,
        Permission.ADMIN_ACCESS
    ],
    Role.MODERATOR: [
        Permission.READ_USERS,
        Permission.READ_OWN_DATA,
        Permission.WRITE_OWN_DATA,
        Permission.MODERATE_CONTENT
    ],
    Role.USER: [
        Permission.READ_OWN_DATA,
        Permission.WRITE_OWN_DATA
    ],
    Role.GUEST: [
        Permission.READ_OWN_DATA
    ]
}

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class AuthorizationService:
    """Service class for handling authorization logic"""
    
    @staticmethod
    def get_user_role(user_id: int, db: Session) -> Role:
        """Get user role from database"""
        user = db.query(models.Users).filter(models.Users.id == user_id).first()
        if not user:
            return Role.GUEST
        
        # If you haven't added role field to your Users model yet,
        # this will default to USER role. You can modify this logic
        # once you add the role field to your database model.
        return getattr(user, 'role', Role.USER)
    
    @staticmethod
    def user_has_permission(user_role: Role, required_permission: Permission) -> bool:
        """Check if user role has the required permission"""
        user_permissions = ROLE_PERMISSIONS.get(user_role, [])
        return required_permission in user_permissions
    
    @staticmethod
    def user_can_access_resource(current_user_id: int, resource_user_id: int, 
                               user_role: Role) -> bool:
        """Check if user can access a specific resource"""
        # Users can always access their own resources
        if current_user_id == resource_user_id:
            return True
        
        # Admins and moderators can access other users' resources
        if user_role in [Role.ADMIN, Role.MODERATOR]:
            return True
        
        return False

def require_permission(required_permission: Permission):
    """Decorator to require specific permission for endpoint access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user and db from kwargs (they should be injected by FastAPI)
            user = None
            db = None
            
            for key, value in kwargs.items():
                if key == 'user' and isinstance(value, dict):
                    user = value
                elif key == 'db' and isinstance(value, Session):
                    db = value
            
            if not user or not db:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = AuthorizationService.get_user_role(user['id'], db)
            
            if not AuthorizationService.user_has_permission(user_role, required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{required_permission.value}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(required_roles: List[Role]):
    """Decorator to require specific roles for endpoint access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user and db from kwargs
            user = None
            db = None
            
            for key, value in kwargs.items():
                if key == 'user' and isinstance(value, dict):
                    user = value
                elif key == 'db' and isinstance(value, Session):
                    db = value
            
            if not user or not db:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = AuthorizationService.get_user_role(user['id'], db)
            
            if user_role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these roles required: {[role.value for role in required_roles]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

async def get_current_user_with_role(
    user: Annotated[dict, Depends(get_current_user)],
    db: db_dependency
) -> dict:
    """Get current user with their role information"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    user_role = AuthorizationService.get_user_role(user['id'], db)
    
    return {
        **user,
        "role": user_role.value,
        "permissions": [perm.value for perm in ROLE_PERMISSIONS.get(user_role, [])]
    }

def check_resource_access(resource_user_id: int):
    """Dependency to check if user can access a specific resource"""
    def _check_access(
        user: Annotated[dict, Depends(get_current_user)],
        db: db_dependency
    ):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user_role = AuthorizationService.get_user_role(user['id'], db)
        
        if not AuthorizationService.user_can_access_resource(
            user['id'], resource_user_id, user_role
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this resource"
            )
        
        return user
    
    return _check_access

# Convenience dependencies for common permission checks
async def require_admin_access(
    user: Annotated[dict, Depends(get_current_user)],
    db: db_dependency
):
    """Require admin access"""
    user_role = AuthorizationService.get_user_role(user['id'], db)
    if not AuthorizationService.user_has_permission(user_role, Permission.ADMIN_ACCESS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

async def require_moderator_access(
    user: Annotated[dict, Depends(get_current_user)],
    db: db_dependency
):
    """Require moderator access or higher"""
    user_role = AuthorizationService.get_user_role(user['id'], db)
    if user_role not in [Role.ADMIN, Role.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator access or higher required"
        )
    return user