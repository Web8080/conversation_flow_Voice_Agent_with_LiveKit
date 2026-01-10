"""
LiveKit Token Generation Service
Handles secure token generation for LiveKit room access
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from livekit import api
from config.settings import settings
from utils.logger import logger


class TokenService:
    def __init__(self):
        self.api_key = settings.livekit_api_key
        self.api_secret = settings.livekit_api_secret
        logger.info("TokenService initialized")
    
    def generate_room_token(
        self,
        room_name: str,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        permissions: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate LiveKit room token with specified permissions
        
        Args:
            room_name: Name of the LiveKit room
            user_id: Unique user identifier (default: anonymous-{timestamp})
            user_name: Display name for user
            permissions: Custom permissions dict
        
        Returns:
            JWT token string for LiveKit room access
        """
        try:
            # Validate room name
            if not self._validate_room_name(room_name):
                raise ValueError(f"Invalid room name: {room_name}")
            
            # Generate user ID if not provided
            if not user_id:
                user_id = f"anonymous-{int(datetime.now().timestamp())}"
            
            # Default permissions
            default_permissions = {
                "roomJoin": True,
                "roomAdmin": False,
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True,
                "canUpdateOwnMetadata": True,
            }
            
            # Merge with custom permissions
            if permissions:
                default_permissions.update(permissions)
            
            # Create access token using LiveKit API
            token = api.AccessToken(self.api_key, self.api_secret) \
                .with_identity(user_id) \
                .with_name(user_name or user_id) \
                .with_grants(
                    api.VideoGrants(
                        room=room_name,
                        roomJoin=default_permissions["roomJoin"],
                        roomAdmin=default_permissions["roomAdmin"],
                        canPublish=default_permissions["canPublish"],
                        canSubscribe=default_permissions["canSubscribe"],
                        canPublishData=default_permissions["canPublishData"],
                        canUpdateOwnMetadata=default_permissions["canUpdateOwnMetadata"],
                    )
                )
            
            # Set expiration (1 hour default)
            expiration_hours = 1
            token.with_ttl(f"{expiration_hours}h")
            
            jwt_token = token.to_jwt()
            
            logger.info(
                "LiveKit token generated",
                room_name=room_name,
                user_id=user_id,
                expires_in="1h"
            )
            
            return jwt_token
            
        except Exception as e:
            logger.error("Failed to generate LiveKit token", error=str(e), room_name=room_name)
            raise
    
    def _validate_room_name(self, room_name: str) -> bool:
        """
        Validate room name format and security
        
        Args:
            room_name: Room name to validate
        
        Returns:
            True if valid, False otherwise
        """
        if not room_name or len(room_name) == 0:
            return False
        
        # Length check
        if len(room_name) > 100:
            return False
        
        # Character check (alphanumeric, dash, underscore only)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', room_name):
            return False
        
        # Block reserved names
        reserved_names = ["admin", "system", "test", "api", "internal"]
        if room_name.lower() in reserved_names:
            return False
        
        return True
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode LiveKit token (for validation purposes)
        Note: LiveKit tokens are stateless JWTs, so this is mainly for debugging
        
        Args:
            token: JWT token to verify
        
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            import jwt
            payload = jwt.decode(
                token,
                settings.livekit_api_secret,
                algorithms=["HS256"],
                options={"verify_signature": True}
            )
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


# Singleton instance
token_service = TokenService()

