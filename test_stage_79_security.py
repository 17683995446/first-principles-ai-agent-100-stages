#!/usr/bin/env python3
"""第79阶段验收测试：安全与权限管理系统"""

import unittest
import time

from src.first_principles_agent.security import (
    PermissionType, ResourceType,
    Permission, Role, User, Resource,
    AccessControlEntry, AuditLog,
    PermissionManager,
    get_permission_manager, set_permission_manager,
    register_permission, register_role,
    create_user, get_user, assign_role,
    check_permission, check_user_permission,
    grant_access, log_audit, get_audit_logs,
    register_resource, get_resource
)


class TestPermissionTypes(unittest.TestCase):
    """测试权限类型定义"""
    
    def test_permission_type_values(self):
        """测试权限类型枚举值"""
        self.assertEqual(PermissionType.READ.value, "read")
        self.assertEqual(PermissionType.WRITE.value, "write")
        self.assertEqual(PermissionType.EXECUTE.value, "execute")
        self.assertEqual(PermissionType.DELETE.value, "delete")
        self.assertEqual(PermissionType.ADMIN.value, "admin")
        self.assertEqual(PermissionType.GRANT.value, "grant")
    
    def test_resource_type_values(self):
        """测试资源类型枚举值"""
        self.assertEqual(ResourceType.TASK.value, "task")
        self.assertEqual(ResourceType.SCHEDULER.value, "scheduler")
        self.assertEqual(ResourceType.CONFIG.value, "config")
        self.assertEqual(ResourceType.MONITOR.value, "monitor")
        self.assertEqual(ResourceType.USER.value, "user")
        self.assertEqual(ResourceType.SYSTEM.value, "system")


class TestPermissionDefinition(unittest.TestCase):
    """测试权限定义"""
    
    def setUp(self):
        self.manager = PermissionManager()
    
    def test_register_permission(self):
        """测试权限注册"""
        perm = Permission(
            name="task.read",
            type_=PermissionType.READ,
            resource_type=ResourceType.TASK,
            description="读取任务权限"
        )
        self.manager.register_permission(perm)
        
        retrieved = self.manager.get_permission("task.read")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "task.read")
        self.assertEqual(retrieved.type_, PermissionType.READ)
        self.assertEqual(retrieved.resource_type, ResourceType.TASK)
    
    def test_register_multiple_permissions(self):
        """测试批量权限注册"""
        perms = [
            Permission("task.create", PermissionType.WRITE, ResourceType.TASK),
            Permission("task.read", PermissionType.READ, ResourceType.TASK),
            Permission("task.delete", PermissionType.DELETE, ResourceType.TASK),
        ]
        self.manager.register_permissions(perms)
        
        self.assertEqual(len(self.manager.get_all_permissions()), 3)


class TestRoleManagement(unittest.TestCase):
    """测试角色管理"""
    
    def setUp(self):
        self.manager = PermissionManager()
    
    def test_register_role(self):
        """测试角色注册"""
        role = Role(
            name="admin",
            description="管理员角色",
            permissions={"task.read", "task.write", "task.delete"}
        )
        self.manager.register_role(role)
        
        retrieved = self.manager.get_role("admin")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "admin")
        self.assertIn("task.read", retrieved.permissions)
    
    def test_role_inheritance(self):
        """测试角色继承"""
        parent_role = Role(
            name="user",
            permissions={"task.read"}
        )
        child_role = Role(
            name="manager",
            permissions={"task.write"},
            parent_role="user"
        )
        
        self.manager.register_role(parent_role)
        self.manager.register_role(child_role)
        
        effective = self.manager.get_effective_permissions("manager")
        self.assertIn("task.read", effective)
        self.assertIn("task.write", effective)


