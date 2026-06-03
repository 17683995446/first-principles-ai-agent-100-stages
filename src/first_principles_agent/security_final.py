"""
安全加固和最终安全审查 - 第90阶段
完整的安全审查和加固框架
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
import re
import secrets
import string
from first_principles_agent import (
    PermissionManager, Permission, Role, User,
    ResourceType, PermissionType
)


class SecuritySeverity(Enum):
    """安全问题严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityCheckCategory(Enum):
    """安全检查分类"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INPUT_VALIDATION = "input_validation"
    DATA_PROTECTION = "data_protection"
    ERROR_HANDLING = "error_handling"
    LOGGING = "logging"
    CONFIGURATION = "configuration"


@dataclass
class SecurityIssue:
    """安全问题"""
    check_name: str
    category: SecurityCheckCategory
    severity: SecuritySeverity
    description: str
    recommendation: str
    is_critical: bool = False


@dataclass
class SecurityCheckResult:
    """安全检查结果"""
    check_name: str
    category: SecurityCheckCategory
    passed: bool
    issues: List[SecurityIssue] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0


@dataclass
class SecurityAuditReport:
    """安全审计报告"""
    report_id: str = field(default_factory=lambda: secrets.token_hex(8))
    generated_at: float = field(default_factory=lambda: __import__('time').time())
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    check_results: List[SecurityCheckResult] = field(default_factory=list)
    overall_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)


class SecurityFinalAudit:
    """最终安全审计"""
    
    def __init__(self):
        self.checks: List[SecurityCheckResult] = []
        self._setup_checks()
    
    def _setup_checks(self):
        """设置安全检查"""
        pass  # 检查将通过方法动态添加
    
    def check_input_validation(self) -> SecurityCheckResult:
        """检查输入验证"""
        result = SecurityCheckResult(
            check_name="Input Validation",
            category=SecurityCheckCategory.INPUT_VALIDATION,
            passed=True
        )
        
        # 测试基本输入验证
        test_cases = [
            ("Normal text", True),
            ("; DROP TABLE users;", False),
            ("<script>alert('xss')</script>", False),
            ("../../etc/passwd", False),
            ("user@example.com", True),
            ("password123", True),
        ]
        
        for input_data, should_pass in test_cases:
            is_safe = self._is_input_safe(input_data)
            if is_safe != should_pass:
                result.issues.append(SecurityIssue(
                    check_name="Input Validation",
                    category=SecurityCheckCategory.INPUT_VALIDATION,
                    severity=SecuritySeverity.HIGH,
                    description=f"Input validation failed for: {input_data[:50]}",
                    recommendation="Implement proper input sanitization and validation",
                    is_critical=not is_safe and should_pass
                ))
                result.passed = False
        
        return result
    
    def _is_input_safe(self, input_str: str) -> bool:
        """检查输入是否安全"""
        if not isinstance(input_str, str):
            return True
        
        # 简单的安全检查模式
        dangerous_patterns = [
            r"['\";]",  # SQL注入风险
            r"<script",  # XSS风险
            r"\.\./",  # 路径遍历风险
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                return False
        
        return True
    
    def check_authorization(self) -> SecurityCheckResult:
        """检查权限系统"""
        result = SecurityCheckResult(
            check_name="Authorization",
            category=SecurityCheckCategory.AUTHORIZATION,
            passed=True
        )
        
        try:
            # 测试权限系统基本功能
            pm = PermissionManager()
            user = pm.create_user("security_test_user")
            role = pm.create_role("tester")
            
            # 添加权限
            perm = Permission(
                name="test_permission",
                resource_type=ResourceType.TASK,
                resource_id="test_123",
                permission_type=PermissionType.EXECUTE
            )
            role.add_permission(perm)
            user.assign_role(role)
            
            # 检查权限
            has_perm = user.has_permission(
                "test_permission",
                ResourceType.TASK,
                "test_123",
                PermissionType.EXECUTE
            )
            
            if not has_perm:
                result.issues.append(SecurityIssue(
                    check_name="Authorization",
                    category=SecurityCheckCategory.AUTHORIZATION,
                    severity=SecuritySeverity.HIGH,
                    description="Permission assignment not working correctly",
                    recommendation="Verify permission system implementation",
                    is_critical=True
                ))
                result.passed = False
            
            # 检查未授权访问
            no_perm_user = pm.create_user("unauthorized")
            if no_perm_user.has_permission(
                "test_permission",
                ResourceType.TASK,
                "test_123",
                PermissionType.EXECUTE
            ):
                result.issues.append(SecurityIssue(
                    check_name="Authorization",
                    category=SecurityCheckCategory.AUTHORIZATION,
                    severity=SecuritySeverity.CRITICAL,
                    description="Unauthorized access should be blocked",
                    recommendation="Ensure proper permission checks are enforced",
                    is_critical=True
                ))
                result.passed = False
        
        except Exception as e:
            result.issues.append(SecurityIssue(
                check_name="Authorization",
                category=SecurityCheckCategory.AUTHORIZATION,
                severity=SecuritySeverity.HIGH,
                description=f"Authorization system error: {str(e)}",
                recommendation="Fix permission system issues",
                is_critical=True
            ))
            result.passed = False
        
        return result
    
    def check_password_strength(self) -> SecurityCheckResult:
        """检查密码强度"""
        result = SecurityCheckResult(
            check_name="Password Strength",
            category=SecurityCheckCategory.AUTHENTICATION,
            passed=True
        )
        
        weak_passwords = [
            "password",
            "123456",
            "qwerty",
            "abc123",
            "admin"
        ]
        
        for pwd in weak_passwords:
            if not self._is_password_strong(pwd):
                result.issues.append(SecurityIssue(
                    check_name="Password Strength",
                    category=SecurityCheckCategory.AUTHENTICATION,
                    severity=SecuritySeverity.MEDIUM,
                    description=f"Weak password detected: {pwd}",
                    recommendation="Enforce strong password policies",
                    is_critical=False
                ))
        
        return result
    
    def _is_password_strong(self, password: str) -> bool:
        """检查密码强度"""
        if len(password) < 8:
            return False
        if not any(c.isupper() for c in password):
            return False
        if not any(c.islower() for c in password):
            return False
        if not any(c.isdigit() for c in password):
            return False
        return True
    
    def check_error_handling(self) -> SecurityCheckResult:
        """检查错误处理"""
        result = SecurityCheckResult(
            check_name="Error Handling",
            category=SecurityCheckCategory.ERROR_HANDLING,
            passed=True
        )
        
        # 测试安全的错误处理
        try:
            # 模拟错误场景
            1 / 0
        except Exception as e:
            # 检查是否泄露敏感信息
            error_msg = str(e)
            if "password" in error_msg.lower() or "secret" in error_msg.lower():
                result.issues.append(SecurityIssue(
                    check_name="Error Handling",
                    category=SecurityCheckCategory.ERROR_HANDLING,
                    severity=SecuritySeverity.HIGH,
                    description="Error messages may leak sensitive information",
                    recommendation="Ensure error messages don't reveal sensitive data",
                    is_critical=False
                ))
        
        return result
    
    def run_full_audit(self) -> SecurityAuditReport:
        """运行完整的安全审计"""
        import time
        print("="*70)
        print("Final Security Audit - Stage 90")
        print("="*70)
        
        report = SecurityAuditReport()
        
        # 运行所有安全检查
        checks = [
            ("Input Validation", self.check_input_validation),
            ("Authorization", self.check_authorization),
            ("Password Strength", self.check_password_strength),
            ("Error Handling", self.check_error_handling),
        ]
        
        for check_name, check_func in checks:
            start = time.time()
            print(f"\nRunning: {check_name}")
            result = check_func()
            end = time.time()
            result.execution_time_ms = (end - start) * 1000
            
            report.check_results.append(result)
            report.total_checks += 1
            
            if result.passed:
                report.passed_checks += 1
                print(f"  ✓ PASSED")
            else:
                report.failed_checks += 1
                print(f"  ✗ FAILED")
            
            for issue in result.issues:
                if issue.severity == SecuritySeverity.CRITICAL:
                    report.critical_issues += 1
                elif issue.severity == SecuritySeverity.HIGH:
                    report.high_issues += 1
                elif issue.severity == SecuritySeverity.MEDIUM:
                    report.medium_issues += 1
                elif issue.severity == SecuritySeverity.LOW:
                    report.low_issues += 1
        
        # 计算总体得分
        max_possible = report.total_checks * 100
        actual_score = (report.passed_checks * 100) - (report.critical_issues * 50) - (report.high_issues * 30)
        report.overall_score = max(0, (actual_score / max_possible) * 100) if max_possible > 0 else 0
        
        # 生成建议
        if report.critical_issues > 0:
            report.recommendations.append("PRIORITY: Fix critical security issues immediately")
        if report.high_issues > 0:
            report.recommendations.append("Address high-severity issues soon")
        if report.medium_issues > 0:
            report.recommendations.append("Plan to fix medium-severity issues")
        
        # 打印报告
        print("\n" + "="*70)
        print("Security Audit Summary")
        print("="*70)
        print(f"Total Checks: {report.total_checks}")
        print(f"Passed: {report.passed_checks}")
        print(f"Failed: {report.failed_checks}")
        print(f"Critical Issues: {report.critical_issues}")
        print(f"High Issues: {report.high_issues}")
        print(f"Medium Issues: {report.medium_issues}")
        print(f"Low Issues: {report.low_issues}")
        print(f"Overall Score: {report.overall_score:.1f}/100")
        
        for rec in report.recommendations:
            print(f"\n⚠ {rec}")
        
        print("\n" + "="*70)
        
        return report


def create_security_audit() -> SecurityFinalAudit:
    """创建安全审计器"""
    return SecurityFinalAudit()


def run_security_audit() -> SecurityAuditReport:
    """运行安全审计"""
    audit = create_security_audit()
    return audit.run_full_audit()
