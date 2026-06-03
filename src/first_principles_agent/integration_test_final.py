"""
最终集成测试和系统完整性验证 - 第92阶段
完整的系统集成测试框架
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Callable
import time
from first_principles_agent import (
    Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction,
    ConfigManager, ConfigItem, ConfigType,
    PermissionManager, Permission, Role, User,
    ResourceType, PermissionType,
    info, warning, error
)


@dataclass
class IntegrationTestResult:
    """集成测试结果"""
    test_name: str
    passed: bool = False
    duration_ms: float = 0.0
    error_message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemIntegrityReport:
    """系统完整性报告"""
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    test_results: List[IntegrationTestResult] = field(default_factory=list)
    overall_score: float = 0.0
    generated_at: float = field(default_factory=time.time)
    recommendations: List[str] = field(default_factory=list)


class FinalIntegrationTester:
    """最终集成测试器"""
    
    def __init__(self):
        self.test_results: List[IntegrationTestResult] = []
    
    def test_core_agent_integration(self) -> IntegrationTestResult:
        """测试核心Agent集成"""
        result = IntegrationTestResult(test_name="Core Agent Integration")
        start = time.time()
        
        try:
            # 创建完整的Agent工作流
            quartet = TaskQuartet(
                target="完整集成测试",
                end_rule=lambda ctx: "final_result" in ctx
            )
            
            task = Task("integration_test", quartet, {
                "input_data": [1, 2, 3, 4, 5],
                "config": {"multiplier": 2}
            })
            
            agent = FirstPrinciplesAgent()
            agent.set_task(task)
            
            # 定义多步骤原子动作
            def validate_input(ctx):
                data = ctx["input_data"]
                return {"validated": all(isinstance(x, (int, float)) for x in data)}
            
            def process_data(ctx):
                multiplier = ctx["config"]["multiplier"]
                data = ctx["input_data"]
                return {"processed": [x * multiplier for x in data]}
            
            def aggregate_results(ctx):
                processed = ctx["processed"]
                return {
                    "sum": sum(processed),
                    "avg": sum(processed) / len(processed),
                    "count": len(processed)
                }
            
            def finalize(ctx):
                return {"final_result": {
                    "status": "complete",
                    "statistics": {
                        "sum": ctx["sum"],
                        "avg": ctx["avg"],
                        "count": ctx["count"]
                    }
                }}
            
            agent.set_atomic_actions([
                AtomicAction("validate", "验证输入", validate_input),
                AtomicAction("process", "处理数据", process_data),
                AtomicAction("aggregate", "聚合结果", aggregate_results),
                AtomicAction("finalize", "完成", finalize)
            ])
            
            execution_result = agent.execute()
            
            result.passed = execution_result.success
            result.details = {
                "execution_success": execution_result.success,
                "final_result": execution_result.context.get("final_result", {})
            }
            
        except Exception as e:
            result.error_message = str(e)
            result.passed = False
        
        result.duration_ms = (time.time() - start) * 1000
        self.test_results.append(result)
        return result
    
    def test_config_integration(self) -> IntegrationTestResult:
        """测试配置系统集成"""
        result = IntegrationTestResult(test_name="Config System Integration")
        start = time.time()
        
        try:
            config = ConfigManager()
            
            # 注册多个配置项
            config.register_config_item(ConfigItem(
                key="test.timeout",
                type_=ConfigType.INTEGER,
                default=30
            ))
            config.register_config_item(ConfigItem(
                key="test.debug",
                type_=ConfigType.BOOLEAN,
                default=False
            ))
            config.register_config_item(ConfigItem(
                key="test.name",
                type_=ConfigType.STRING,
                default="test"
            ))
            
            # 设置和获取配置
            config.set("test.timeout", 60)
            config.set("test.debug", True)
            config.set("test.name", "integration_test")
            
            timeout = config.get("test.timeout")
            debug = config.get("test.debug")
            name = config.get("test.name")
            
            # 验证
            result.passed = (timeout == 60 and debug == True and name == "integration_test")
            result.details = {
                "timeout": timeout,
                "debug": debug,
                "name": name
            }
            
        except Exception as e:
            result.error_message = str(e)
            result.passed = False
        
        result.duration_ms = (time.time() - start) * 1000
        self.test_results.append(result)
        return result
    
    def test_security_integration(self) -> IntegrationTestResult:
        """测试安全系统集成"""
        result = IntegrationTestResult(test_name="Security System Integration")
        start = time.time()
        
        try:
            pm = PermissionManager()
            
            # 创建用户和角色
            admin_user = pm.create_user("admin_user")
            normal_user = pm.create_user("normal_user")
            admin_role = pm.create_role("admin")
            user_role = pm.create_role("user")
            
            # 定义权限
            admin_perm = Permission(
                name="admin_access",
                resource_type=ResourceType.TASK,
                resource_id="all",
                permission_type=PermissionType.EXECUTE
            )
            read_perm = Permission(
                name="read_access",
                resource_type=ResourceType.TASK,
                resource_id="all",
                permission_type=PermissionType.READ
            )
            
            # 分配权限
            admin_role.add_permission(admin_perm)
            admin_role.add_permission(read_perm)
            user_role.add_permission(read_perm)
            
            admin_user.assign_role(admin_role)
            normal_user.assign_role(user_role)
            
            # 验证权限
            admin_has_exec = admin_user.has_permission(
                "admin_access",
                ResourceType.TASK,
                "all",
                PermissionType.EXECUTE
            )
            normal_has_exec = normal_user.has_permission(
                "admin_access",
                ResourceType.TASK,
                "all",
                PermissionType.EXECUTE
            )
            normal_has_read = normal_user.has_permission(
                "read_access",
                ResourceType.TASK,
                "all",
                PermissionType.READ
            )
            
            # admin应该有执行权限，normal用户不应该有执行权限但应该有读权限
            result.passed = (
                admin_has_exec == True and
                normal_has_exec == False and
                normal_has_read == True
            )
            result.details = {
                "admin_has_exec": admin_has_exec,
                "normal_has_exec": normal_has_exec,
                "normal_has_read": normal_has_read
            }
            
        except Exception as e:
            result.error_message = str(e)
            result.passed = False
        
        result.duration_ms = (time.time() - start) * 1000
        self.test_results.append(result)
        return result
    
    def test_logging_integration(self) -> IntegrationTestResult:
        """测试日志系统集成"""
        result = IntegrationTestResult(test_name="Logging System Integration")
        start = time.time()
        
        try:
            # 测试各级别日志
            info("Integration test info message")
            warning("Integration test warning message")
            error("Integration test error message")
            
            # 日志系统应该正常工作
            result.passed = True
            result.details = {
                "info_logged": True,
                "warning_logged": True,
                "error_logged": True
            }
            
        except Exception as e:
            result.error_message = str(e)
            result.passed = False
        
        result.duration_ms = (time.time() - start) * 1000
        self.test_results.append(result)
        return result
    
    def test_full_system_workflow(self) -> IntegrationTestResult:
        """测试完整系统工作流"""
        result = IntegrationTestResult(test_name="Full System Workflow")
        start = time.time()
        
        try:
            # 1. 配置系统
            config = ConfigManager()
            config.register_config_item(ConfigItem(
                key="workflow.enabled",
                type_=ConfigType.BOOLEAN,
                default=True
            ))
            config.set("workflow.enabled", True)
            
            # 2. 权限系统
            pm = PermissionManager()
            workflow_user = pm.create_user("workflow_user")
            workflow_role = pm.create_role("workflow_executor")
            exec_perm = Permission(
                name="execute_workflow",
                resource_type=ResourceType.TASK,
                resource_id="workflow_1",
                permission_type=PermissionType.EXECUTE
            )
            workflow_role.add_permission(exec_perm)
            workflow_user.assign_role(workflow_role)
            
            # 3. 核心Agent
            if config.get("workflow.enabled"):
                quartet = TaskQuartet(
                    target="完整系统工作流测试",
                    end_rule=lambda ctx: "workflow_complete" in ctx
                )
                task = Task("workflow_1", quartet, {"step": 1})
                agent = FirstPrinciplesAgent()
                agent.set_task(task)
                
                def execute_step(ctx):
                    info(f"Executing step {ctx['step']}")
                    return {"workflow_complete": True, "steps_executed": ctx["step"]}
                
                agent.set_atomic_actions([
                    AtomicAction("execute", "执行步骤", execute_step)
                ])
                
                exec_result = agent.execute()
                
                result.passed = exec_result.success
                result.details = {
                    "config_enabled": config.get("workflow.enabled"),
                    "permission_verified": workflow_user.has_permission(
                        "execute_workflow",
                        ResourceType.TASK,
                        "workflow_1",
                        PermissionType.EXECUTE
                    ),
                    "workflow_success": exec_result.success
                }
            else:
                result.passed = False
                result.error_message = "Workflow not enabled"
            
        except Exception as e:
            result.error_message = str(e)
            result.passed = False
        
        result.duration_ms = (time.time() - start) * 1000
        self.test_results.append(result)
        return result
    
    def run_all_tests(self) -> SystemIntegrityReport:
        """运行所有集成测试"""
        print("="*80)
        print("Final Integration Test Suite - Stage 92")
        print("="*80)
        
        tests = [
            ("Core Agent", self.test_core_agent_integration),
            ("Config System", self.test_config_integration),
            ("Security System", self.test_security_integration),
            ("Logging System", self.test_logging_integration),
            ("Full Workflow", self.test_full_system_workflow),
        ]
        
        for test_name, test_func in tests:
            print(f"\nRunning: {test_name}...")
            result = test_func()
            status = "✓ PASSED" if result.passed else "✗ FAILED"
            print(f"  {status} ({result.duration_ms:.2f}ms)")
            if not result.passed and result.error_message:
                print(f"  Error: {result.error_message}")
        
        # 生成报告
        report = SystemIntegrityReport()
        report.test_results = self.test_results.copy()
        report.total_tests = len(self.test_results)
        report.passed_tests = sum(1 for r in self.test_results if r.passed)
        report.failed_tests = report.total_tests - report.passed_tests
        
        if report.total_tests > 0:
            report.overall_score = (report.passed_tests / report.total_tests) * 100
        
        # 生成建议
        if report.failed_tests > 0:
            report.recommendations.append("Review failed tests and fix issues")
        if report.overall_score < 100:
            report.recommendations.append("Improve test coverage")
        
        print("\n" + "="*80)
        print("Integration Test Summary")
        print("="*80)
        print(f"Total Tests: {report.total_tests}")
        print(f"Passed: {report.passed_tests}")
        print(f"Failed: {report.failed_tests}")
        print(f"Score: {report.overall_score:.1f}/100")
        
        for rec in report.recommendations:
            print(f"\n⚠ {rec}")
        
        print("="*80)
        
        return report


def create_integration_tester() -> FinalIntegrationTester:
    """创建集成测试器"""
    return FinalIntegrationTester()


def run_final_integration_tests() -> SystemIntegrityReport:
    """运行最终集成测试"""
    tester = create_integration_tester()
    return tester.run_all_tests()