class TestUserManagement(unittest.TestCase):
    """测试用户管理"""
    
    def setUp(self):
        self.manager = PermissionManager()
    
    def test_create_user(self):
        """测试创建用户"""
        user = self.manager.create_user("testuser", email="test@example.com")
        
        self.assertIsNotNone(user.id)
        self.assertEqual(user.name, "testuser")
        self.assertEqual(user.attributes["email"], "test@example.com")
        self.assertTrue(user.is_active)
    
    def test_get_user(self):
        """测试获取用户"""
        created = self.manager.create_user("testuser")
        retrieved = self.manager.get_user(created.id)
        
        self.assertEqual(created.id, retrieved.id)
        self.assertEqual(created.name, retrieved.name)
    
    def test_get_user_by_name(self):
        """测试按名称获取用户"""
        self.manager.create_user("testuser")
        retrieved = self.manager.get_user_by_name("testuser")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "testuser")
    
    def test_assign_role(self):
        """测试分配角色"""
        user = self.manager.create_user("testuser")
        self.manager.register_role(Role(name="admin", permissions={"task.admin"}))
        
        result = self.manager.assign_role(user.id, "admin")
        self.assertTrue(result)
        self.assertIn("admin", user.roles)
    
    def test_revoke_role(self):
        """测试撤销角色"""
        user = self.manager.create_user("testuser")
        self.manager.register_role(Role(name="admin"))
        self.manager.assign_role(user.id, "admin")
        
        result = self.manager.revoke_role(user.id, "admin")
        self.assertTrue(result)
        self.assertNotIn("admin", user.roles)
    
    def test_get_user_permissions(self):
        """测试获取用户权限"""
        self.manager.register_role(Role(
            name="admin",
            permissions={"task.read", "task.write", "task.delete"}
        ))
        
        user = self.manager.create_user("testuser")
        self.manager.assign_role(user.id, "admin")
        
        perms = self.manager.get_user_permissions(user.id)
        self.assertIn("task.read", perms)
        self.assertIn("task.write", perms)
        self.assertIn("task.delete", perms)
    
    def test_deactivate_user(self):
        """测试停用用户"""
        user = self.manager.create_user("testuser")
        self.assertTrue(user.is_active)
        
        self.manager.deactivate_user(user.id)
        self.assertFalse(user.is_active)
        
        self.manager.activate_user(user.id)
        self.assertTrue(user.is_active)


class TestResourceManagement(unittest.TestCase):
    """测试资源管理"""
    
    def setUp(self):
        self.manager = PermissionManager()
    
    def test_register_resource(self):
        """测试注册资源"""
        resource = Resource(
            id="task-001",
            type_=ResourceType.TASK,
            name="Test Task",
            owner_id="user-001"
        )
        self.manager.register_resource(resource)
        
        retrieved = self.manager.get_resource("task-001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "task-001")
        self.assertEqual(retrieved.name, "Test Task")


class TestAccessControl(unittest.TestCase):
    """测试访问控制"""
    
    def setUp(self):
        self.manager = PermissionManager()
    
    def test_grant_access(self):
        """测试授予访问权限"""
        user = self.manager.create_user("testuser")
        
        result = self.manager.grant_access(
            principal=user.id,
            principal_type="user",
            resource_id="task-001",
            permission=PermissionType.READ
        )
        self.assertTrue(result)
        
        has_perm = self.manager.check_permission(
            principal=user.id,
            resource_id="task-001",
            permission=PermissionType.READ
        )
        self.assertTrue(has_perm)
    
    def test_revoke_access(self):
        """测试撤销访问权限"""
        user = self.manager.create_user("testuser")
        
        self.manager.grant_access(
            principal=user.id,
            principal_type="user",
            resource_id="task-001",
            permission=PermissionType.READ
        )
        
        result = self.manager.revoke_access(
            principal=user.id,
            resource_id="task-001",
            permission=PermissionType.READ
        )
        self.assertTrue(result)
        
        has_perm = self.manager.check_permission(
            principal=user.id,
            resource_id="task-001",
            permission=PermissionType.READ
        )
        self.assertFalse(has_perm)
    
    def test_expired_access(self):
        """测试过期访问权限"""
        user = self.manager.create_user("testuser")
        
        self.manager.grant_access(
            principal=user.id,
            principal_type="user",
            resource_id="task-001",
            permission=PermissionType.READ,
            expires_at=time.time() - 1
        )
        
        has_perm = self.manager.check_permission(
            principal=user.id,
            resource_id="task-001",
            permission=PermissionType.READ
        )
        self.assertFalse(has_perm)
    
    def test_admin_grants_admin(self):
        """测试管理员自动获得授权权限"""
        user = self.manager.create_user("testuser")
        
        self.manager.grant_access(
            principal=user.id,
            principal_type="user",
            resource_id="task-001",
            permission=PermissionType.ADMIN
        )
        
        has_admin = self.manager.check_permission(
            principal=user.id,
            resource_id="task-001",
            permission=PermissionType.ADMIN
        )
        has_grant = self.manager.check_permission(
            principal=user.id,
            resource_id="task-001",
            permission=PermissionType.GRANT
        )
        
        self.assertTrue(has_admin)
        self.assertTrue(has_grant)
    
    def test_check_user_permission_with_role(self):
        """测试基于角色的权限检查"""
        self.manager.register_role(Role(
            name="reader",
            permissions={"task.read"}
        ))
        
        user = self.manager.create_user("testuser")
        self.manager.assign_role(user.id, "reader")
        
        has_perm = self.manager.check_user_permission(
            user_id=user.id,
            resource_id="task-001",
            permission=PermissionType.READ
        )
        self.assertTrue(has_perm)


class TestAuditLog(unittest.TestCase):
    """测试审计日志"""
    
    def setUp(self):
        self.manager = PermissionManager()
    
    def test_log_audit(self):
        """测试记录审计日志"""
        user = self.manager.create_user("testuser")
        
        self.manager.log_audit(
            user_id=user.id,
            action="read",
            resource_type=ResourceType.TASK,
            resource_id="task-001",
            permission=PermissionType.READ,
            result="success"
        )
        
        logs = self.manager.get_audit_logs(user_id=user.id)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, "read")
        self.assertEqual(logs[0].result, "success")
    
    def test_get_audit_logs_with_filters(self):
        """测试带过滤条件的审计日志查询"""
        user1 = self.manager.create_user("user1")
        user2 = self.manager.create_user("user2")
        
        self.manager.log_audit(user1.id, "read", ResourceType.TASK, "task-001", PermissionType.READ, "success")
        self.manager.log_audit(user1.id, "write", ResourceType.TASK, "task-002", PermissionType.WRITE, "success")
        self.manager.log_audit(user2.id, "read", ResourceType.TASK, "task-001", PermissionType.READ, "success")
        
        logs = self.manager.get_audit_logs(user_id=user1.id)
        self.assertEqual(len(logs), 2)
        
        logs = self.manager.get_audit_logs(resource_id="task-001")
        self.assertEqual(len(logs), 2)
    
    def test_audit_enabled_disabled(self):
        """测试审计开关"""
        self.manager.disable_audit()
        
        user = self.manager.create_user("testuser")
        self.manager.log_audit(user.id, "read", ResourceType.TASK, "task-001", PermissionType.READ, "success")
        
        logs = self.manager.get_audit_logs(user_id=user.id)
        self.assertEqual(len(logs), 0)
        
        self.manager.enable_audit()
        self.manager.log_audit(user.id, "read", ResourceType.TASK, "task-001", PermissionType.READ, "success")
        
        logs = self.manager.get_audit_logs(user_id=user.id)
        self.assertEqual(len(logs), 1)


