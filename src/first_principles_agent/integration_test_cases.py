"""
集成测试用例 - 第83阶段
核心模块间的集成测试
"""

import time
import threading
from typing import List, Callable

from first_principles_agent.integration_tests import (
    IntegrationLevel, DefectSeverity, DefectType,
    IntegrationTestCase, IntegrationTestRunner,
    SystemHealthMonitor, create_integration_test
)
from first_principles_agent import (
    Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction,
    ConfigManager, ConfigItem, ConfigType,
    PermissionManager, Permission, Role, User, Resource,
    PermissionType, ResourceType,
    TaskScheduler, QueuedTask, TaskPriority,
    RetryManager, RetryConfig, RetryStrategy,
    info, warning, error, debug
)


def create_core_integration_tests() -> IntegrationTestRunner:
    """创建核心集成测试套件"""
    runner = IntegrationTestRunner("Core Integration Tests")
    
    # 添加核心集成测试
    runner.add_tests([
        # 1. 任务与配置集成测试
        create_task_config_integration_test(),
        
        # 2. 任务与权限集成测试
        create_task_permission_integration_test(),
        
        # 3. 配置与日志集成测试
        create_config_logging_integration_test(),
        
        # 4. 调度器与任务集成测试
        create_scheduler_task_integration_test(),
        
        # 5. 重试与任务集成测试
        create_retry_task_integration_test(),
        
        # 6. 多模块并发集成测试
        create_concurrent_integration_test(),
        
        # 7. 端到端工作流测试
        create_e2e_workflow_integration_test(),
    ])
    
    return runner


def create_task_config_integration_test() -> IntegrationTestCase:
    """任务与配置集成测试"""
    config_manager = ConfigManager()
    setup_count = [0]
    teardown_count = [0]
    
    def setup():
        """设置"""
        setup_count[0] += 1
        # 注册测试配置
        config_manager.register_config_item(ConfigItem(
            key="test.task.timeout",
            type_=ConfigType.INTEGER,
            default=30
        ))
        config_manager.register_config_item(ConfigItem(
            key="test.task.retries",
            type_=ConfigType.INTEGER,
            default=3
        ))
    
    def test_function():
        """测试函数"""
        # 创建任务
        quartet = TaskQuartet(
            target="Test Task with Config",
            end_rule=lambda ctx: "result" in ctx
        )
        task = Task("config_test_task", quartet, context={"a": 10, "b": 20})
        
        # 从配置读取参数
        timeout = config_manager.get_int("test.task.timeout", 30)
        
        agent = FirstPrinciplesAgent()
        agent.set_task(task)
        
        # 添加动作
        def add_func(ctx):
            return {"result": ctx["a"] + ctx["b"]}
        
        action = AtomicAction("add", "Add", add_func)
        agent.set_atomic_actions([action])
        
        # 执行
        result = agent.execute()
        
        # 验证
        assert result.success, "Task execution failed"
        assert "result" in result.context, "Result not in context"
        assert result.context["result"] == 30, f"Expected 30, got {result.context['result']}"
    
    def teardown():
        """清理"""
        teardown_count[0] += 1
    
    return create_integration_test(
        name="Task-Config Integration",
        test_function=test_function,
        modules=["task_model", "config"],
        level=IntegrationLevel.MODULES,
        description="测试任务模块与配置模块的集成",
        setup=setup,
        teardown=teardown,
        timeout=30.0
    )


def create_task_permission_integration_test() -> IntegrationTestCase:
    """任务与权限集成测试"""
    permission_manager = PermissionManager()
    
    def setup():
        """设置"""
        # 注册权限
        permission_manager.register_permission(Permission(
            name="task.execute",
            type_=PermissionType.EXECUTE,
            resource_type=ResourceType.TASK
        ))
        
        # 创建用户
        user = permission_manager.create_user("test_user_perm")
        permission_manager.assign_role(user.id, "admin")
        
        # 授予资源访问权限
        resource = Resource(
            id="test_resource_001",
            type_=ResourceType.TASK,
            name="Test Resource"
        )
        permission_manager.register_resource(resource)
    
    def test_function():
        """测试函数"""
        # 获取用户
        user = permission_manager.get_user_by_name("test_user_perm")
        assert user is not None, "User not found"
        
        # 创建任务
        quartet = TaskQuartet(target="Permission Test Task")
        task = Task("permission_test_task", quartet)
        agent = FirstPrinciplesAgent()
        agent.set_task(task)
        
        # 添加动作
        def simple_func(ctx):
            return {"executed": True}
        
        action = AtomicAction("simple", "Simple", simple_func)
        agent.set_atomic_actions([action])
        
        # 检查权限
        has_perm = permission_manager.check_user_permission(
            user.id, "test_resource_001", PermissionType.EXECUTE
        )
        
        # 执行任务
        result = agent.execute()
        
        assert result.success, "Task execution failed"
        assert user.is_active, "User should be active"
    
    def teardown():
        """清理"""
        pass
    
    return create_integration_test(
        name="Task-Permission Integration",
        test_function=test_function,
        modules=["task_model", "security"],
        level=IntegrationLevel.MODULES,
        description="测试任务模块与权限模块的集成",
        setup=setup,
        teardown=teardown,
        timeout=30.0
    )


