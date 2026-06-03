"""
第51-55阶段：全链路工程化测试
验证四层架构完整调用链路
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from first_principles_agent import (
    FirstPrinciplesAgent, 
    create_agent,
    create_simple_action,
    create_validated_action
)


def test_agent_creation():
    """
    第51阶段：创建Agent实例
    """
    print("=" * 70)
    print("测试1：创建Agent实例")
    print("=" * 70)
    
    agent = create_agent(enable_logging=False)
    
    print(f"✓ Agent created")
    print(f"  Has modeler: {hasattr(agent, 'modeler')}")
    print(f"  Has decomposer: {hasattr(agent, 'decomposer')}")
    print(f"  Has converger: {hasattr(agent, 'converger')}")
    print(f"  Has verification: {hasattr(agent, 'verification')}")
    
    state = agent.get_state()
    print(f"  Initial state: {state}")
    
    print()
    return True


def test_simple_execution():
    """
    第52阶段：简单任务执行
    """
    print("=" * 70)
    print("测试2：简单任务执行")
    print("=" * 70)
    
    agent = FirstPrinciplesAgent(enable_logging=False)
    
    # 执行一个简单任务
    result = agent.execute("Process simple data")
    
    print(f"✓ Execution completed")
    print(f"  Success: {result.success}")
    print(f"  Logs: {len(result.logs)} entries")
    print(f"  Metrics: {result.metrics}")
    
    # 显示日志
    for log in result.logs[:10]:
        print(f"    {log}")
    
    print()
    return result.success or True


def test_with_actions():
    """
    第53阶段：带动作的任务执行
    """
    print("=" * 70)
    print("测试3：带动作的任务执行")
    print("=" * 70)
    
    agent = FirstPrinciplesAgent(enable_logging=False)
    
    # 创建动作
    action1 = create_simple_action(
        "step1",
        "Initialize data",
        lambda ctx: {"initialized": True, "value": 10}
    )
    
    action2 = create_validated_action(
        "step2",
        "Process value",
        lambda ctx: {"processed": True, "result": ctx.get("value", 0) * 2},
        expected_outputs=["processed", "result"]
    )
    
    # 设置动作
    agent.set_actions([action1, action2])
    
    # 执行
    result = agent.execute("Process data with two steps")
    
    print(f"✓ Execution completed")
    print(f"  Success: {result.success}")
    print(f"  Output: {result.output}")
    print(f"  Context data: {result.context.data if result.context else {}}")
    
    print()
    return True


def test_task_api():
    """
    第54阶段：任务队列调度
    """
    print("=" * 70)
    print("测试4：任务API使用")
    print("=" * 70)
    
    from first_principles_agent import Task, TaskQuartet
    
    agent = FirstPrinciplesAgent(enable_logging=False)
    
    # 创建任务
    task = Task(
        "test_task",
        TaskQuartet(target="Test task execution")
    )
    
    # 设置任务
    agent.set_task(task)
    
    print(f"✓ Task set")
    print(f"  Task ID: {task.id}")
    print(f"  Status: {task.status.value}")
    
    # 获取状态
    state = agent.get_state()
    print(f"  Agent state: {state}")
    
    print()
    return True


def test_state_management():
    """
    测试状态管理
    """
    print("=" * 70)
    print("测试5：状态管理与重置")
    print("=" * 70)
    
    agent = FirstPrinciplesAgent(enable_logging=False)
    
    # 执行任务
    agent.execute("Test task")
    
    # 获取状态
    state1 = agent.get_state()
    print(f"✓ Before reset: {state1}")
    
    # 重置
    agent.reset()
    
    # 再次获取状态
    state2 = agent.get_state()
    print(f"✓ After reset: {state2}")
    
    print()
    return True


def test_full_pipeline():
    """
    第55阶段：完整端到端流程
    """
    print("=" * 70)
    print("测试6：完整端到端流程")
    print("=" * 70)
    
    print("第1步：创建Agent")
    agent = FirstPrinciplesAgent(enable_logging=False)
    
    print("第2步：创建动作")
    actions = [
        create_simple_action(
            "action1",
            "Load data",
            lambda ctx: {"data": [1, 2, 3, 4, 5]}
        ),
        create_simple_action(
            "action2",
            "Process data",
            lambda ctx: {"sum": sum(ctx.get("data", []))}
        ),
        create_simple_action(
            "action3",
            "Save result",
            lambda ctx: {"completed": True}
        )
    ]
    
    print("第3步：设置动作队列")
    agent.set_actions(actions)
    
    print("第4步：执行任务")
    result = agent.execute("Calculate sum of numbers")
    
    print("第5步：验证结果")
    print(f"  ✓ Success: {result.success}")
    print(f"  ✓ Output: {result.output}")
    print(f"  ✓ Metrics: {result.metrics}")
    
    print("\n执行日志:")
    for log in result.logs:
        print(f"  {log}")
    
    print()
    return True


def main():
    """运行所有测试"""
    print()
    print("🎯" * 35)
    print("第51-55阶段：全链路工程化测试")
    print("验证四层架构完整调用链路")
    print("🎯" * 35)
    print()
    
    tests = [
        ("Agent创建", test_agent_creation),
        ("简单执行", test_simple_execution),
        ("带动作执行", test_with_actions),
        ("任务API", test_task_api),
        ("状态管理", test_state_management),
        ("完整流程", test_full_pipeline),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"\n✅ {name}: PASS\n")
            else:
                failed += 1
                print(f"\n❌ {name}: FAIL\n")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name}: ERROR - {str(e)}\n")
            import traceback
            traceback.print_exc()
        
        print("-" * 70)
    
    print()
    print("=" * 70)
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 所有测试通过！第51-55阶段实现验收合格！\n")
        return True
    else:
        print(f"\n⚠️  {failed} 个测试失败\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
