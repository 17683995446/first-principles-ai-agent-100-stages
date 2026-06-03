#!/usr/bin/env python3
"""
First Principles AI Agent - 完整集成示例
演示所有核心功能的组合使用
"""

import time
import sys

# 导入所有核心模块
from first_principles_agent import (
    # 任务建模
    Task, TaskQuartet, TaskStatus,
    # 拓扑拆解
    TopologicalDecomposer, TaskNode,
    # 原子动作
    AtomicConverger, AtomicAction, AtomicActionStatus,
    create_simple_action,
    # 验证层
    VerificationLayer, VerificationConfig,
    # 主控制器
    FirstPrinciplesAgent,
    # 调度器
    IntegratedTaskScheduler,
    # 重试管理
    RetryManager, RetryConfig, RetryStrategy,
    # 配置管理
    ConfigManager, ConfigItem, ConfigType,
    register_config_item, get, set, get_int,
    # 日志记录
    LogLevel, LogManager, MemoryHandler,
    get_logger, add_default_handler,
    info, warning, error, debug,
    # 权限管理
    PermissionManager, Permission, Role, User, Resource,
    PermissionType, ResourceType,
    create_user, assign_role, register_permission, register_role,
    grant_access, check_user_permission,
    # 监控管理
    MonitoringManager,
    create_monitoring_manager
)


def print_separator(title=""):
    """打印分隔符"""
    print("\n" + "="*70)
    if title:
        print(f"  {title}")
        print("="*70)


# ==============
# 示例1: 完整的四元架构示例
# ==============
def example_1_full_architecture():
    """演示完整的四元架构使用"""
    print_separator("示例 1: 完整四元架构")

    # 1. 创建任务四元组
    def end_condition(ctx):
        return "final_result" in ctx and ctx["final_result"] >= 100

    quartet = TaskQuartet(
        target="Calculate (a + b) * c * d",
        end_rule=end_condition
    )

    # 2. 创建主任务
    main_task = Task(
        "calculate",
        quartet,
        context={"a": 5, "b": 10, "c": 2, "d": 3}
    )

    # 3. 创建 Agent
    agent = FirstPrinciplesAgent()
    agent.set_task(main_task)

    # 4. 创建子任务（带依赖）
    # 步骤1: a + b
    step1_quartet = TaskQuartet(target="Add a and b")
    step1 = Task("step1_add", step1_quartet)
    
    # 步骤2: * c
    step2_quartet = TaskQuartet(target="Multiply by c")
    step2 = Task("step2_multiply_c", step2_quartet)
    
    # 步骤3: * d
    step3_quartet = TaskQuartet(target="Multiply by d")
    step3 = Task("step3_multiply_d", step3_quartet)

    # 添加子任务，建立依赖关系
    agent.add_subtask(step1)
    agent.add_subtask(step2, dependencies=["step1_add"])
    agent.add_subtask(step3, dependencies=["step2_multiply_c"])

    # 5. 创建原子动作
    def add_ab(ctx):
        return {"sum_ab": ctx["a"] + ctx["b"]}
    
    def multiply_by_c(ctx):
        return {"product_c": ctx["sum_ab"] * ctx["c"]}
    
    def multiply_by_d(ctx):
        return {"final_result": ctx["product_c"] * ctx["d"]}

    action1 = AtomicAction("add_ab", "Add a + b", add_ab)
    action2 = AtomicAction("multiply_c", "Multiply by c", multiply_by_c)
    action3 = AtomicAction("multiply_d", "Multiply by d", multiply_by_d)

    agent.set_atomic_actions([action1, action2, action3])

    # 6. 执行
    print("\n开始执行任务...")
    result = agent.execute()

    # 7. 查看结果
    print(f"\n执行结果:")
    print(f"  Success: {result.success}")
    print(f"  Final Result: {result.context.get('final_result')}")
    print(f"  Execution Time: {result.end_time - result.start_time:.4f}s")
    
    return result