class TestGlobalAPI(unittest.TestCase):
    """测试全局API"""
    
    def setUp(self):
        set_permission_manager(PermissionManager())
    
    def test_global_create_user(self):
        """测试全局创建用户"""
        user = create_user("testuser", email="test@example.com")
        
        self.assertIsNotNone(user.id)
        self.assertEqual(user.name, "testuser")
    
    def test_global_register_permission(self):
        """测试全局权限注册"""
        perm = Permission(
            name="task.read",
            type_=PermissionType.READ,
            resource_type=ResourceType.TASK
        )
        register_permission(perm)
        
        retrieved = get_permission_manager().get_permission("task.read")
        self.assertIsNotNone(retrieved)
    
    def test_global_check_permission(self):
        """测试全局权限检查"""
        user = create_user("testuser")
        
        grant_access(
            principal=user.id,
            principal_type="user",
            resource_id="task-001",
            permission=PermissionType.READ
        )
        
        has_perm = check_permission(
            principal=user.id,
            resource_id="task-001",
            permission=PermissionType.READ
        )
        self.assertTrue(has_perm)
    
    def test_global_log_audit(self):
        """测试全局审计日志"""
        user = create_user("testuser")
        
        log_audit(
            user_id=user.id,
            action="delete",
            resource_type=ResourceType.TASK,
            resource_id="task-001",
            permission=PermissionType.DELETE,
            result="success"
        )
        
        logs = get_audit_logs(user_id=user.id)
        self.assertEqual(len(logs), 1)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestPermissionTypes))
    suite.addTests(loader.loadTestsFromTestCase(TestPermissionDefinition))
    suite.addTests(loader.loadTestsFromTestCase(TestRoleManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestUserManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestResourceManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestAccessControl))
    suite.addTests(loader.loadTestsFromTestCase(TestAuditLog))
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalAPI))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
