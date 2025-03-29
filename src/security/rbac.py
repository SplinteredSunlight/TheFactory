"""
Role-based access control (RBAC) for the AI-Orchestration-Platform.

This module provides RBAC functionality for the AI-Orchestration-Platform.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, Set, Union
from enum import Enum
from datetime import datetime, timedelta
from functools import wraps

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
SECRET_KEY = os.environ.get("SECRET_KEY", "insecure-secret-key-for-development-only")
RBAC_CONFIG_FILE = os.environ.get("RBAC_CONFIG_FILE", "config/rbac_config.json")


# Models
class Role(str, Enum):
    """Role enum."""
    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    GUEST = "guest"


class Permission(str, Enum):
    """Permission enum."""
    # Workflow permissions
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_UPDATE = "workflow:update"
    WORKFLOW_DELETE = "workflow:delete"
    WORKFLOW_EXECUTE = "workflow:execute"
    
    # Task permissions
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    TASK_EXECUTE = "task:execute"
    
    # Agent permissions
    AGENT_CREATE = "agent:create"
    AGENT_READ = "agent:read"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    AGENT_EXECUTE = "agent:execute"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_READ = "system:read"
    SYSTEM_UPDATE = "system:update"
    
    # Monitoring permissions
    MONITORING_READ = "monitoring:read"
    MONITORING_UPDATE = "monitoring:update"
    
    # Progress permissions
    PROGRESS_READ = "progress:read"
    PROGRESS_UPDATE = "progress:update"


class User(BaseModel):
    """User model."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    roles: List[Role] = [Role.GUEST]


class UserInDB(User):
    """User in database model."""
    hashed_password: str


class Token(BaseModel):
    """Token model."""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None
    roles: List[Role] = []
    permissions: List[Permission] = []
    exp: Optional[int] = None


# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# RBAC configuration
class RBACConfig:
    """RBAC configuration."""
    
    def __init__(self, config_file: str = RBAC_CONFIG_FILE):
        """
        Initialize RBAC configuration.
        
        Args:
            config_file: Path to RBAC configuration file
        """
        self.config_file = config_file
        self.role_permissions: Dict[Role, List[Permission]] = {}
        self.users: Dict[str, UserInDB] = {}
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Load RBAC configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                
                # Load role permissions
                for role_name, permissions in config.get("role_permissions", {}).items():
                    try:
                        role = Role(role_name)
                        self.role_permissions[role] = [Permission(p) for p in permissions]
                    except ValueError:
                        logger.warning(f"Invalid role or permission: {role_name}, {permissions}")
                
                # Load users
                for username, user_data in config.get("users", {}).items():
                    try:
                        roles = [Role(r) for r in user_data.get("roles", ["guest"])]
                        self.users[username] = UserInDB(
                            username=username,
                            email=user_data.get("email"),
                            full_name=user_data.get("full_name"),
                            disabled=user_data.get("disabled", False),
                            roles=roles,
                            hashed_password=user_data.get("hashed_password", "")
                        )
                    except ValueError:
                        logger.warning(f"Invalid user data: {username}, {user_data}")
            else:
                # Create default configuration
                self._create_default_config()
        except Exception as e:
            logger.error(f"Error loading RBAC configuration: {e}")
            # Create default configuration
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default RBAC configuration."""
        # Default role permissions
        self.role_permissions = {
            Role.ADMIN: [p for p in Permission],
            Role.USER: [
                Permission.WORKFLOW_READ,
                Permission.WORKFLOW_EXECUTE,
                Permission.TASK_READ,
                Permission.TASK_EXECUTE,
                Permission.AGENT_READ,
                Permission.MONITORING_READ,
                Permission.PROGRESS_READ,
            ],
            Role.AGENT: [
                Permission.WORKFLOW_READ,
                Permission.WORKFLOW_EXECUTE,
                Permission.TASK_READ,
                Permission.TASK_EXECUTE,
                Permission.AGENT_READ,
                Permission.PROGRESS_UPDATE,
            ],
            Role.SYSTEM: [
                Permission.WORKFLOW_READ,
                Permission.WORKFLOW_EXECUTE,
                Permission.TASK_READ,
                Permission.TASK_EXECUTE,
                Permission.AGENT_READ,
                Permission.SYSTEM_READ,
                Permission.MONITORING_READ,
                Permission.PROGRESS_READ,
            ],
            Role.GUEST: [
                Permission.WORKFLOW_READ,
                Permission.TASK_READ,
                Permission.AGENT_READ,
                Permission.MONITORING_READ,
                Permission.PROGRESS_READ,
            ],
        }
        
        # Default admin user
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin")
        self.users = {
            "admin": UserInDB(
                username="admin",
                email="admin@example.com",
                full_name="Admin User",
                disabled=False,
                roles=[Role.ADMIN],
                hashed_password=pwd_context.hash(admin_password)
            )
        }
        
        # Save default configuration
        self._save_config()
    
    def _save_config(self):
        """Save RBAC configuration to file."""
        try:
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Prepare configuration
            config = {
                "role_permissions": {
                    role.value: [p.value for p in permissions]
                    for role, permissions in self.role_permissions.items()
                },
                "users": {
                    user.username: {
                        "email": user.email,
                        "full_name": user.full_name,
                        "disabled": user.disabled,
                        "roles": [r.value for r in user.roles],
                        "hashed_password": user.hashed_password
                    }
                    for user in self.users.values()
                }
            }
            
            # Save configuration
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving RBAC configuration: {e}")
    
    def get_user_permissions(self, user: User) -> Set[Permission]:
        """
        Get permissions for a user.
        
        Args:
            user: User
            
        Returns:
            Set of permissions
        """
        permissions = set()
        
        # Add permissions for each role
        for role in user.roles:
            if role in self.role_permissions:
                permissions.update(self.role_permissions[role])
        
        return permissions
    
    def has_permission(self, user: User, permission: Permission) -> bool:
        """
        Check if a user has a permission.
        
        Args:
            user: User
            permission: Permission
            
        Returns:
            True if the user has the permission, False otherwise
        """
        # Get user permissions
        user_permissions = self.get_user_permissions(user)
        
        # Check if the user has the permission
        return permission in user_permissions
    
    def add_user(self, user: UserInDB) -> bool:
        """
        Add a user.
        
        Args:
            user: User
            
        Returns:
            True if the user was added, False otherwise
        """
        try:
            # Add user
            self.users[user.username] = user
            
            # Save configuration
            self._save_config()
            
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def update_user(self, user: UserInDB) -> bool:
        """
        Update a user.
        
        Args:
            user: User
            
        Returns:
            True if the user was updated, False otherwise
        """
        try:
            # Check if the user exists
            if user.username not in self.users:
                return False
            
            # Update user
            self.users[user.username] = user
            
            # Save configuration
            self._save_config()
            
            return True
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    def delete_user(self, username: str) -> bool:
        """
        Delete a user.
        
        Args:
            username: Username
            
        Returns:
            True if the user was deleted, False otherwise
        """
        try:
            # Check if the user exists
            if username not in self.users:
                return False
            
            # Delete user
            del self.users[username]
            
            # Save configuration
            self._save_config()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    def get_user(self, username: str) -> Optional[UserInDB]:
        """
        Get a user.
        
        Args:
            username: Username
            
        Returns:
            User or None if not found
        """
        return self.users.get(username)


# Create RBAC configuration
rbac_config = RBACConfig()


# Authentication functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password.
    
    Args:
        plain_password: Plain password
        hashed_password: Hashed password
        
    Returns:
        True if the password is correct, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Get password hash.
    
    Args:
        password: Password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate a user.
    
    Args:
        username: Username
        password: Password
        
    Returns:
        User if authentication is successful, None otherwise
    """
    user = rbac_config.get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create an access token.
    
    Args:
        data: Token data
        expires_delta: Expiration time
        
    Returns:
        Access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a refresh token.
    
    Args:
        data: Token data
        expires_delta: Expiration time
        
    Returns:
        Refresh token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user.
    
    Args:
        token: Access token
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(
            username=username,
            roles=[Role(r) for r in payload.get("roles", [])],
            permissions=[Permission(p) for p in payload.get("permissions", [])],
            exp=payload.get("exp")
        )
    except JWTError:
        raise credentials_exception
    user = rbac_config.get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: Current user
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If the user is disabled
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def has_permission(permission: Permission):
    """
    Decorator to check if a user has a permission.
    
    Args:
        permission: Permission
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_active_user), **kwargs):
            if not rbac_config.has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def has_role(role: Role):
    """
    Decorator to check if a user has a role.
    
    Args:
        role: Role
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_active_user), **kwargs):
            if role not in current_user.roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
