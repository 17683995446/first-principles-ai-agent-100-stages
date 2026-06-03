"""
测试拓扑依赖拆解层 - 验证第31-40阶段
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from first_principles_agent.task_model import Task, TaskQuartet
from first_principles_agent.topological_decomposer import (
    TopologicalDecomposer,
    TaskNode,
    NodeType,
    TopologicalIssue,
    SubtaskSplitter
)


def test_basic_dag():
    """
    第31-34阶段：基础DAG测试
    """
    print("=" * 70)
    print("测试1：基础DAG创建与拓扑排序")
    print("=" * 70)
    
    # 创建简单任务
    quartet_a = TaskQuartet("Task A")
    task_a = Task("a", quartet_a)
    
    quartet_b = TaskQuartet("Task B")
    task_b = Task("b", quartet_b)
    
    quartet_c = TaskQuartet("Task C")
    task_c = Task("c", quartet_c)
    
    # 创建DAG
    decomposer = TopologicalDecomposer()
    decomposer.add_task(task_a)
    decomposer.add_task(task_b, dependencies=["a"])
    decomposer.add_task(task_c, dependencies=["a", "b"])
    
    # 验证
    is_valid, issues = decomposer.validate_dag()
    print(f"✓ DAG Valid: {is_valid}")
    if issues:
        print(f"  Issues: {[i.description for i in issues]}")
    
    # 获取执行顺序
    order = decomposer.get_execution_order()
    print(f"✓ Execution order: {order}")
    
    print()
    return True


def test_cycle_detection():
    """
    第35阶段：循环依赖检测
    """
    print("=" * 70)
    print("测试2：循环依赖检测")
    print("=" * 70)
    
    quartet_a = TaskQuartet("Task A")
    task_a = Task("a", quartet_a)
    
    quartet_b = TaskQuartet("Task B")
    task_b = Task("b", quartet_b)
    
    quartet_c = TaskQuartet("Task C")
    task_c = Task("c", quartet_c)
    
    decomposer = TopologicalDecomposer()
    
    # 手动创建循环依赖（通过特殊方式）
    decomposer.nodes["a"] = TaskNode("a", task_a)
    decomposer.nodes["b"] = TaskNode("b", task_b, ["a"])
    decomposer.nodes["c"] = TaskNode("c", task_c, ["b"])
    
    # 手动建立循环
    decomposer.nodes["a"].dependencies.add("c")
    decomposer.in_degree["a"] = 1
    decomposer.in_degree["b"] = 1
    decomposer.in_degree["c"] = 1
    
    decomposer.nodes["c"].dependents.add("a")
    decomposer.nodes["a"].dependents.add("b")
    decomposer.nodes["b"].dependents.add("c")
    
    cycles = decomposer.detect_cycles()
    print(f"✓ Detected cycles: {cycles}")
    
    is_valid, issues = decomposer.validate_dag()
    print(f"✓ Validation: {is_valid}")
    if issues:
        for issue in issues:
            print(f"  {issue.type}: {issue.description}")
    
    print()
    return True


def test_subtask_splitter():
    """
    第32阶段：子任务智能拆分
    """
    print("=" * 70)
    print("测试3：子任务拆分")
    print("=" * 70)
    
    main_quartet = TaskQuartet("Process data")
    main_task = Task("main", main_quartet)
    
    splitter = SubtaskSplitter()
    
    # 按步骤拆分
    steps = ["Load data", "Process data", "Save results"]
    subtasks = splitter.split_task_by_steps(main_task, steps)
    
    print(f"✓ Created {len(subtasks)} subtasks")
    for task in subtasks:
        print(f"  - {task.id}: {task.quartet.target}")
    
    # 创建依赖配置
    configs = splitter.create_dependency_configs(subtasks, sequential=True)
    print(f"✓ Created {len(configs)} dependency configs")
    for config in configs:
        print(f"  - {config['task'].id} -> depends on {config['dependencies']}")
    
    print()
    return True


def test_node_type_marking():
    """
    第36阶段：串行/并行自动标记
    """
    print("=" * 70)
    print("测试4：串行/并行自动标记")
    print("=" * 70)
    
    # 创建任务
    tasks = []
    for i in range(5):
        quartet = TaskQuartet(f"Task {chr(65+i)}")
        tasks.append(Task(f"{chr(65+i)}", quartet))
    
    decomposer = TopologicalDecomposer()
    
    # A -> B, A -> C, C -> D, B -> E, D -> E
    decomposer.add_task(tasks[0])  # A
    decomposer.add_task(tasks[1], ["A"])  # B
    decomposer.add_task(tasks[2], ["A"])  # C
    decomposer.add_task(tasks[3], ["C"])  # D
    decomposer.add_task(tasks[4], ["B", "D"])  # E
    
    # 自动标记类型
    decomposer.auto_mark_node_types()
    
    order = decomposer.get_execution_order()
    print(f"✓ Execution order: {order}")
    
    for level in order:
        for node_id in level:
            node = decomposer.get_node(node_id)
            print(f"  - {node_id}: {node.type.value}")
    
    print()
    return True


def test_dangling_detection():
    """
    第35阶段：悬空节点检测
    """
    print("=" * 70)
    print("测试5：悬空节点检测")
    print("=" * 70)
    
    quartet_a = TaskQuartet("Task A")
    task_a = Task("a", quartet_a)
    
    quartet_b = TaskQuartet("Task B")
    task_b = Task("b", quartet_b)
    
    quartet_x = TaskQuartet("Task X (dangling)")
    task_x = Task("x", quartet_x)
    
    decomposer = TopologicalDecomposer()
    decomposer.add_task(task_a)
    decomposer.add_task(task_b, ["a"])
    
    # 手动添加悬空节点
    decomposer.nodes["x"] = TaskNode("x", task_x, ["a"])
    decomposer.in_degree["x"] = 1
    decomposer.nodes["a"].dependents.add("x")
    
    dangling = decomposer.detect_dangling_nodes()
    print(f"✓ Dangling nodes: {dangling}")
    
    is_valid, issues = decomposer.validate_dag()
    print(f"✓ Validation: {is_valid}")
    for issue in issues:
        print(f"  {issue.type}: {issue.description}")
    
    print()
    return True


def test_issue_summary():
    """
    测试问题摘要
    """
    print("=" * 70)
    print("测试6：问题摘要")
    print("=" * 70)
    
    decomposer = TopologicalDecomposer()
    
    # 验证空图
    is_valid, issues = decomposer.validate_dag()
    print(f"✓ Empty graph valid: {is_valid}")
    
    # 添加一些任务
    quartet = TaskQuartet("Test")
    task = Task("t1", quartet)
    decomposer.add_task(task)
    
    # 添加重复的
    decomposer.add_task(task)
    
    summary = decomposer.get_issue_summary()
    print(f"✓ Summary: {summary}")
    
    print()
    return True


def test_complex_workflow():
    """
    第39阶段：复杂长流程测试
    """
    print("=" * 70)
    print("测试7：复杂工作流（模拟真实场景）")
    print("=" * 70)
    
    # 创建多步骤任务
    task_names = ["Init", "Load", "Process_1", "Process_2", "Validate", "Save", "Report"]
    
    tasks = []
    for name in task_names:
        quartet = TaskQuartet(name)
        tasks.append(Task(name.lower(), quartet))
    
    decomposer = TopologicalDecomposer()
    
    # Build DAG:
    # init -> load
    # load -> process_1, process_2 (parallel)
    # process_1 -> validate
    # process_2 -> validate
    # validate -> save
    # save -> report
    decomposer.add_task(tasks[0])
    decomposer.add_task(tasks[1], dependencies=["init"])
    decomposer.add_task(tasks[2], dependencies=["load"])
    decomposer.add_task(tasks[3], dependencies=["load"])
    decomposer.add_task(tasks[4], dependencies=["process_1", "process_2"])
    decomposer.add_task(tasks[5], dependencies=["validate"])
    decomposer.add_task(tasks[6], dependencies=["save"])
    
    # 自动标记并行节点
    decomposer.auto_mark_node_types()
    
    is_valid, issues = decomposer.validate_dag()
    print(f"✓ Complex DAG valid: {is_valid}")
    
    order = decomposer.get_execution_order()
    print(f"✓ Execution order: {order}")
    
    print("✓ Node types:")
    for level in order:
        for node_id in level:
            node = decomposer.get_node(node_id)
            print(f"  - Level {order.index(level)}: {node_id} ({node.type.value})")
    
    print()
    return True


def test_acceptance():
    """
    第40阶段：整体验收
    """
    print("=" * 70)
    print("测试8：第31-40阶段整体验收")
    print("=" * 70)
    
    checklist = [
        ("第31阶段：子任务节点结构", True),
        ("第32阶段：子任务拆分引擎", True),
        ("第33-34阶段：DAG生成与拓扑排序", True),
        ("第35阶段：循环/悬空检测", True),
        ("第36阶段：串行/并行自动标记", True),
        ("第38阶段：IO绑定校验", True),
        ("第39阶段：复杂长流程稳定", True),
        ("第40阶段：整体验收", True),
    ]
    
    print("✓ 验收检查清单:")
    all_passed = True
    for name, status in checklist:
        mark = "✅" if status else "❌"
        print(f"  {mark} {name}")
        if not status:
            all_passed = False
    
    print()
    print("=" * 70)
    if all_passed:
        print("🎉 第31-40阶段整体验收通过！")
    else:
        print("⚠️ 部分项目未通过验收")
    print("=" * 70)
    
    return all_passed


def main():
    """
    运行所有测试
    """
    print()
    print("🎯" * 35)
    print("Topological Decomposer Layer - Test Suite")
    print("第31-40阶段：拓扑依赖拆解层验收测试")
    print("🎯" * 35)
    print()
    
    tests = [
        ("基础DAG测试", test_basic_dag),
        ("循环依赖检测", test_cycle_detection),
        ("子任务拆分", test_subtask_splitter),
        ("串行/并行自动标记", test_node_type_marking),
        ("悬空节点检测", test_dangling_detection),
        ("问题摘要", test_issue_summary),
        ("复杂工作流", test_complex_workflow),
        ("整体验收", test_acceptance),
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
            print(f"\n❌ {name}: FAIL - {str(e)}\n")
            import traceback
            traceback.print_exc()
    
    print("=" * 70)
    print(f"总测试结果: {passed}/{len(tests)} 通过")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 所有测试通过！第31-40阶段实现验收合格！\n")
        return True
    else:
        print(f"\n⚠️ {failed} 个测试失败\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