def create_config_logging_integration_test() -> IntegrationTestCase:
    """配置与日志集成测试"""
    config_manager = ConfigManager()
    log_messages = []
    
    def setup():
        """设置"""
        config_manager.register_config_item(ConfigItem(
            key="test.log.level",
            type_=ConfigType.STRING,
            default="INFO"
        ))
    
    def test_function():
        """测试函数"""
        # 获取日志级别配置
        log_level = config_manager.get("test.log.level", "INFO")
        
        # 记录日志
        info(f"Testing log integration with level: {log_level}")
        warning(f"Warning message from integration test")
        error(f"Error message from integration test")
        
        # 验证日志记录
        log_messages.append(f"Log level: {log_level}")
        
        assert len(log_messages) > 0, "No log messages recorded"
    
    def teardown():
        """清理"""
        log_messages.clear()
    
    return create_integration_test(
        name="Config-Logging Integration",
        test_function=test_function,
        modules=["config", "logging"],
        level=IntegrationLevel.MODULES,
        description="测试配置模块与日志模块的集成",
        setup=setup,
        teardown=teardown,
        timeout=30.0
    )


def create_scheduler_task_integration_test() -> IntegrationTestCase:
    """调度器与任务集成测试"""
    scheduler = TaskScheduler()
    execution_results = []
    
    def setup():
        """设置"""
        scheduler.start()
    
    def test_function():
        """测试函数"""
        # 创建任务
        for i in range(5):
            task = QueuedTask(
                task_id=f"scheduled_task_{i}",
                priority=TaskPriority.NORMAL,
                task_data={"index": i}
            )
            scheduler.enqueue(task)
        
        # 等待任务执行
        time.sleep(2)
        
        # 验证任务队列状态
        status = scheduler.get_status()
        
        assert status is not None, "Failed to get scheduler status"
        assert "total_enqueued" in status, "Missing total_enqueued"
        
        # 清理
        scheduler.stop()
    
    def teardown():
        """清理"""
        if scheduler.is_running():
            scheduler.stop()
        execution_results.clear()
    
    return create_integration_test(
        name="Scheduler-Task Integration",
        test_function=test_function,
        modules=["task_scheduler", "task_model"],
        level=IntegrationLevel.MODULES,
        description="测试调度器模块与任务模块的集成",
        setup=setup,
        teardown=teardown,
        timeout=30.0
    )


def create_retry_task_integration_test() -> IntegrationTestCase:
    """重试与任务集成测试"""
    retry_manager = RetryManager(RetryConfig(
        max_retries=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        initial_delay=0.1
    ))
    attempt_count = [0]
    
    def setup():
        """设置"""
        attempt_count[0] = 0
    
    def test_function():
        """测试函数"""
        def unstable_operation():
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise RuntimeError(f"Simulated failure at attempt {attempt_count[0]}")
            return {"success": True, "attempts": attempt_count[0]}
        
        # 执行带重试的操作
        result = retry_manager.execute_with_retry(unstable_operation)
        
        assert result is not None, "Result should not be None"
        assert attempt_count[0] == 3, f"Expected 3 attempts, got {attempt_count[0]}"
    
    def teardown():
        """清理"""
        attempt_count[0] = 0
    
    return create_integration_test(
        name="Retry-Task Integration",
        test_function=test_function,
        modules=["retry_handler", "task_model"],
        level=IntegrationLevel.MODULES,
        description="测试重试模块与任务模块的集成",
        setup=setup,
        teardown=teardown,
        timeout=30.0
    )


