from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any
import threading
import time
import uuid


class PermissionType(Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"
    GRANT = "grant"


class ResourceType(Enum):
    TASK = "task"
    SCHEDULER = "scheduler"
    CONFIG = "config"
    MONITOR = "monitor"
    USER = "user"
    SYSTEM = "system"


@dataclass
class Permission:
    name: str
    type_: PermissionType
    resource_type: ResourceType
    description: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Role:
    name: str
    description: str = ""
    permissions: Set[str] = field(default_factory=set)
    parent_role: Optional[str] = None
    priority: int = 0


@dataclass
class User:
    id: str
    name: str
    roles: Set[str] = field(default_factory=set)
    attributes: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass
class Resource:
    id: str
    type_: ResourceType
    name: str
    owner_id: Optional[str] = None
    permissions: Dict[str, PermissionType] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessControlEntry:
    principal: str
    principal_type: str
    resource_id: str
    permission: PermissionType
    granted: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)
    granted_by: Optional[str] = None
    granted_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None


@dataclass
class AuditLog:
    id: str
    timestamp: float
    user_id: str
    action: str
    resource_type: ResourceType
    resource_id: str
    permission: PermissionType
    result: str
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None


class PermissionManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._permissions: Dict[str, Permission] = {}
        self._roles: Dict[str, Role] = {}
        self._users: Dict[str, User] = {}
        self._resources: Dict[str, Resource] = {}
        self._acl: List[AccessControlEntry] = []
        self._audit_logs: List[AuditLog] = []
        self._audit_enabled = True
        
    def register_permission(self, permission: Permission) -> None:
        with self._lock:
            self._permissions[permission.name] = permission
    
    def register_permissions(self, permissions: List[Permission]) -> None:
        for p in permissions:
            self.register_permission(p)
    
    def get_permission(self, name: str) -> Optional[Permission]:
        return self._permissions.get(name)
    
    def register_role(self, role: Role) -> None:
        with self._lock:
            self._roles[role.name] = role
    
    def register_roles(self, roles: List[Role]) -> None:
        for r in roles:
            self.register_role(r)
    
    def get_role(self, name: str) -> Optional[Role]:
        return self._roles.get(name)
    
    def get_effective_permissions(self, role_name: str) -> Set[str]:
        with self._lock:
            role = self._roles.get(role_name)
            if not role:
                return set()
            
            perms = role.permissions.copy()
            
            if role.parent_role:
                parent_perms = self.get_effective_permissions(role.parent_role)
                perms.update(parent_perms)
            
            return perms
    
    def create_user(self, name: str, **attributes) -> User:
        with self._lock:
            user_id = str(uuid.uuid4())
            user = User(
                id=user_id,
                name=name,
                attributes=attributes
            )
            self._users[user_id] = user
            return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)
    
    def get_user_by_name(self, name: str) -> Optional[User]:
        for user in self._users.values():
            if user.name == name:
                return user
        return None
    
    def assign_role(self, user_id: str, role_name: str) -> bool:
        with self._lock:
            user = self._users.get(user_id)
            role = self._roles.get(role_name)
            if not user or not role:
                return False
            user.roles.add(role_name)
            return True
    
    def revoke_role(self, user_id: str, role_name: str) -> bool:
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                return False
            if role_name in user.roles:
                user.roles.discard(role_name)
                return True
            return False
    
    def get_user_permissions(self, user_id: str) -> Set[str]:
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                return set()
            
            all_perms = set()
            for role_name in user.roles:
                all_perms.update(self.get_effective_permissions(role_name))
            
            return all_perms
    
    def register_resource(self, resource: Resource) -> None:
        with self._lock:
            self._resources[resource.id] = resource
    
    def get_resource(self, resource_id: str) -> Optional[Resource]:
        return self._resources.get(resource_id)
    
    def grant_access(
        self,
        principal: str,
        principal_type: str,
        resource_id: str,
        permission: PermissionType,
        granted_by: Optional[str] = None,
        expires_at: Optional[float] = None,
        conditions: Optional[Dict[str, Any]] = None
    ) -> bool:
        with self._lock:
            ace = AccessControlEntry(
                principal=principal,
                principal_type=principal_type,
                resource_id=resource_id,
                permission=permission,
                granted=True,
                granted_by=granted_by,
                expires_at=expires_at,
                conditions=conditions or {}
            )
            self._acl.append(ace)
            
            if permission == PermissionType.ADMIN:
                admin_ace = AccessControlEntry(
                    principal=principal,
                    principal_type=principal_type,
                    resource_id=resource_id,
                    permission=PermissionType.GRANT,
                    granted=True,
                    granted_by=granted_by,
                    expires_at=expires_at
                )
                self._acl.append(admin_ace)
            
            return True
    
    def revoke_access(
        self,
        principal: str,
        resource_id: str,
        permission: PermissionType
    ) -> bool:
        with self._lock:
            for ace in reversed(self._acl):
                if (ace.principal == principal and 
                    ace.resource_id == resource_id and 
                    ace.permission == permission and
                    ace.granted):
                    ace.granted = False
                    return True
            return False
    
    def check_permission(
        self,
        principal: str,
        resource_id: str,
        permission: PermissionType
    ) -> bool:
        with self._lock:
            for ace in reversed(self._acl):
                if (ace.principal == principal and 
                    ace.resource_id == resource_id and 
                    ace.permission == permission):
                    if ace.expires_at and time.time() > ace.expires_at:
                        continue
                    return ace.granted
            return False
    
    def check_user_permission(
        self,
        user_id: str,
        resource_id: str,
        permission: PermissionType
    ) -> bool:
        with self._lock:
            user = self._users.get(user_id)
            if not user or not user.is_active:
                return False
            
            for ace in reversed(self._acl):
                if (ace.principal == user_id and 
                    ace.principal_type == "user" and
                    ace.resource_id == resource_id and 
                    ace.permission == permission):
                    if ace.expires_at and time.time() > ace.expires_at:
                        continue
                    return ace.granted
            
            user_perms = self.get_user_permissions(user_id)
            for perm_name in user_perms:
                perm = self._permissions.get(perm_name)
                if perm and perm.type_ == permission:
                    return True
            
            return False
    
    def log_audit(
        self,
        user_id: str,
        action: str,
        resource_type: ResourceType,
        resource_id: str,
        permission: PermissionType,
        result: str,
        **details
    ) -> None:
        if not self._audit_enabled:
            return
        
        with self._lock:
            log = AuditLog(
                id=str(uuid.uuid4()),
                timestamp=time.time(),
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                permission=permission,
                result=result,
                details=details
            )
            self._audit_logs.append(log)
    
    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        since: Optional[float] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        with self._lock:
            logs = self._audit_logs
            
            if user_id:
                logs = [l for l in logs if l.user_id == user_id]
            if resource_id:
                logs = [l for l in logs if l.resource_id == resource_id]
            if since:
                logs = [l for l in logs if l.timestamp >= since]
            
            return logs[-limit:]
    
    def enable_audit(self) -> None:
        self._audit_enabled = True
    
    def disable_audit(self) -> None:
        self._audit_enabled = False
    
    def get_all_users(self) -> List[User]:
        with self._lock:
            return list(self._users.values())
    
    def get_all_roles(self) -> List[Role]:
        with self._lock:
            return list(self._roles.values())
    
    def get_all_permissions(self) -> List[Permission]:
        with self._lock:
            return list(self._permissions.values())
    
    def get_user_acl(self, user_id: str) -> List[AccessControlEntry]:
        with self._lock:
            return [
                ace for ace in self._acl 
                if ace.principal == user_id and ace.principal_type == "user"
            ]
    
    def clear_audit_logs(self) -> None:
        with self._lock:
            self._audit_logs.clear()
    
    def deactivate_user(self, user_id: str) -> bool:
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                return False
            user.is_active = False
            return True
    
    def activate_user(self, user_id: str) -> bool:
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                return False
            user.is_active = True
            return True


