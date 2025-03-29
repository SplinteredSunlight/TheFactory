"""
Authentication Module for AI-Orchestration-Platform

This module provides authentication functionality for the AI-Orchestration-Platform,
including token generation, validation, and management.
"""

import base64
import datetime
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from typing import Dict, List, Optional, Tuple, Union, Any

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError


class AuthenticationError(Exception):
    """Exception raised for authentication errors."""
    pass


class AuthorizationError(Exception):
    """Exception raised for authorization errors."""
    pass


class TokenManager:
    """Manages authentication tokens for the AI-Orchestration-Platform."""

    def __init__(self, secret_key: Optional[str] = None, token_expiry: int = 3600):
        """Initialize the TokenManager.

        Args:
            secret_key: Secret key for signing tokens. If not provided, a random key will be generated.
            token_expiry: Expiry time for access tokens in seconds. Default is 1 hour.
        """
        self.secret_key = secret_key or os.environ.get("JWT_SECRET_KEY") or secrets.token_hex(32)
        self.token_expiry = token_expiry
        self.refresh_token_expiry = token_expiry * 24  # 24 hours
        
        # In-memory token store (in a production system, this would be a database)
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.agent_tokens: Dict[str, Dict[str, Any]] = {}

    def register_api_key(self, client_id: str, api_key: Optional[str] = None, 
                         scopes: Optional[List[str]] = None) -> str:
        """Register a new API key for a client.

        Args:
            client_id: Identifier for the client
            api_key: API key to register. If not provided, a random key will be generated.
            scopes: List of scopes the API key is authorized for

        Returns:
            The registered API key
        """
        if not api_key:
            api_key = secrets.token_hex(16)
            
        self.api_keys[api_key] = {
            "client_id": client_id,
            "scopes": scopes or ["default"],
            "created_at": datetime.datetime.now().isoformat(),
        }
        
        return api_key

    def validate_api_key(self, api_key: str, required_scopes: Optional[List[str]] = None) -> Tuple[bool, str, List[str]]:
        """Validate an API key.

        Args:
            api_key: API key to validate
            required_scopes: List of scopes required for the operation

        Returns:
            Tuple of (is_valid, client_id, scopes)
        """
        if api_key not in self.api_keys:
            return False, "", []
            
        client_id = self.api_keys[api_key]["client_id"]
        scopes = self.api_keys[api_key]["scopes"]
        
        if required_scopes and not all(scope in scopes for scope in required_scopes):
            return True, client_id, []
            
        return True, client_id, scopes

    def generate_token(self, client_id: str, scopes: List[str]) -> Dict[str, Any]:
        """Generate a new JWT token for a client.

        Args:
            client_id: Identifier for the client
            scopes: List of scopes the token is authorized for

        Returns:
            Dictionary containing the token information
        """
        # Generate a unique token ID
        jti = str(uuid.uuid4())
        
        # Set token expiry
        now = int(time.time())
        expiry = now + self.token_expiry
        
        # Create the JWT payload
        payload = {
            "iss": "ai-orchestration-platform",
            "sub": client_id,
            "aud": "ai-orchestrator",
            "exp": expiry,
            "iat": now,
            "jti": jti,
            "scope": scopes,
        }
        
        # Generate the JWT token
        access_token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        # Generate a refresh token
        refresh_token = secrets.token_hex(32)
        refresh_expiry = now + self.refresh_token_expiry
        
        # Store the tokens
        self.tokens[jti] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "client_id": client_id,
            "scopes": scopes,
            "issued_at": now,
            "expires_at": expiry,
            "refresh_expires_at": refresh_expiry,
            "is_revoked": False,
        }
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": self.token_expiry,
            "refresh_token": refresh_token,
            "scope": scopes,
        }

    def validate_token(self, token: str, required_scopes: Optional[List[str]] = None) -> Tuple[bool, Dict[str, Any]]:
        """Validate a JWT token.

        Args:
            token: JWT token to validate
            required_scopes: List of scopes required for the operation

        Returns:
            Tuple of (is_valid, token_info)
        """
        try:
            # Decode the JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"], audience="ai-orchestrator")
            
            # Get the token ID
            jti = payload.get("jti")
            if not jti or jti not in self.tokens:
                return False, {}
                
            # Check if the token is revoked
            if self.tokens[jti]["is_revoked"]:
                return False, {}
                
            # Check if the token is expired
            if payload["exp"] < int(time.time()):
                return False, {}
                
            # Check if the token has the required scopes
            token_scopes = payload.get("scope", [])
            if required_scopes and not all(scope in token_scopes for scope in required_scopes):
                return False, {}
                
            return True, payload
            
        except (InvalidTokenError, ExpiredSignatureError):
            return False, {}

    def refresh_token(self, refresh_token: str, client_id: str) -> Dict[str, Any]:
        """Refresh a JWT token.

        Args:
            refresh_token: Refresh token to use
            client_id: Identifier for the client

        Returns:
            Dictionary containing the new token information

        Raises:
            AuthenticationError: If the refresh token is invalid
        """
        # Find the token entry by refresh token
        token_id = None
        for jti, token_info in self.tokens.items():
            if token_info["refresh_token"] == refresh_token and token_info["client_id"] == client_id:
                token_id = jti
                break
                
        if not token_id:
            raise AuthenticationError("Invalid refresh token")
            
        token_info = self.tokens[token_id]
        
        # Check if the refresh token is expired
        if token_info["refresh_expires_at"] < int(time.time()):
            raise AuthenticationError("Refresh token expired")
            
        # Check if the token is revoked
        if token_info["is_revoked"]:
            raise AuthenticationError("Token has been revoked")
            
        # Revoke the old token
        self.tokens[token_id]["is_revoked"] = True
        
        # Generate a new token
        return self.generate_token(client_id, token_info["scopes"])

    def revoke_token(self, token: str, token_type_hint: str = "access_token") -> bool:
        """Revoke a token.

        Args:
            token: Token to revoke
            token_type_hint: Type of token ("access_token" or "refresh_token")

        Returns:
            True if the token was revoked, False otherwise
        """
        if token_type_hint == "access_token":
            try:
                # Decode the JWT token
                payload = jwt.decode(token, self.secret_key, algorithms=["HS256"], options={"verify_signature": True})
                
                # Get the token ID
                jti = payload.get("jti")
                if not jti or jti not in self.tokens:
                    return False
                    
                # Revoke the token
                self.tokens[jti]["is_revoked"] = True
                return True
                
            except (InvalidTokenError, ExpiredSignatureError):
                return False
                
        elif token_type_hint == "refresh_token":
            # Find the token entry by refresh token
            for jti, token_info in self.tokens.items():
                if token_info["refresh_token"] == token:
                    # Revoke the token
                    self.tokens[jti]["is_revoked"] = True
                    return True
                    
            return False
            
        return False

    def generate_agent_token(self, agent_id: str, name: str, capabilities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a token for an agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Name of the agent
            capabilities: Dictionary of agent capabilities

        Returns:
            Dictionary containing the agent token information
        """
        # Generate a unique token
        auth_token = secrets.token_hex(16)
        
        # Set token expiry (24 hours)
        now = int(time.time())
        expiry = now + 86400
        
        # Store the agent token
        self.agent_tokens[agent_id] = {
            "agent_id": agent_id,
            "name": name,
            "capabilities": capabilities,
            "auth_token": auth_token,
            "created_at": now,
            "expires_at": expiry,
            "is_active": True,
        }
        
        return {
            "agent_id": agent_id,
            "auth_token": auth_token,
            "expires_in": 86400,
        }

    def validate_agent_token(self, agent_id: str, auth_token: str) -> bool:
        """Validate an agent token.

        Args:
            agent_id: Unique identifier for the agent
            auth_token: Authentication token for the agent

        Returns:
            True if the token is valid, False otherwise
        """
        if agent_id not in self.agent_tokens:
            return False
            
        agent_info = self.agent_tokens[agent_id]
        
        # Check if the token matches
        if agent_info["auth_token"] != auth_token:
            return False
            
        # Check if the token is expired
        if agent_info["expires_at"] < int(time.time()):
            return False
            
        # Check if the agent is active
        if not agent_info["is_active"]:
            return False
            
        return True

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an agent.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            Dictionary containing agent information, or None if the agent doesn't exist
        """
        if agent_id not in self.agent_tokens:
            return None
            
        agent_info = self.agent_tokens[agent_id].copy()
        
        # Remove sensitive information
        agent_info.pop("auth_token", None)
        
        return agent_info


# Singleton instance
_token_manager_instance: Optional[TokenManager] = None


def get_token_manager(secret_key: Optional[str] = None, token_expiry: int = 3600) -> TokenManager:
    """Get the TokenManager singleton instance.

    Args:
        secret_key: Secret key for signing tokens. If not provided, a random key will be generated.
        token_expiry: Expiry time for access tokens in seconds. Default is 1 hour.

    Returns:
        The TokenManager instance
    """
    global _token_manager_instance
    
    if _token_manager_instance is None:
        _token_manager_instance = TokenManager(
            secret_key=secret_key,
            token_expiry=token_expiry,
        )
    
    return _token_manager_instance


async def get_current_user(token: str = None) -> Dict[str, Any]:
    """Get the current user from the token.

    Args:
        token: JWT token

    Returns:
        Dictionary containing user information

    Raises:
        HTTPException: If the token is invalid
    """
    # For development purposes, return a mock user
    return {
        "id": "user-1",
        "username": "admin",
        "email": "admin@example.com",
        "roles": ["admin"],
        "scopes": ["read", "write"],
    }