# ==============
# 示例2: 配置管理集成
# ==============
def example_2_config_integration():
    """演示配置管理集成使用"""
    print_separator("示例 2: 配置管理集成")

    # 1. 注册配置项
    config_items = [
        ConfigItem(
            key="app.mode",
            type_=ConfigType.STRING,
            default="development",
            description="运行模式"
        ),
        ConfigItem(
            key="app.max_retries",
            type_=ConfigType.INTEGER,
            default=3,
            description="最大重试次数"
        ),
        ConfigItem(
            key="app.debug",
            type_=ConfigType.BOOLEAN,
            default=True,
            description="调试模式"
        ),
        ConfigItem(
            key="app.features",
            type_=ConfigType.LIST,
            default=["logging", "monitoring"],
            description="启用的功能"
        )
    ]

    for item in config_items:
        register_config_item(item)

    # 2. 使用全局API访问配置
    print("\n当前配置:")
    print(f"  Mode: {get('app.mode')}")
    print(f"  Max Retries: {get_int('app.max_retries')}")
    print(f"  Debug: {get('app.debug')}")
    print(f"  Features: {get('app.features')}")

    # 3. 修改配置
    set("app.mode", "production")
    set("app.max_retries", 5)
    
    print("\n更新后配置:")
    print(f"  Mode: {get('app.mode')}")
    print(f"  Max Retries: {get_int('app.max_retries')}")

    return True


# ==============
# 示例3: 日志与审计集成
# ==============
def example_3_logging_audit():
    """演示日志与审计集成"""
    print_separator("示例 3: 日志与审计")

    # 1. 配置日志
    memory_handler = MemoryHandler(LogLevel.DEBUG)
    add_default_handler(memory_handler)

    # 2. 记录日志
    debug("这是调试信息")
    info("应用启动成功")
    warning("发现潜在问题")
    error("发生了错误")

    # 3. 创建用户和角色
    register_permission(Permission(
        name="task.execute",
        type_=PermissionType.EXECUTE,
        resource_type=ResourceType.TASK
    ))
    register_role(Role(
        name="operator",
        permissions={"task.execute"}
    ))

    user = create_user("operator_001", department="engineering")
    assign_role(user.id, "operator")

    # 4. 授予权限
    resource = Resource(
        id="job_001",
        type_=ResourceType.TASK,
        name="Data Processing Job",
        owner_id=user.id
    )
    register_permission(Permission("task.execute", PermissionType.EXECUTE, ResourceType.TASK))
    grant_access(
        principal=user.id,
        principal_type="user",
        resource_id="job_001",
        permission=PermissionType.EXECUTE
    )

    # 5. 检查权限并记录审计
    has_perm = check_user_permission(user.id, "job_001", PermissionType.EXECUTE)
    print(f"\n权限检查: {'通过' if has_perm else '拒绝'}")

    # 查看日志
    records = memory_handler.get_records()
    print(f"\n日志记录数: {len(records)}")
    
    return True


# ==============
# 示例4: 重试机制集成
# ==============
def example_4_retry_integration():
    """演示重试机制集成"""
    print_separator("示例 4: 重试机制")

    # 1. 配置重试管理器
    retry_config = RetryConfig(
        max_retries=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        initial_delay=0.1,
        max_delay=1.0
    )
    retry_manager = RetryManager(retry_config)

    # 2. 创建一个不稳定的操作
    attempt_count = 0
    
    def unstable_operation():
        nonlocal attempt_count
        attempt_count += 1
        
        if attempt_count < 3:
            print(f"  尝试 {attempt_count}: 失败 (模拟错误)")
            raise Exception(f"Simulated error at attempt {attempt_count}")
        
        print(f"  尝试 {attempt_count}: 成功!")
        return {"success": True, "attempts": attempt_count}

    # 3. 执行带重试的操作
    print("\n执行带重试的操作...")
    try:
        result = retry_manager.execute_with_retry(unstable_operation)
        print(f"\n最终结果: {result}")
    except Exception as e:
        print(f"\n最终失败: {e}")

    return True