_global_permission_manager: Optional[PermissionManager] = None
_global_lock = threading.Lock()


def get_permission_manager() -> PermissionManager:
    global _global_permission_manager
    with _global_lock:
        if _global_permission_manager is None:
            _global_permission_manager = PermissionManager()
        return _global_permission_manager


def set_permission_manager(manager: PermissionManager) -> None:
    global _global_permission_manager
    with _global_lock:
        _global_permission_manager = manager


def register_permission(permission: Permission) -> None:
    get_permission_manager().register_permission(permission)


def register_role(role: Role) -> None:
    get_permission_manager().register_role(role)


def create_user(name: str, **attributes) -> User:
    return get_permission_manager().create_user(name, **attributes)


def get_user(user_id: str) -> Optional[User]:
    return get_permission_manager().get_user(user_id)


def assign_role(user_id: str, role_name: str) -> bool:
    return get_permission_manager().assign_role(user_id, role_name)


def check_permission(
    principal: str,
    resource_id: str,
    permission: PermissionType
) -> bool:
    return get_permission_manager().check_permission(principal, resource_id, permission)


def check_user_permission(
    user_id: str,
    resource_id: str,
    permission: PermissionType
) -> bool:
    return get_permission_manager().check_user_permission(user_id, resource_id, permission)


def grant_access(
    principal: str,
    principal_type: str,
    resource_id: str,
    permission: PermissionType,
    **kwargs
) -> bool:
    return get_permission_manager().grant_access(principal, principal_type, resource_id, permission, **kwargs)


def log_audit(
    user_id: str,
    action: str,
    resource_type: ResourceType,
    resource_id: str,
    permission: PermissionType,
    result: str,
    **details
) -> None:
    get_permission_manager().log_audit(user_id, action, resource_type, resource_id, permission, result, **details)


def get_audit_logs(**kwargs) -> List[AuditLog]:
    return get_permission_manager().get_audit_logs(**kwargs)


def register_resource(resource: Resource) -> None:
    get_permission_manager().register_resource(resource)


def get_resource(resource_id: str) -> Optional[Resource]:
    return get_permission_manager().get_resource(resource_id)
