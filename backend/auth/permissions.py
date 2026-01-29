"""
Permission System
Defines and checks user permissions
"""

from typing import List, Set, Optional
from enum import Enum
from utils.logger import logger


class Permission(Enum):
    """User permissions"""
    # Conversation permissions
    CREATE_CONVERSATION = "create_conversation"
    VIEW_CONVERSATION = "view_conversation"
    VIEW_ALL_CONVERSATIONS = "view_all_conversations"
    
    # Appointment permissions
    CREATE_APPOINTMENT = "create_appointment"
    VIEW_APPOINTMENT = "view_appointment"
    VIEW_ALL_APPOINTMENTS = "view_all_appointments"
    CANCEL_APPOINTMENT = "cancel_appointment"
    
    # Room permissions
    CREATE_ROOM = "create_room"
    JOIN_ROOM = "join_room"
    ADMIN_ROOM = "admin_room"
    
    # System permissions
    VIEW_METRICS = "view_metrics"
    VIEW_LOGS = "view_logs"
    MANAGE_USERS = "manage_users"
    SYSTEM_ADMIN = "system_admin"


class Role:
    """User roles with associated permissions"""
    
    ANONYMOUS_PERMISSIONS: Set[Permission] = {
        Permission.CREATE_CONVERSATION,
        Permission.JOIN_ROOM,
    }
    
    USER_PERMISSIONS: Set[Permission] = {
        Permission.CREATE_CONVERSATION,
        Permission.VIEW_CONVERSATION,
        Permission.CREATE_APPOINTMENT,
        Permission.VIEW_APPOINTMENT,
        Permission.JOIN_ROOM,
    }
    
    ADMIN_PERMISSIONS: Set[Permission] = {
        Permission.CREATE_CONVERSATION,
        Permission.VIEW_CONVERSATION,
        Permission.VIEW_ALL_CONVERSATIONS,
        Permission.CREATE_APPOINTMENT,
        Permission.VIEW_APPOINTMENT,
        Permission.VIEW_ALL_APPOINTMENTS,
        Permission.CANCEL_APPOINTMENT,
        Permission.CREATE_ROOM,
        Permission.JOIN_ROOM,
        Permission.ADMIN_ROOM,
        Permission.VIEW_METRICS,
        Permission.VIEW_LOGS,
        Permission.MANAGE_USERS,
    }
    
    SYSTEM_ADMIN_PERMISSIONS: Set[Permission] = {
        *ADMIN_PERMISSIONS,
        Permission.SYSTEM_ADMIN,
    }
    
    @classmethod
    def get_permissions(cls, role: str) -> Set[Permission]:
        """Get permissions for a role"""
        role_mapping = {
            "anonymous": cls.ANONYMOUS_PERMISSIONS,
            "user": cls.USER_PERMISSIONS,
            "admin": cls.ADMIN_PERMISSIONS,
            "system_admin": cls.SYSTEM_ADMIN_PERMISSIONS,
        }
        return role_mapping.get(role, cls.ANONYMOUS_PERMISSIONS)
    
    @classmethod
    def has_permission(cls, role: str, permission: Permission) -> bool:
        """Check if role has specific permission"""
        permissions = cls.get_permissions(role)
        return permission in permissions


class PermissionChecker:
    """Helper class to check permissions"""
    
    @staticmethod
    def check_permission(user_role: str, permission: Permission) -> bool:
        """Check if user has permission"""
        has_permission = Role.has_permission(user_role, permission)
        
        if not has_permission:
            logger.warning(
                "Permission denied",
                role=user_role,
                permission=permission.value
            )
        
        return has_permission
    
    @staticmethod
    def check_permissions(user_role: str, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions"""
        return all(
            Role.has_permission(user_role, perm)
            for perm in permissions
        )
    
    @staticmethod
    def check_any_permission(user_role: str, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(
            Role.has_permission(user_role, perm)
            for perm in permissions
        )
    
    @staticmethod
    def can_view_conversation(user_role: str, conversation_user_id: Optional[str], current_user_id: Optional[str]) -> bool:
        """Check if user can view a specific conversation"""
        # Admins can view all
        if Role.has_permission(user_role, Permission.VIEW_ALL_CONVERSATIONS):
            return True
        
        # Users can view their own
        if conversation_user_id and current_user_id and conversation_user_id == current_user_id:
            return Role.has_permission(user_role, Permission.VIEW_CONVERSATION)
        
        return False


# Singleton instance
permission_checker = PermissionChecker()


