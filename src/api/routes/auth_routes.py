"""
Authentication routes for the AI-Orchestration-Platform.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any, List, Optional
from datetime import timedelta

from src.security.rbac import (
    User,
    UserInDB,
    Token,
    Role,
    Permission,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    get_password_hash,
    rbac_config,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    has_permission,
    has_role
)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}},
)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Get an access token.
    
    Args:
        form_data: OAuth2 password request form
        
    Returns:
        Access token
        
    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user permissions
    permissions = rbac_config.get_user_permissions(user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "roles": [role.value for role in user.roles],
            "permissions": [permission.value for permission in permissions]
        },
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.username},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """
    Refresh an access token.
    
    Args:
        refresh_token: Refresh token
        
    Returns:
        New access token
        
    Raises:
        HTTPException: If the refresh token is invalid
    """
    try:
        # Decode refresh token
        from jose import jwt
        from src.security.rbac import SECRET_KEY, ALGORITHM
        
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user
        user = rbac_config.get_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user permissions
        permissions = rbac_config.get_user_permissions(user)
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "roles": [role.value for role in user.roles],
                "permissions": [permission.value for permission in permissions]
            },
            expires_delta=access_token_expires
        )
        
        # Create new refresh token
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        new_refresh_token = create_refresh_token(
            data={"sub": user.username},
            expires_delta=refresh_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_token": new_refresh_token
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get the current user.
    
    Args:
        current_user: Current user
        
    Returns:
        Current user
    """
    return current_user


@router.get("/users", response_model=List[User])
@has_permission(Permission.SYSTEM_ADMIN)
async def read_users(current_user: User = Depends(get_current_active_user)):
    """
    Get all users.
    
    Args:
        current_user: Current user
        
    Returns:
        List of users
    """
    return list(rbac_config.users.values())


@router.post("/users", response_model=User)
@has_permission(Permission.SYSTEM_ADMIN)
async def create_user(
    username: str,
    password: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    roles: List[Role] = [Role.USER],
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new user.
    
    Args:
        username: Username
        password: Password
        email: Email
        full_name: Full name
        roles: Roles
        current_user: Current user
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If the user already exists
    """
    # Check if the user already exists
    if rbac_config.get_user(username) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Create user
    user = UserInDB(
        username=username,
        email=email,
        full_name=full_name,
        roles=roles,
        hashed_password=get_password_hash(password)
    )
    
    # Add user
    if not rbac_config.add_user(user):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding user"
        )
    
    return user


@router.put("/users/{username}", response_model=User)
@has_permission(Permission.SYSTEM_ADMIN)
async def update_user(
    username: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    roles: Optional[List[Role]] = None,
    disabled: Optional[bool] = None,
    password: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a user.
    
    Args:
        username: Username
        email: Email
        full_name: Full name
        roles: Roles
        disabled: Disabled
        password: Password
        current_user: Current user
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: If the user does not exist
    """
    # Get user
    user = rbac_config.get_user(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user
    if email is not None:
        user.email = email
    if full_name is not None:
        user.full_name = full_name
    if roles is not None:
        user.roles = roles
    if disabled is not None:
        user.disabled = disabled
    if password is not None:
        user.hashed_password = get_password_hash(password)
    
    # Update user
    if not rbac_config.update_user(user):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user"
        )
    
    return user


@router.delete("/users/{username}")
@has_permission(Permission.SYSTEM_ADMIN)
async def delete_user(
    username: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a user.
    
    Args:
        username: Username
        current_user: Current user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If the user does not exist or cannot be deleted
    """
    # Check if the user exists
    if rbac_config.get_user(username) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if the user is trying to delete themselves
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    # Delete user
    if not rbac_config.delete_user(username):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting user"
        )
    
    return {"message": "User deleted"}


@router.get("/roles", response_model=Dict[str, List[str]])
@has_permission(Permission.SYSTEM_READ)
async def get_roles(current_user: User = Depends(get_current_active_user)):
    """
    Get all roles and their permissions.
    
    Args:
        current_user: Current user
        
    Returns:
        Dictionary of roles and their permissions
    """
    return {
        role.value: [permission.value for permission in permissions]
        for role, permissions in rbac_config.role_permissions.items()
    }


@router.get("/permissions", response_model=List[str])
@has_permission(Permission.SYSTEM_READ)
async def get_permissions(current_user: User = Depends(get_current_active_user)):
    """
    Get all permissions.
    
    Args:
        current_user: Current user
        
    Returns:
        List of permissions
    """
    return [permission.value for permission in Permission]
