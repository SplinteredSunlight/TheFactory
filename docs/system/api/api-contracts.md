# API Contracts for AI-Orchestration-Platform

This document outlines the API contracts between different components of the AI-Orchestration-Platform, with a focus on the integration between AI-Orchestrator and Fast-Agent.

## Table of Contents

1. [Authentication Mechanism](#authentication-mechanism)
2. [Error Handling Protocol](#error-handling-protocol)

## Authentication Mechanism

### Overview

The authentication mechanism ensures secure communication between AI-Orchestrator and Fast-Agent components. It uses a token-based authentication system with the following features:

- API key authentication for initial connection
- JWT (JSON Web Token) for session-based authentication
- Token refresh mechanism for long-running sessions
- Role-based access control for different operations

### Endpoints

#### 1. Authentication Endpoints

##### 1.1 Generate Authentication Token

**Endpoint:** `/api/v1/auth/token`

**Method:** POST

**Request:**
```json
{
  "api_key": "string",
  "client_id": "string",
  "scope": ["string"]
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "string",
  "scope": ["string"]
}
```

**Status Codes:**
- 200: Success
- 401: Invalid API key
- 403: Insufficient permissions
- 500: Server error

##### 1.2 Refresh Authentication Token

**Endpoint:** `/api/v1/auth/token/refresh`

**Method:** POST

**Request:**
```json
{
  "refresh_token": "string",
  "client_id": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "string",
  "scope": ["string"]
}
```

**Status Codes:**
- 200: Success
- 401: Invalid refresh token
- 403: Insufficient permissions
- 500: Server error

##### 1.3 Validate Authentication Token

**Endpoint:** `/api/v1/auth/token/validate`

**Method:** POST

**Request:**
```json
{
  "access_token": "string"
}
```

**Response:**
```json
{
  "valid": true,
  "expires_in": 3600,
  "scope": ["string"],
  "client_id": "string"
}
```

**Status Codes:**
- 200: Success
- 401: Invalid token
- 500: Server error

##### 1.4 Revoke Authentication Token

**Endpoint:** `/api/v1/auth/token/revoke`

**Method:** POST

**Request:**
```json
{
  "token": "string",
  "token_type_hint": "access_token|refresh_token"
}
```

**Response:**
```json
{
  "success": true
}
```

**Status Codes:**
- 200: Success
- 401: Invalid token
- 500: Server error

#### 2. Agent Authentication Endpoints

##### 2.1 Register Agent

**Endpoint:** `/api/v1/agents/register`

**Method:** POST

**Headers:**
- Authorization: Bearer {access_token}

**Request:**
```json
{
  "name": "string",
  "description": "string",
  "capabilities": {
    "model": "string",
    "servers": ["string"],
    "provider": "string"
  },
  "auth_type": "api_key|jwt|oauth",
  "auth_credentials": {
    "key": "value"
  }
}
```

**Response:**
```json
{
  "agent_id": "string",
  "auth_token": "string",
  "expires_in": 86400
}
```

**Status Codes:**
- 201: Created
- 400: Bad request
- 401: Unauthorized
- 500: Server error

##### 2.2 Authenticate Agent

**Endpoint:** `/api/v1/agents/authenticate`

**Method:** POST

**Request:**
```json
{
  "agent_id": "string",
  "auth_token": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": ["string"]
}
```

**Status Codes:**
- 200: Success
- 401: Invalid credentials
- 403: Agent disabled
- 500: Server error

### Data Formats

#### JWT Token Format

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "iss": "ai-orchestration-platform",
    "sub": "client_id|agent_id",
    "aud": "ai-orchestrator|fast-agent",
    "exp": 1615566294,
    "iat": 1615562694,
    "jti": "unique-token-id",
    "scope": ["scope1", "scope2"]
  },
  "signature": "..."
}
```

#### Agent Credentials Format

```json
{
  "agent_id": "string",
  "auth_token": "string",
  "auth_type": "api_key|jwt|oauth",
  "capabilities": {
    "model": "string",
    "servers": ["string"],
    "provider": "string"
  },
  "permissions": ["permission1", "permission2"],
  "created_at": "ISO-8601 timestamp",
  "expires_at": "ISO-8601 timestamp"
}
```

### Authentication Flow

1. **Initial Authentication:**
   - Fast-Agent requests an authentication token from AI-Orchestrator using its API key
   - AI-Orchestrator validates the API key and issues a JWT token
   - Fast-Agent uses the JWT token for subsequent requests

2. **Agent Registration:**
   - Fast-Agent registers an agent with AI-Orchestrator using its JWT token
   - AI-Orchestrator validates the JWT token and registers the agent
   - AI-Orchestrator issues an agent-specific authentication token

3. **Agent Authentication:**
   - Fast-Agent authenticates an agent with AI-Orchestrator using the agent-specific token
   - AI-Orchestrator validates the agent token and issues a JWT token for the agent
   - Fast-Agent uses the agent JWT token for agent-specific operations

4. **Token Refresh:**
   - When a JWT token is about to expire, Fast-Agent requests a new token using the refresh token
   - AI-Orchestrator validates the refresh token and issues a new JWT token
   - Fast-Agent uses the new JWT token for subsequent requests

5. **Token Revocation:**
   - When an agent is no longer needed, Fast-Agent revokes its token
   - AI-Orchestrator invalidates the token and removes it from the valid tokens list

### Security Considerations

1. **Token Storage:**
   - Tokens should be stored securely and never exposed in logs or error messages
   - Refresh tokens should be stored with higher security than access tokens

2. **Token Expiration:**
   - Access tokens should have a short lifetime (e.g., 1 hour)
   - Refresh tokens can have a longer lifetime but should still expire (e.g., 14 days)

3. **Token Scope:**
   - Tokens should be issued with the minimum necessary scope
   - Scope should be validated for each API request

4. **Rate Limiting:**
   - Authentication endpoints should implement rate limiting to prevent brute force attacks
   - Failed authentication attempts should be monitored and trigger alerts

5. **Secure Communication:**
   - All API communication should use HTTPS
   - API keys and tokens should never be transmitted in URL parameters

6. **Audit Logging:**
   - All authentication events should be logged for audit purposes
   - Logs should include client ID, timestamp, and event type, but not sensitive data

## Error Handling Protocol

The AI-Orchestration-Platform implements a standardized error handling protocol to ensure consistent error reporting and handling across all components.

### Overview

The error handling protocol includes:

- Standardized error response format
- Consistent error codes and HTTP status codes
- Error handling mechanisms (Circuit Breaker, Retry Handler)
- Error logging and monitoring

### Error Response Format

All API errors follow a standardized JSON format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... },
    "severity": "ERROR",
    "component": "COMPONENT_NAME",
    "request_id": "unique-request-id",
    "timestamp": "2025-03-09T01:30:00Z",
    "documentation_url": "https://example.com/docs/errors/error-code"
  }
}
```

### Error Handling Mechanisms

The platform implements several error handling mechanisms:

1. **Circuit Breaker**: Prevents cascading failures by temporarily disabling operations that are failing repeatedly
2. **Retry Handler**: Automatically retries failed operations with exponential backoff
3. **Error Standardization**: Converts all errors to the standard error format

### Detailed Documentation

For detailed information about error codes, handling mechanisms, and client implementation guidelines, see the [Error Handling Protocol Documentation](api-contracts/error-handling.md).