def create_concurrent_integration_test() -> IntegrationTestCase:
    """多模块并发集成测试"""
    results = {"success": False}
    
    def setup():
        """设置"""
        results["success"] = False
    
    def test_function():
        """测试函数"""
        def worker(worker_id: int):
            """工作线程"""
            try:
                # 1. 创建任务
                quartet = TaskQuartet(target=f"Concurrent Task {worker_id}")
                task = Task(f"concurrent_task_{worker_id}", quartet)
                agent = FirstPrinciplesAgent()
                agent.set_task(task)
                
                # 2. 配置
                config_manager = ConfigManager()
                config_manager.register_config_item(ConfigItem(
                    key=f"worker.{worker_id}.count",
                    type_=ConfigType.INTEGER,
                    default=0
                ))
                config_manager.set(f"worker.{worker_id}.count", worker_id)
                
                # 3. 记录日志
                info(f"Worker {worker_id} executing")
                
                # 4. 执行
                result = agent.execute()
                
                return result.success
            except Exception as e:
                error(f"Worker {worker_id} failed: {e}")
                return False
        
        # 并发执行
        threads = []
        thread_results = []
        
        for i in range(10):
            t = threading.Thread(target=lambda idx=i: thread_results.append(worker(idx)))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=5.0)
        
        # 验证
        success_count = sum(1 for r in thread_results if r)
        assert success_count > 0, "No successful executions"
        
        results["success"] = True
    
    def teardown():
        """清理"""
        results["success"] = False
    
    return create_integration_test(
        name="Concurrent Multi-Module Integration",
        test_function=test_function,
        modules=["task_model", "config", "logging", "orchestrator"],
        level=IntegrationLevel.SYSTEM,
        description="测试多模块并发集成",
        setup=setup,
        teardown=teardown,
        timeout=60.0
    )


def create_e2e_workflow_integration_test() -> IntegrationTestCase:
    """端到端工作流集成测试"""
    
    def setup():
        """设置"""
        pass
    
    def test_function():
        """端到端工作流"""
        # 1. 配置阶段
        config_manager = ConfigManager()
        config_manager.register_config_item(ConfigItem(
            key="workflow.max_steps",
            type_=ConfigType.INTEGER,
            default=10
        ))
        config_manager.set("workflow.max_steps", 5)
        
        # 2. 权限阶段
        permission_manager = PermissionManager()
        permission_manager.register_permission(Permission(
            name="workflow.execute",
            type_=PermissionType.EXECUTE,
            resource_type=ResourceType.SYSTEM
        ))
        
        # 3. 创建工作流任务
        workflow_quartet = TaskQuartet(
            target="End-to-End Workflow",
            end_rule=lambda ctx: "workflow_complete" in ctx and ctx["workflow_complete"]
        )
        workflow_task = Task("e2e_workflow", workflow_quartet, context={
            "input": "test_data",
            "steps": []
        })
        
        agent = FirstPrinciplesAgent()
        agent.set_task(workflow_task)
        
        # 4. 添加工作流步骤
        step1 = Task("validate", TaskQuartet(target="Validate input"))
        step2 = Task("process", TaskQuartet(target="Process data"))
        step3 = Task("save", TaskQuartet(target="Save result"))
        
        agent.add_subtask(step1)
        agent.add_subtask(step2, dependencies=["validate"])
        agent.add_subtask(step3, dependencies=["process"])
        
        # 5. 定义动作
        def validate_action(ctx):
            info("Validating input...")
            return {"validated": True}
        
        def process_action(ctx):
            info("Processing data...")
            return {"processed": True}
        
        def save_action(ctx):
            info("Saving result...")
            return {"saved": True, "workflow_complete": True}
        
        actions = [
            AtomicAction("validate", "Validate", validate_action),
            AtomicAction("process", "Process", process_action),
            AtomicAction("save", "Save", save_action)
        ]
        agent.set_atomic_actions(actions)
        
        # 6. 执行工作流
        result = agent.execute()
        
        # 7. 验证结果
        assert result.success, "Workflow execution failed"
        assert result.context.get("workflow_complete") == True, "Workflow not complete"
        assert result.context.get("validated") == True, "Validation not completed"
        assert result.context.get("processed") == True, "Processing not completed"
        assert result.context.get("saved") == True, "Saving not completed"
    
    def teardown():
        """清理"""
        pass
    
    return create_integration_test(
        name="End-to-End Workflow Integration",
        test_function=test_function,
        modules=["task_model", "config", "security", "logging", "orchestrator"],
        level=IntegrationLevel.E2E,
        description="端到端工作流集成测试",
        setup=setup,
        teardown=teardown,
        timeout=120.0
    )


def run_all_integration_tests():
    """运行所有集成测试"""
    print("="*70)
    print("Running Core Integration Tests (Stage 83)")
    print("="*70)
    
    runner = create_core_integration_tests()
    results = runner.run_all()
    
    print("\n" + "="*70)
    print("Integration Test Results")
    print("="*70)
    
    for result in results:
        print(f"\nTest: {result.test_name}")
        print(f"  Status: {result.status.value}")
        print(f"  Duration: {result.duration:.2f}s")
        
        if result.error_message:
            print(f"  Error: {result.error_message}")
    
    # 生成摘要
    summary = runner.get_summary()
    print("\n" + "="*70)
    print("Summary")
    print("="*70)
    print(f"Total: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Errors: {summary['error']}")
    print(f"Timeouts: {summary['timeout']}")
    
    # 生成缺陷报告
    if summary['defects']['total'] > 0:
        print("\n" + "="*70)
        print(runner.generate_defect_report())
    else:
        print("\n✓ No defects found!")
    
    return runner
