"""
Authentication Middleware
Handles authentication for API endpoints (Flask-compatible)
Can be adapted for other frameworks
"""

from functools import wraps
from typing import Optional, Callable, Any, Dict
import jwt
from datetime import datetime
from config.settings import settings
from utils.logger import logger


class AuthMiddleware:
    """Authentication middleware - framework agnostic"""
    def __init__(self):
        self.secret_key = settings.livekit_api_secret  # Use LiveKit secret or separate JWT secret
        self.algorithm = "HS256"
    
    def extract_token_from_headers(self, headers: Dict[str, str]) -> Optional[str]:
        """Extract JWT token from headers (framework agnostic)"""
        auth_header = headers.get("Authorization") or headers.get("authorization")
        
        if not auth_header:
            return None
        
        # Support "Bearer <token>" format
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        
        # Support direct token
        return auth_header
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_signature": True, "verify_exp": True}
            )
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.now():
                logger.warning("Token expired")
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid token", error=str(e))
            return None
        except Exception as e:
            logger.error("Token verification failed", error=str(e))
            return None
    
    # Flask-specific decorators (if using Flask)
    def require_auth_flask(self, f: Callable) -> Callable:
        """Flask decorator to require authentication"""
        try:
            from flask import request, jsonify, g
        except ImportError:
            logger.warning("Flask not available, decorator won't work")
            return f
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = self.extract_token_from_headers(dict(request.headers))
            
            if not token:
                return jsonify({"error": "Authentication required"}), 401
            
            user_data = self.verify_token(token)
            if not user_data:
                return jsonify({"error": "Invalid or expired token"}), 401
            
            # Add user data to Flask global context
            g.user_id = user_data.get("sub")
            g.user_role = user_data.get("role", "user")
            g.user_permissions = user_data.get("permissions", [])
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def optional_auth_flask(self, f: Callable) -> Callable:
        """Flask decorator for optional authentication"""
        try:
            from flask import request, g
        except ImportError:
            return f
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = self.extract_token_from_headers(dict(request.headers))
            
            if token:
                user_data = self.verify_token(token)
                if user_data:
                    g.user_id = user_data.get("sub")
                    g.user_role = user_data.get("role", "anonymous")
                    g.user_permissions = user_data.get("permissions", [])
                else:
                    g.user_id = None
                    g.user_role = "anonymous"
            else:
                g.user_id = None
                g.user_role = "anonymous"
            
            return f(*args, **kwargs)
        
        return decorated_function


# Singleton instance
auth_middleware = AuthMiddleware()

