# Authentication Implementation Guide

## Quick Start

### Backend Authentication

The backend provides token generation and authentication middleware:

```python
from auth.token_service import token_service
from auth.middleware import auth_middleware

# Generate LiveKit token
token = token_service.generate_room_token(
 room_name="voice-agent-room",
 user_id="user-123",
 user_name="John Doe"
)

# Protect endpoint
@auth_middleware.require_auth
def protected_endpoint():
 user_id = g.user_id # Available from middleware
 return jsonify({"user_id": user_id})
```

### Frontend Authentication

Use the AuthProvider context:

```tsx
import { useAuth } from '@/components/auth/AuthProvider'

function MyComponent() {
 const { user, isAuthenticated, login, logout } = useAuth()

 // Check auth status
 if (!isAuthenticated) {
 return <LoginButton />
 }

 return <ProtectedContent />
}
```

## Files Structure

- `backend/auth/token_service.py` - LiveKit token generation
- `backend/auth/middleware.py` - Authentication middleware
- `backend/auth/permissions.py` - Role and permission system
- `backend/api/auth_routes.py` - Authentication API endpoints
- `frontend/components/auth/AuthProvider.tsx` - React auth context
- `frontend/components/auth/ProtectedRoute.tsx` - Route protection

## API Endpoints

### POST /api/auth/token
Generate LiveKit room token (rate limited: 60/min)

Request:
```json
{
 "room_name": "voice-agent-room",
 "user_id": "optional-user-id",
 "user_name": "Optional Name"
}
```

Response:
```json
{
 "token": "livekit-jwt-token",
 "room_name": "voice-agent-room",
 "expires_in": 3600
}
```

### POST /api/auth/verify
Verify a token (optional auth)

### GET /api/auth/permissions
Get current user permissions (requires auth)

## Security Best Practices

1. **Always generate tokens server-side**
2. **Validate room names before token generation**
3. **Implement rate limiting on token endpoints**
4. **Use HTTPS for all token transmission**
5. **Don't log or expose tokens**
6. **Implement token expiration**
7. **Block reserved room names**

## Testing

```bash
# Test token generation
curl -X POST http://localhost:8000/api/auth/token \
 -H "Content-Type: application/json" \
 -d '{"room_name": "test-room"}'

# Test rate limiting (send 61 requests)
for i in {1..61}; do
 curl -X POST http://localhost:8000/api/auth/token \
 -H "Content-Type: application/json" \
 -d '{"room_name": "test-room"}'
done
```

## Production Considerations

1. **Use Redis for rate limiting** (not in-memory)
2. **Implement token refresh mechanism**
3. **Add token revocation** (if needed)
4. **Use separate JWT secret** (not LiveKit secret)
5. **Implement audit logging** for auth events
6. **Add MFA** for sensitive operations

