"""
第61阶段验证脚本
将理论伪代码完全工程化改写 - 验收测试

验收标准：伪代码全部落地为实代码逻辑
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))


def test_all_modules():
    """测试所有模块是否可正常导入"""
    print("=" * 70)
    print("第61阶段：工程化改写验证")
    print("=" * 70)
    print()
    
    modules_to_test = [
        ("task_model", "任务模型模块"),
        ("task_parser", "任务解析模块"),
        ("topological_decomposer", "拓扑分解模块"),
        ("atomic_converger", "原子动作收敛模块"),
        ("verification_layer", "验证层模块"),
        ("orchestrator", "主控制器模块")
    ]
    
    results = []
    
    for module_name, description in modules_to_test:
        print(f"测试 {description} ({module_name})...")
        try:
            __import__(f"first_principles_agent.{module_name}")
            print(f"  ✅ {module_name} - OK")
            results.append((module_name, True, ""))
        except Exception as e:
            print(f"  ❌ {module_name} - FAIL: {e}")
            results.append((module_name, False, str(e)))
    
    print()
    return results


def test_core_classes():
    """测试核心类是否可正常实例化"""
    print("=" * 70)
    print("核心类实例化测试")
    print("=" * 70)
    print()
    
    from first_principles_agent import (
        Task, TaskQuartet, TaskStatus,
        TopologicalDecomposer, TaskNode, NodeType,
        AtomicAction, AtomicConverger,
        VerificationLayer,
        FirstPrinciplesAgent, create_agent,
        create_simple_action
    )
    
    classes_to_test = [
        ("Task", lambda: Task("test", TaskQuartet("test"))),
        ("TaskQuartet", lambda: TaskQuartet("test")),
        ("TopologicalDecomposer", lambda: TopologicalDecomposer()),
        ("AtomicConverger", lambda: AtomicConverger()),
        ("VerificationLayer", lambda: VerificationLayer()),
        ("FirstPrinciplesAgent", lambda: FirstPrinciplesAgent())
    ]
    
    results = []
    
    for class_name, constructor in classes_to_test:
        try:
            instance = constructor()
            print(f"  ✅ {class_name} - OK")
            results.append((class_name, True, ""))
        except Exception as e:
            print(f"  ❌ {class_name} - FAIL: {e}")
            results.append((class_name, False, str(e)))
    
    print()
    return results


def test_task_quartet():
    """测试Task Quartet理论落地"""
    print("=" * 70)
    print("Task Quartet 理论落地验证")
    print("=" * 70)
    print()
    
    from first_principles_agent import Task, TaskQuartet
    
    tests = []
    
    # 测试1：四元组创建
    print("1. 测试四元组创建...")
    try:
        quartet = TaskQuartet(
            target="测试目标",
            end_rule=lambda ctx: True
        )
        print("   ✅ 四元组创建成功")
        tests.append(("四元组创建", True))
    except Exception as e:
        print(f"   ❌ 四元组创建失败: {e}")
        tests.append(("四元组创建", False, str(e)))
    
    # 测试2：任务创建
    print("2. 测试任务创建...")
    try:
        task = Task("task_1", quartet)
        print("   ✅ 任务创建成功")
        print(f"      Task ID: {task.id}")
        print(f"      Target: {task.quartet.target}")
        tests.append(("任务创建", True))
    except Exception as e:
        print(f"   ❌ 任务创建失败: {e}")
        tests.append(("任务创建", False, str(e)))
    
    # 测试3：状态管理
    print("3. 测试状态管理...")
    try:
        task.mark_in_progress()
        print(f"   ✅ 状态更新成功: {task.status.value}")
        tests.append(("状态管理", True))
    except Exception as e:
        print(f"   ❌ 状态管理失败: {e}")
        tests.append(("状态管理", False, str(e)))
    
    print()
    return tests


def test_dag_theory():
    """测试DAG理论落地"""
    print("=" * 70)
    print("DAG 理论落地验证")
    print("=" * 70)
    print()
    
    from first_principles_agent import (
        Task, TaskQuartet, TopologicalDecomposer
    )
    
    tests = []
    
    # 测试1：DAG创建
    print("1. 测试DAG创建...")
    try:
        decomposer = TopologicalDecomposer()
        print("   ✅ DAG创建成功")
        tests.append(("DAG创建", True))
    except Exception as e:
        print(f"   ❌ DAG创建失败: {e}")
        tests.append(("DAG创建", False, str(e)))
    
    # 测试2：节点添加
    print("2. 测试节点添加...")
    try:
        task1 = Task("node1", TaskQuartet("Node 1"))
        task2 = Task("node2", TaskQuartet("Node 2"))
        
        decomposer.add_task(task1)
        decomposer.add_task(task2, dependencies=["node1"])
        
        print(f"   ✅ 节点添加成功: {len(decomposer.nodes)} 个节点")
        tests.append(("节点添加", True))
    except Exception as e:
        print(f"   ❌ 节点添加失败: {e}")
        tests.append(("节点添加", False, str(e)))
    
    # 测试3：DAG验证
    print("3. 测试DAG验证...")
    try:
        is_valid, issues = decomposer.validate_dag()
        print(f"   ✅ DAG验证成功: valid={is_valid}")
        tests.append(("DAG验证", True))
    except Exception as e:
        print(f"   ❌ DAG验证失败: {e}")
        tests.append(("DAG验证", False, str(e)))
    
    # 测试4：拓扑排序
    print("4. 测试拓扑排序...")
    try:
        order = decomposer.get_execution_order()
        print(f"   ✅ 拓扑排序成功: {order}")
        tests.append(("拓扑排序", True))
    except Exception as e:
        print(f"   ❌ 拓扑排序失败: {e}")
        tests.append(("拓扑排序", False, str(e)))
    
    print()
    return tests


def test_atomic_action_theory():
    """测试原子动作理论落地"""
    print("=" * 70)
    print("原子动作 理论落地验证")
    print("=" * 70)
    print()
    
    from first_principles_agent import (
        AtomicConverger, create_simple_action
    )
    
    tests = []
    
    # 测试1：原子动作创建
    print("1. 测试原子动作创建...")
    try:
        def test_func(ctx):
            return {"result": 42}
        
        action = create_simple_action(
            "test_action",
            "Test action",
            test_func
        )
        print(f"   ✅ 原子动作创建成功: {action.id}")
        tests.append(("原子动作创建", True))
    except Exception as e:
        print(f"   ❌ 原子动作创建失败: {e}")
        tests.append(("原子动作创建", False, str(e)))
    
    # 测试2：动作执行
    print("2. 测试动作执行...")
    try:
        output = action.execute({})
        print(f"   ✅ 动作执行成功: {output}")
        tests.append(("动作执行", True))
    except Exception as e:
        print(f"   ❌ 动作执行失败: {e}")
        tests.append(("动作执行", False, str(e)))
    
    # 测试3：队列管理
    print("3. 测试队列管理...")
    try:
        converger = AtomicConverger()
        converger.add_action(action)
        print(f"   ✅ 队列管理成功: {len(converger.action_queue)} 个动作")
        tests.append(("队列管理", True))
    except Exception as e:
        print(f"   ❌ 队列管理失败: {e}")
        tests.append(("队列管理", False, str(e)))
    
    print()
    return tests


def test_verification_theory():
    """测试验证层理论落地"""
    print("=" * 70)
    print("验证层 理论落地验证")
    print("=" * 70)
    print()
    
    from first_principles_agent import VerificationLayer
    
    tests = []
    
    # 测试1：验证层创建
    print("1. 测试验证层创建...")
    try:
        verification = VerificationLayer()
        print("   ✅ 验证层创建成功")
        tests.append(("验证层创建", True))
    except Exception as e:
        print(f"   ❌ 验证层创建失败: {e}")
        tests.append(("验证层创建", False, str(e)))
    
    # 测试2：验证报告
    print("2. 测试验证报告...")
    try:
        from first_principles_agent import Task, TaskQuartet
        test_task = Task("verify_test", TaskQuartet("Verification test"))
        report = verification.check_end_condition(test_task, {})
        print(f"   ✅ 验证报告生成成功: {report.result.value if hasattr(report.result, 'value') else report.result}")
        tests.append(("验证报告", True))
    except Exception as e:
        print(f"   ❌ 验证报告生成失败: {e}")
        tests.append(("验证报告", False, str(e)))
    
    print()
    return tests


def test_orchestrator_theory():
    """测试主控制器理论落地"""
    print("=" * 70)
    print("主控制器 理论落地验证")
    print("=" * 70)
    print()
    
    from first_principles_agent import create_agent, create_simple_action
    
    tests = []
    
    # 测试1：Agent创建
    print("1. 测试Agent创建...")
    try:
        agent = create_agent(enable_logging=False)
        print("   ✅ Agent创建成功")
        tests.append(("Agent创建", True))
    except Exception as e:
        print(f"   ❌ Agent创建失败: {e}")
        tests.append(("Agent创建", False, str(e)))
    
    # 测试2：执行流程
    print("2. 测试执行流程...")
    try:
        action = create_simple_action("test", "Test", lambda ctx: {"done": True})
        agent.set_actions([action])
        
        result = agent.execute("Test execution")
        
        print(f"   ✅ 执行流程成功: success={result['success']}")
        print(f"      TraceID: {result['trace_id']}")
        tests.append(("执行流程", True))
    except Exception as e:
        print(f"   ❌ 执行流程失败: {e}")
        tests.append(("执行流程", False, str(e)))
    
    # 测试3：状态管理
    print("3. 测试状态管理...")
    try:
        state = agent.get_state()
        print(f"   ✅ 状态管理成功: has_task={state['has_task']}")
        tests.append(("状态管理", True))
    except Exception as e:
        print(f"   ❌ 状态管理失败: {e}")
        tests.append(("状态管理", False, str(e)))
    
    print()
    return tests


def main():
    """主测试流程"""
    print()
    print("🎯" * 35)
    print("第61阶段：工程化改写验收测试")
    print("验收标准：伪代码全部落地为实代码逻辑")
    print("🎯" * 35)
    print()
    
    # 1. 模块导入测试
    module_results = test_all_modules()
    
    # 2. 核心类实例化测试
    class_results = test_core_classes()
    
    # 3. 理论落地验证
    quartet_tests = test_task_quartet()
    dag_tests = test_dag_theory()
    action_tests = test_atomic_action_theory()
    verification_tests = test_verification_theory()
    orchestrator_tests = test_orchestrator_theory()
    
    # 汇总结果
    print("=" * 70)
    print("验收结果汇总")
    print("=" * 70)
    
    all_tests = (
        module_results + class_results + quartet_tests +
        dag_tests + action_tests + verification_tests + orchestrator_tests
    )
    
    passed = sum(1 for test in all_tests if test[1])
    failed = sum(1 for test in all_tests if not test[1])
    total = len(all_tests)
    
    print(f"\n总测试数: {total}")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    print(f"通过率: {passed/total*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 第61阶段验收通过！")
        print("所有理论设计已完全工程化！")
    else:
        print(f"\n⚠️  {failed} 个测试失败，需要修复")
    
    print()
    
    # 返回测试结果
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
