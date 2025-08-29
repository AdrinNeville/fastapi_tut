from fastapi import FastAPI, status, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.requests import Request
import models
from database import engine, SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
import authentication
from authentication import get_current_user
from authorisation import (
    require_permission, 
    require_role, 
    get_current_user_with_role,
    require_admin_access,
    require_moderator_access,
    check_resource_access,
    Permission,
    Role
)

app = FastAPI()
app.include_router(authentication.router)

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "error": str(e)},
        )

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@app.get("/", status_code=status.HTTP_200_OK)
async def read_root():
    return {"message": "Welcome to the FastAPI application!"}

@app.get("/users/me", status_code=status.HTTP_200_OK)
async def get_current_user_info(user: Annotated[dict, Depends(get_current_user_with_role)]):
    """Get current user information with role and permissions"""
    return {"user": user}

@app.get("/users", status_code=status.HTTP_200_OK)
async def get_all_users(user: user_dependency, db: db_dependency):
    """Get all users - requires READ_USERS permission"""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    # Check if user has permission to read all users
    from authorisation import AuthorizationService, Permission
    user_role = AuthorizationService.get_user_role(user['id'], db)
    
    if not AuthorizationService.user_has_permission(user_role, Permission.READ_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission to read users required"
        )
    
    users = db.query(models.Users).all()
    return {"users": [{"id": u.id, "username": u.username, "role": u.role.value} for u in users]}

@app.get("/users/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_by_id(user_id: int, user: user_dependency, db: db_dependency):
    """Get user by ID - users can access their own data, admins/moderators can access others"""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    # Check resource access
    from authorisation import AuthorizationService
    user_role = AuthorizationService.get_user_role(user['id'], db)
    
    if not AuthorizationService.user_can_access_resource(user['id'], user_id, user_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this resource"
        )
    
    db_user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": db_user.id, 
        "username": db_user.username, 
        "role": db_user.role.value
    }

@app.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: int, admin_user: Annotated[dict, Depends(require_admin_access)], db: db_dependency):
    """Delete user - requires admin access"""
    db_user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if db_user.id == admin_user['id']:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    db.delete(db_user)
    db.commit()
    
    return {"message": f"User {db_user.username} deleted successfully"}

@app.get("/admin/stats", status_code=status.HTTP_200_OK)
async def get_admin_stats(admin_user: Annotated[dict, Depends(require_admin_access)], db: db_dependency):
    """Get admin statistics - requires admin access"""
    total_users = db.query(models.Users).count()
    admin_count = db.query(models.Users).filter(models.Users.role == models.RoleEnum.ADMIN).count()
    user_count = db.query(models.Users).filter(models.Users.role == models.RoleEnum.USER).count()
    moderator_count = db.query(models.Users).filter(models.Users.role == models.RoleEnum.MODERATOR).count()
    
    return {
        "total_users": total_users,
        "admin_count": admin_count,
        "user_count": user_count,
        "moderator_count": moderator_count
    }

@app.get("/moderator/dashboard", status_code=status.HTTP_200_OK)
async def get_moderator_dashboard(moderator_user: Annotated[dict, Depends(require_moderator_access)], db: db_dependency):
    """Get moderator dashboard - requires moderator access or higher"""
    return {"message": "Welcome to moderator dashboard", "user": moderator_user}

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}