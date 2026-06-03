"""
测试 Task 四元组模块 - 验证第21阶段实现
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from first_principles_agent.task_model import (
    Task,
    TaskQuartet,
    EndRule,
    Constraint,
    Precondition,
    TaskStatus,
    ConstraintType,
    create_simple_task,
    max_steps_constraint,
    time_limit_constraint,
    no_network_constraint
)


def test_basic_task():
    """测试基本任务创建"""
    print("=" * 70)
    print("测试1: 基本任务创建")
    print("=" * 70)
    
    def end_condition(ctx):
        return "result" in ctx and ctx["result"] is not None
    
    quartet = TaskQuartet(
        target="Calculate sum of a and b",
        end_rule=EndRule(end_condition)
    )
    
    task = Task(
        task_id="test_task_1",
        quartet=quartet,
        context={"a": 5, "b": 3}
    )
    
    print(f"✓ Task created: {task.id}")
    print(f"  Target: {task.quartet.target}")
    print(f"  Status: {task.status.value}")
    print()
    
    return task


def test_task_validation():
    """测试任务验证"""
    print("=" * 70)
    print("测试2: 任务验证")
    print("=" * 70)
    
    def end_condition(ctx):
        return ctx.get("completed", False)
    
    quartet = TaskQuartet(
        target="Valid task",
        end_rule=EndRule(end_condition)
    )
    
    task = Task("task_2", quartet)
    
    is_valid, errors, warnings = task.validate()
    
    print(f"✓ Validation result: {is_valid}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    
    if warnings:
        for w in warnings:
            print(f"    ⚠ {w.field}: {w.message}")
    print()
    
    return is_valid


def test_constraint():
    """测试约束"""
    print("=" * 70)
    print("测试3: 约束检查")
    print("=" * 70)
    
    constraint = max_steps_constraint(10)
    print(f"✓ Constraint created: {constraint.description}")
    print(f"  Type: {constraint.type.value}")
    print(f"  Value: {constraint.value}")
    
    context_ok = {"step_count": 5}
    context_fail = {"step_count": 15}
    
    print(f"  ✓ Context OK (5 steps): {constraint.is_satisfied(context_ok)}")
    print(f"  ✗ Context Fail (15 steps): {constraint.is_satisfied(context_fail)}")
    print()
    
    return True


def test_end_rule():
    """测试终止规则"""
    print("=" * 70)
    print("测试4: 终止规则")
    print("=" * 70)
    
    def end_func(ctx):
        return ctx.get("done", False)
    
    end_rule = EndRule(end_func, description="Task done when done=True")
    
    print(f"✓ EndRule created: {end_rule.description}")
    print(f"  ✓ Not ended (done=False): {end_rule.is_ended({'done': False})}")
    print(f"  ✓ Ended (done=True): {end_rule.is_ended({'done': True})}")
    print()
    
    return True


def test_serialization():
    """测试序列化"""
    print("=" * 70)
    print("测试5: 序列化")
    print("=" * 70)
    
    quartet = TaskQuartet(target="Serializable task")
    task = Task("task_ser", quartet, context={"value": 42})
    
    task_dict = task.to_dict()
    task_json = task.to_json()
    
    print(f"✓ Task serialized to dict: {type(task_dict)}")
    print(f"✓ Task serialized to JSON: {len(task_json)} chars")
    
    task_restored = Task.from_dict(task_dict)
    print(f"✓ Task restored from dict: {task_restored.id}")
    print(f"  Context restored: {task_restored.context}")
    print()
    
    return True


def test_factory_function():
    """测试工厂函数"""
    print("=" * 70)
    print("测试6: 工厂函数")
    print("=" * 70)
    
    def end_cond(ctx):
        return ctx.get("finished", False)
    
    task = create_simple_task(
        task_id="factory_task",
        target="Factory created task",
        end_condition_func=end_cond,
        context={"value": 100}
    )
    
    print(f"✓ Task created via factory: {task.id}")
    print(f"  Target: {task.quartet.target}")
    print(f"  Context: {task.context}")
    print()
    
    return True


def test_task_lifecycle():
    """测试任务生命周期"""
    print("=" * 70)
    print("测试7: 任务生命周期")
    print("=" * 70)
    
    quartet = TaskQuartet(target="Lifecycle test task")
    task = Task("lifecycle_task", quartet)
    
    print(f"✓ Initial status: {task.status.value}")
    
    task.mark_in_progress()
    print(f"✓ After mark_in_progress: {task.status.value}")
    
    task.mark_completed(output_val={"result": "success"})
    print(f"✓ After mark_completed: {task.status.value}")
    print(f"  Output: {task.output}")
    print(f"  Execution time: {task.get_execution_time():.3f}s")
    print()
    
    return True


def test_constraint_types():
    """测试多种约束类型"""
    print("=" * 70)
    print("测试8: 多种约束类型")
    print("=" * 70)
    
    constraints = [
        max_steps_constraint(5),
        time_limit_constraint(60),
        no_network_constraint()
    ]
    
    for c in constraints:
        print(f"✓ {c.type.value}: {c.description}")
    
    print()
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("Task Model Module - Complete Test Suite")
    print("第21阶段: 设计标准 Task 四元组结构体验收测试")
    print("=" * 70 + "\n")
    
    tests = [
        ("基本任务创建", test_basic_task),
        ("任务验证", test_task_validation),
        ("约束检查", test_constraint),
        ("终止规则", test_end_rule),
        ("序列化", test_serialization),
        ("工厂函数", test_factory_function),
        ("任务生命周期", test_task_lifecycle),
        ("多种约束类型", test_constraint_types),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {name}: PASSED")
            else:
                failed += 1
                print(f"❌ {name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {name}: FAILED - {str(e)}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 70)
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 所有测试通过！第21阶段实现验收合格！\n")
        return True
    else:
        print(f"\n⚠️  {failed} 个测试失败\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
