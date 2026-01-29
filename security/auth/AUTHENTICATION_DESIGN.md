# Authentication Design & Implementation

## Authentication Strategy

### Overview

The voice agent system uses a **multi-layer authentication approach**:

1. **LiveKit Token Authentication** (Primary)
 - JWT-based tokens for room access
 - Server-side token generation
 - Token expiration and validation

2. **API Authentication** (Secondary)
 - Session-based or JWT for API endpoints
 - Rate limiting per authenticated user
 - Optional: OAuth2/OIDC for enterprise

3. **User Management** (Optional)
 - Anonymous users (default)
 - Authenticated users (for appointment tracking)
 - Admin users (for system management)

## Authentication Flows

### Flow 1: Anonymous User (Default)

```
User → Frontend → Request LiveKit Token → Backend (No Auth) → Token → LiveKit Room
```

**Use Case**: Quick start, no user tracking required

**Security**:
- Rate limiting on token generation
- IP-based throttling
- Room name validation

### Flow 2: Authenticated User

```
User → Frontend Login → JWT/Session Token → Request LiveKit Token → Backend (Verify Auth) → Token → LiveKit Room
```

**Use Case**: Track conversations, save appointments, user preferences

**Security**:
- JWT with expiration
- Refresh token mechanism
- User session management

### Flow 3: Enterprise SSO (Optional)

```
User → Enterprise SSO → OAuth2/OIDC → JWT → Request LiveKit Token → Backend (Verify) → Token → LiveKit Room
```

**Use Case**: Enterprise deployments with existing identity providers

## Token Architecture

### LiveKit Token

```json
{
 "sub": "user-id-or-anonymous",
 "iss": "your-server",
 "exp": 1234567890,
 "video": {
 "room": "voice-agent-room",
 "roomJoin": true,
 "canPublish": true,
 "canSubscribe": true
 },
 "audio": {
 "room": "voice-agent-room",
 "roomJoin": true,
 "canPublish": true,
 "canSubscribe": true
 }
}
```

**Lifetime**: 1 hour (configurable)
**Renewal**: Generate new token before expiration
**Revocation**: Not supported by LiveKit (tokens are stateless)

### API Token (JWT)

```json
{
 "sub": "user-id",
 "iss": "voice-agent-api",
 "exp": 1234567890,
 "iat": 1234567890,
 "aud": "voice-agent-frontend",
 "roles": ["user"],
 "permissions": ["create_conversation", "view_appointments"]
}
```

**Lifetime**: 15 minutes (access token), 7 days (refresh token)
**Renewal**: Refresh token mechanism
**Revocation**: Token blacklist or database check

## Security Considerations

### 1. Token Generation Security

- **Server-Side Only**: Tokens MUST be generated server-side
- **Secret Management**: LiveKit API secret stored securely
- **Validation**: Verify room names, user permissions before token generation
- **Rate Limiting**: Prevent token generation abuse

### 2. Token Storage

- **Frontend**: Store in memory (not localStorage for security)
- **Backend**: Never log or expose tokens
- **Transmission**: Always use HTTPS

### 3. Token Validation

- **Signature Verification**: Always verify JWT signatures
- **Expiration Check**: Reject expired tokens
- **Audience Check**: Verify token audience matches
- **Issuer Check**: Verify token issuer

### 4. Room Security

- **Room Name Validation**: Prevent room name injection
- **Participant Limits**: Enforce max participants per room
- **Room Isolation**: Users can only access authorized rooms
- **Room Cleanup**: Auto-delete idle/expired rooms

## Implementation Components

### Backend

1. **Token Generation Service**
 - Generate LiveKit tokens
 - Validate user permissions
 - Handle token expiration

2. **Authentication Middleware**
 - Verify JWT tokens
 - Extract user context
 - Handle authentication errors

3. **Rate Limiting Middleware**
 - Per-IP rate limiting
 - Per-user rate limiting (if authenticated)
 - Token generation throttling

### Frontend

1. **Auth Context**
 - Manage authentication state
 - Handle token refresh
 - Provide auth methods

2. **Protected Routes**
 - Require authentication for certain routes
 - Redirect to login if not authenticated
 - Handle token expiration

3. **Token Management**
 - Request tokens from backend
 - Store tokens securely
 - Handle token refresh

## User Roles & Permissions

### Anonymous User
- Can create conversations
- Can join rooms
- Cannot track appointments
- Rate limited (stricter)

### Authenticated User
- Can create conversations
- Can join rooms
- Can track appointments
- Can view conversation history
- Rate limited (standard)

### Admin User
- All user permissions
- Can view all conversations
- Can manage system settings
- Can access monitoring dashboards

## Implementation Files

- `backend/auth/token_service.py` - Token generation and validation
- `backend/auth/middleware.py` - Authentication middleware
- `backend/auth/permissions.py` - Permission checking
- `frontend/components/auth/AuthProvider.tsx` - Auth context
- `frontend/components/auth/LoginForm.tsx` - Login component
- `frontend/middleware.ts` - Next.js auth middleware

## Security Best Practices

1. **Never expose secrets**: API keys, secrets stay server-side
2. **Use HTTPS**: All token transmission over HTTPS
3. **Short token lifetime**: Minimize token lifetime
4. **Token rotation**: Implement refresh token mechanism
5. **Audit logging**: Log all authentication events
6. **Rate limiting**: Prevent brute force and abuse
7. **Input validation**: Validate all inputs before token generation
8. **Error handling**: Don't leak sensitive info in errors

## Compliance Considerations

- **GDPR**: User consent for data collection
- **CCPA**: User data access and deletion
- **SOC 2**: Audit trail for authentication events
- **HIPAA**: If handling healthcare data, additional auth requirements

## Future Enhancements

1. **Multi-Factor Authentication (MFA)**
2. **Biometric Authentication**
3. **OAuth2/OIDC Integration**
4. **Single Sign-On (SSO)**
5. **Device Management**