# ==============
# 示例5: 监控集成
# ==============
def example_5_monitoring():
    """演示监控集成"""
    print_separator("示例 5: 系统监控")

    # 1. 创建监控管理器
    monitor = create_monitoring_manager()

    # 2. 记录各种指标
    print("\n记录监控指标...")
    monitor.record_counter("requests.total", 1)
    monitor.record_gauge("system.cpu", 0.35)
    monitor.record_gauge("system.memory", 0.62)
    monitor.record_distribution("response.time", 120)
    monitor.record_distribution("response.time", 150)
    monitor.record_distribution("response.time", 90)

    # 3. 获取统计数据
    cpu_stats = monitor.get_statistics("system.cpu", 3600)
    resp_stats = monitor.get_statistics("response.time", 3600)

    print(f"\n监控统计:")
    print(f"  CPU (当前): {cpu_stats.get('current', 0):.2%}")
    print(f"  响应时间 (p95): {resp_stats.get('p95', 0):.2f}ms")
    print(f"  总请求数: {monitor.get_gauge('requests.total')}")

    return True


# ==============
# 示例6: 完整的端到端工作流
# ==============
def example_6_end_to_end():
    """演示完整的端到端工作流"""
    print_separator("示例 6: 端到端工作流")

    print("\n=== 第1步: 配置系统 ===")
    register_config_item(ConfigItem(
        key="workflow.max_concurrent",
        type_=ConfigType.INTEGER,
        default=5
    ))
    set("workflow.max_concurrent", 3)
    print(f"  配置完成: max_concurrent = {get_int('workflow.max_concurrent')}")

    print("\n=== 第2步: 设置权限 ===")
    register_permission(Permission("workflow.run", PermissionType.EXECUTE, ResourceType.SYSTEM))
    register_role(Role("workflow_admin", permissions={"workflow.run"}))
    user = create_user("workflow_user")
    assign_role(user.id, "workflow_admin")
    print(f"  权限设置完成: 用户 {user.id} 获得 workflow_admin 角色")

    print("\n=== 第3步: 创建任务工作流 ===")
    
    def workflow_end(ctx):
        return "workflow_complete" in ctx and ctx["workflow_complete"]

    workflow_quartet = TaskQuartet(
        target="Data processing pipeline",
        end_rule=workflow_end
    )

    workflow_task = Task(
        "data_pipeline",
        workflow_quartet,
        context={"input_file": "data.csv", "output_dir": "/tmp/results"}
    )

    agent = FirstPrinciplesAgent()
    agent.set_task(workflow_task)

    # 创建处理步骤
    validate_task = Task("validate", TaskQuartet(target="Validate input data"))
    process_task = Task("process", TaskQuartet(target="Process data"))
    save_task = Task("save", TaskQuartet(target="Save results"))

    agent.add_subtask(validate_task)
    agent.add_subtask(process_task, dependencies=["validate"])
    agent.add_subtask(save_task, dependencies=["process"])

    # 创建动作
    def validate_data(ctx):
        info("验证输入数据...")
        return {"validated": True, "record_count": 1000}
    
    def process_data(ctx):
        info("处理数据...")
        time.sleep(0.1)
        return {"processed": True, "records_processed": 1000}
    
    def save_results(ctx):
        info("保存结果...")
        return {"saved": True, "workflow_complete": True}

    agent.set_atomic_actions([
        AtomicAction("validate", "Validate", validate_data),
        AtomicAction("process", "Process", process_data),
        AtomicAction("save", "Save", save_results)
    ])

    print("  工作流创建完成")

    print("\n=== 第4步: 执行工作流 ===")
    result = agent.execute()

    print(f"\n=== 第5步: 工作流完成 ===")
    print(f"  执行成功: {result.success}")
    print(f"  执行时间: {(result.end_time - result.start_time) * 1000:.2f}ms")
    
    return result


# ==============
# 主函数
# ==============
def main():
    """运行所有示例"""
    print("="*70)
    print("  First Principles AI Agent - 完整集成示例")
    print("="*70)
    print(f"  Python 版本: {sys.version}")
    print(f"  运行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 运行示例
        example_1_full_architecture()
        example_2_config_integration()
        example_3_logging_audit()
        example_4_retry_integration()
        example_5_monitoring()
        example_6_end_to_end()

        print_separator("所有示例完成!")
        print("\n✅ 所有示例执行成功!")
        print("\n提示: 查看以下文件了解更多:")
        print("  - QUICKSTART.md: 快速开始指南")
        print("  - README.md: 完整项目文档")
        print("  - examples/: 更多示例代码")
        print("  - stages/: 各阶段开发文档")

        return 0

    except Exception as e:
        print(f"\n❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
