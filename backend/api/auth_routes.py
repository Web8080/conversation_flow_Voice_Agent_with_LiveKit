"""
Authentication API Routes
Handles token generation and authentication endpoints
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import secrets
from auth.token_service import token_service
try:
    from flask import Blueprint, request, jsonify, g
    from auth.middleware import auth_middleware
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logger.warning("Flask not available - auth routes will use alternative implementation")
from auth.permissions import PermissionChecker, Role
from utils.logger import logger
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def rate_limit(max_per_minute: int = 60):
    """Simple rate limiting decorator"""
    from collections import defaultdict
    from time import time
    
    requests = defaultdict(list)
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            now = time()
            
            # Clean old requests
            requests[client_ip] = [
                req_time for req_time in requests[client_ip]
                if now - req_time < 60
            ]
            
            # Check rate limit
            if len(requests[client_ip]) >= max_per_minute:
                logger.warning("Rate limit exceeded", ip=client_ip)
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            requests[client_ip].append(now)
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


@auth_bp.route('/token', methods=['POST'])
@rate_limit(max_per_minute=60)
def generate_livekit_token():
    """
    Generate LiveKit room token
    
    Request body:
    {
        "room_name": "voice-agent-room",
        "user_id": "optional-user-id",
        "user_name": "Optional Display Name"
    }
    """
    try:
        data = request.get_json() or {}
        
        room_name = data.get("room_name")
        if not room_name:
            return jsonify({"error": "room_name is required"}), 400
        
        user_id = data.get("user_id")
        user_name = data.get("user_name")
        
        # Generate token
        token = token_service.generate_room_token(
            room_name=room_name,
            user_id=user_id,
            user_name=user_name
        )
        
        logger.info("Token generated via API", room_name=room_name, user_id=user_id)
        
        return jsonify({
            "token": token,
            "room_name": room_name,
            "expires_in": 3600,  # 1 hour in seconds
        }), 200
        
    except ValueError as e:
        logger.warning("Invalid token request", error=str(e))
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Token generation failed", error=str(e))
        return jsonify({"error": "Failed to generate token"}), 500


@auth_bp.route('/verify', methods=['POST'])
@auth_middleware.optional_auth
def verify_token():
    """Verify a LiveKit token"""
    try:
        data = request.get_json() or {}
        token = data.get("token")
        
        if not token:
            return jsonify({"error": "token is required"}), 400
        
        payload = token_service.verify_token(token)
        
        if payload:
            return jsonify({
                "valid": True,
                "payload": payload
            }), 200
        else:
            return jsonify({
                "valid": False,
                "error": "Invalid or expired token"
            }), 401
            
    except Exception as e:
        logger.error("Token verification failed", error=str(e))
        return jsonify({"error": "Verification failed"}), 500


@auth_bp.route('/permissions', methods=['GET'])
@auth_middleware.require_auth
def get_permissions():
    """Get current user's permissions"""
    from flask import g
    
    user_role = getattr(g, 'user_role', 'anonymous')
    permissions = [perm.value for perm in Role.get_permissions(user_role)]
    
    return jsonify({
        "role": user_role,
        "permissions": permissions
    }), 200

