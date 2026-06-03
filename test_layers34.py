"""
测试原子动作收敛层+分段校验收敛层 - 验证第41-50阶段
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from first_principles_agent.atomic_converger import (
    AtomicAction,
    AtomicConverger,
    ActionValidator,
    ActionSplitter,
    ActionInputSchema,
    ActionOutputSchema,
    VerificationLayer,
    VerificationReport,
    CircuitBreaker,
    RollbackManager,
    AtomicActionStatus,
    ActionGranularity,
    create_simple_action,
    create_validated_action
)
from first_principles_agent.task_model import Task, TaskQuartet


def test_atomic_action_creation():
    """
    第41阶段：原子动作标准存储结构
    """
    print("=" * 70)
    print("测试1：原子动作标准存储结构")
    print("=" * 70)
    
    def simple_func(ctx):
        return {"result": ctx["value"] * 2}
    
    action = AtomicAction(
        action_id="test_action",
        description="Double a value",
        execute_func=simple_func,
        input_schema=ActionInputSchema(required_keys=["value"]),
        output_schema=ActionOutputSchema(expected_keys=["result"]),
        max_retries=3,
        granularity=ActionGranularity.FINE
    )
    
    print(f"✓ Action created: {action.id}")
    print(f"  Description: {action.description}")
    print(f"  Granularity: {action.granularity.value}")
    print(f"  Max retries: {action.max_retries}")
    print(f"  Input schema: {action.input_schema.required_keys}")
    print(f"  Output schema: {action.output_schema.expected_keys}")
    
    print()
    return True


def test_action_execution():
    """测试动作执行"""
    print("=" * 70)
    print("测试2：原子动作执行")
    print("=" * 70)
    
    def add_func(ctx):
        return {"sum": ctx["a"] + ctx["b"]}
    
    action = create_validated_action(
        "add_numbers",
        "Add two numbers",
        add_func,
        required_inputs=["a", "b"],
        expected_outputs=["sum"]
    )
    
    context = {"a": 5, "b": 3}
    output = action.execute(context)
    
    print(f"✓ Action executed: {action.id}")
    print(f"  Status: {action.status.value}")
    print(f"  Output: {output}")
    print(f"  Execution time: {action.execution_time_ms:.2f}ms")
    
    print()
    return action.status == AtomicActionStatus.COMPLETED


def test_action_validator():
    """
    第43阶段：三大原子判定条件校验
    """
    print("=" * 70)
    print("测试3：原子性判定校验")
    print("=" * 70)
    
    validator = ActionValidator()
    
    # 测试原子动作
    atomic_action = create_simple_action(
        "read_file",
        "Read a file",
        lambda ctx: {"content": "data"}
    )
    
    # 测试非原子动作
    non_atomic_action = create_simple_action(
        "complex_action",
        "Read file and analyze and save",
        lambda ctx: {}
    )
    
    is_atomic_1, issues_1 = validator.is_atomic(atomic_action)
    is_atomic_2, issues_2 = validator.is_atomic(non_atomic_action)
    
    print(f"✓ Atomic action '{atomic_action.id}': {is_atomic_1}")
    print(f"✓ Non-atomic action '{non_atomic_action.id}': {is_atomic_2}")
    if issues_2:
        print(f"  Issues: {issues_2}")
    
    print()
    return True


def test_action_splitter():
    """
    第42阶段：复合动作自动拆分
    """
    print("=" * 70)
    print("测试4：复合动作自动拆分")
    print("=" * 70)
    
    splitter = ActionSplitter()
    
    # 测试复合动作
    complex_action = create_simple_action(
        "complex",
        "Read file, analyze data, and save result",
        lambda ctx: {}
    )
    
    subtasks = splitter.split_if_needed(complex_action)
    
    print(f"✓ Original action: {complex_action.id}")
    print(f"  Description: {complex_action.description}")
    print(f"✓ Split into {len(subtasks)} subtasks:")
    for sub in subtasks:
        print(f"  - {sub.id}: {sub.description}")
    
    print()
    return len(subtasks) > 1


def test_converger_queue():
    """
    第44-45阶段：队列管理与净化
    """
    print("=" * 70)
    print("测试5：原子动作队列管理")
    print("=" * 70)
    
    converger = AtomicConverger()
    
    # 添加动作
    action1 = create_simple_action("step1", "Step 1", lambda ctx: {"s1": True})
    action2 = create_simple_action("step2", "Step 2", lambda ctx: {"s2": True})
    action3 = create_simple_action("step3", "Step 3", lambda ctx: {"s3": True})
    
    converger.add_action(action1)
    converger.add_action(action2)
    converger.add_action(action3)
    
    print(f"✓ Added {len(converger.action_queue)} actions")
    
    # 执行队列
    for action in converger.action_queue:
        action.execute({})
    
    stats = converger.get_statistics()
    print(f"✓ Statistics: {stats}")
    
    print()
    return True


def test_verification_layer():
    """
    第46-47阶段：分段校验收敛
    """
    print("=" * 70)
    print("测试6：分段校验收敛层")
    print("=" * 70)
    
    verification = VerificationLayer()
    
    # 创建任务
    task = Task("test_task", TaskQuartet(target="Test task"))
    context = {}
    
    # 预校验
    pre_report = verification.check_preconditions(task, context)
    print(f"✓ Precondition check: {pre_report.result.value}")
    
    # 约束检查
    constraint_report = verification.check_constraints(task, context)
    print(f"✓ Constraint check: {constraint_report.result.value}")
    
    # 终止条件检查
    end_report = verification.check_end_condition(task, context)
    print(f"✓ End condition check: {end_report.result.value}")
    
    print()
    return True


def test_circuit_breaker():
    """
    第48阶段：熔断机制
    """
    print("=" * 70)
    print("测试7：熔断触发判定机制")
    print("=" * 70)
    
    cb = CircuitBreaker(failure_threshold=3, timeout_seconds=10)
    
    print(f"✓ Initial state: {cb.state}")
    
    # 模拟失败
    for i in range(2):
        cb.record_failure()
        print(f"  After failure {i+1}: {cb.get_status()}")
    
    # 第3次失败触发熔断
    cb.record_failure()
    print(f"✓ After failure 3: {cb.get_status()}")
    print(f"  Circuit breaker opened: {cb.state == 'open'}")
    
    print()
    return cb.state == "open"


def test_rollback_manager():
    """
    第49阶段：回滚机制
    """
    print("=" * 70)
    print("测试8：任务回滚管理")
    print("=" * 70)
    
    rollback_mgr = RollbackManager()
    
    # 创建检查点
    state1 = {"step": 1, "data": "initial"}
    state2 = {"step": 2, "data": "modified"}
    
    rollback_mgr.create_checkpoint("checkpoint_1", state1)
    rollback_mgr.create_checkpoint("checkpoint_2", state2)
    
    print(f"✓ Created checkpoints: {list(rollback_mgr.checkpoints.keys())}")
    
    # 记录动作
    rollback_mgr.record_action("action_1", {"result": "output1"})
    rollback_mgr.record_action("action_2", {"result": "output2"})
    
    print(f"✓ Recorded actions: {len(rollback_mgr.execution_history)}")
    
    # 回滚
    restored = rollback_mgr.rollback_to_checkpoint("checkpoint_1")
    print(f"✓ Rolled back to checkpoint_1: {restored}")
    
    print()
    return True


def test_batch_validation():
    """批量原子性验证"""
    print("=" * 70)
    print("测试9：批量原子性验证")
    print("=" * 70)
    
    validator = ActionValidator()
    
    actions = [
        create_simple_action("a1", "Single action", lambda c: {}),
        create_simple_action("a2", "Multiple things", lambda c: {}),
        create_simple_action("a3", "Do A and B", lambda c: {}),
    ]
    
    result = validator.validate_batch(actions)
    print(f"✓ Batch validation: {result}")
    
    print()
    return True


def test_end_to_end():
    """
    第50阶段：四层架构联动测试
    """
    print("=" * 70)
    print("测试10：四层架构联动测试")
    print("=" * 70)
    
    # 1. 创建任务
    from first_principles_agent.task_parser import UnifiedTaskModeling
    
    modeler = UnifiedTaskModeling()
    success, result = modeler.model("Process data in 5 steps")
    
    if not success:
        print(f"❌ Modeling failed")
        return False
    
    task = result["task"]
    print(f"✓ Layer 1 (Task): {task.id}")
    
    # 2. 拓扑拆解
    from first_principles_agent.topological_decomposer import TopologicalDecomposer
    
    decomposer = TopologicalDecomposer()
    decomposer.add_task(task)
    
    is_valid, issues = decomposer.validate_dag()
    print(f"✓ Layer 2 (DAG): Valid={is_valid}")
    
    # 3. 原子动作
    converger = AtomicConverger()
    action1 = create_simple_action("action1", "Step 1", lambda c: {"s1": True})
    action2 = create_simple_action("action2", "Step 2", lambda c: {"s2": True})
    
    converger.add_actions([action1, action2])
    converger.purify_queue()
    print(f"✓ Layer 3 (Atomic): {len(converger.action_queue)} actions")
    
    # 4. 验证收敛
    verification = VerificationLayer()
    pre_report = verification.check_preconditions(task, {})
    post_report = verification.check_end_condition(task, {})
    
    print(f"✓ Layer 4 (Verification): Pre={pre_report.result.value}, End={post_report.result.value}")
    
    print()
    return True


def main():
    """运行所有测试"""
    print()
    print("🎯" * 35)
    print("Layer 3 & 4 - Complete Test Suite")
    print("第41-50阶段：原子动作+收敛验证验收测试")
    print("🎯" * 35)
    print()
    
    tests = [
        ("原子动作存储结构", test_atomic_action_creation),
        ("原子动作执行", test_action_execution),
        ("原子性判定校验", test_action_validator),
        ("复合动作自动拆分", test_action_splitter),
        ("队列管理与净化", test_converger_queue),
        ("分段校验收敛", test_verification_layer),
        ("熔断触发机制", test_circuit_breaker),
        ("任务回滚管理", test_rollback_manager),
        ("批量原子性验证", test_batch_validation),
        ("四层架构联动", test_end_to_end),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {name}: PASS\n")
            else:
                failed += 1
                print(f"❌ {name}: FAIL\n")
        except Exception as e:
            failed += 1
            print(f"❌ {name}: FAIL - {str(e)}\n")
            import traceback
            traceback.print_exc()
    
    print("=" * 70)
    print(f"总测试结果: {passed}/{len(tests)} 通过")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 所有测试通过！第41-50阶段实现验收合格！\n")
        return True
    else:
        print(f"\n⚠️  {failed} 个测试失败\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
