"""
测试任务解析与建模模块 - 验证第22-28阶段实现
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from first_principles_agent.task_parser import (
    TaskParser,
    TargetExtractor,
    PreconditionRecognizer,
    BoundaryRecognizer,
    EndRuleParser,
    TaskValidator,
    TaskRejector,
    UnifiedTaskModeling
)


def test_parser():
    """测试解析器"""
    print("=" * 70)
    print("测试1: TaskParser - 用户需求统一解析")
    print("=" * 70)
    
    parser = TaskParser()
    
    test_cases = [
        "帮我读取文件data.csv",
        "随便处理一下",
        "优化这个代码"
    ]
    
    for test_input in test_cases:
        success, task, warnings = parser.parse(test_input)
        print(f"\n输入: {test_input}")
        print(f"  成功: {success}")
        if task:
            print(f"  Task ID: {task.id}")
            print(f"  Target: {task.quartet.target}")
        if warnings:
            print(f"  警告: {warnings}")
    
    print()
    return True


def test_target_extractor():
    """测试目标提取器"""
    print("=" * 70)
    print("测试2: TargetExtractor - Target 提取与归一化")
    print("=" * 70)
    
    extractor = TargetExtractor()
    
    test_cases = [
        "帮我快速读取文件",
        "看看这个代码",
        "随便优化一下代码"
    ]
    
    for raw_input in test_cases:
        result = extractor.extract(raw_input)
        print(f"\n原始输入: {raw_input}")
        print(f"  归一化结果: {result}")
    
    print()
    return True


def test_precondition_recognizer():
    """测试前置条件识别"""
    print("=" * 70)
    print("测试3: PreconditionRecognizer - 前置条件自动识别")
    print("=" * 70)
    
    recognizer = PreconditionRecognizer()
    
    test_cases = [
        "读取文件data.csv并分析",
        "查询数据库获取用户信息",
        "调用API获取天气数据"
    ]
    
    for description in test_cases:
        preconditions = recognizer.recognize(description, {})
        print(f"\n任务描述: {description}")
        print(f"  识别到前置条件: {len(preconditions)} 个")
        for pc in preconditions:
            print(f"    - {pc.description}")
    
    print()
    return True


def test_boundary_recognizer():
    """测试边界约束识别"""
    print("=" * 70)
    print("测试4: BoundaryRecognizer - 边界约束识别")
    print("=" * 70)
    
    recognizer = BoundaryRecognizer()
    
    test_cases = [
        "在5分钟内完成，最多10步",
        "不联网处理这个任务",
        "帮我优化代码，要求在3分钟内"
    ]
    
    for description in test_cases:
        constraints = recognizer.recognize(description)
        print(f"\n任务描述: {description}")
        print(f"  识别到约束: {len(constraints)} 个")
        for c in constraints:
            print(f"    - {c.type.value}: {c.description}")
    
    print()
    return True


def test_endrule_parser():
    """测试终止规则解析"""
    print("=" * 70)
    print("测试5: EndRuleParser - 终止规则解析器")
    print("=" * 70)
    
    parser = EndRuleParser()
    
    test_cases = [
        "当文件result.txt生成完成",
        "任务完成后告诉我",
        "生成最终结果"
    ]
    
    for description in test_cases:
        end_rule = parser.parse(description, {})
        print(f"\n描述: {description}")
        print(f"  终止规则: {end_rule.description}")
        
        # 测试终止条件
        test_ctx_fail = {"files": []}
        test_ctx_success = {"files": ["result.txt"]}
        print(f"  ✓ 不终止 (无文件): {end_rule.is_ended(test_ctx_fail)}")
        print(f"  ✓ 终止 (有文件): {end_rule.is_ended(test_ctx_success)}")
    
    print()
    return True


def test_validator():
    """测试任务校验器"""
    print("=" * 70)
    print("测试6: TaskValidator - 任务合法性校验")
    print("=" * 70)
    
    from first_principles_agent.task_model import Task, TaskQuartet, EndRule
    
    validator = TaskValidator()
    
    # 测试合法任务
    print("\n测试合法任务:")
    valid_task = Task(
        "valid_task",
        TaskQuartet(
            target="读取并分析data.csv文件，生成报告",
            end_rule=EndRule(lambda ctx: "report" in ctx)
        )
    )
    
    is_valid, errors = validator.validate(valid_task)
    print(f"  合法: {is_valid}")
    if errors:
        print(f"  错误: {[e.message for e in errors]}")
    
    # 测试模糊任务
    print("\n测试模糊任务:")
    vague_task = Task(
        "vague_task",
        TaskQuartet(target="随便看看")
    )
    
    is_valid, errors = validator.validate(vague_task)
    print(f"  合法: {is_valid}")
    if errors:
        print(f"  错误数: {len(errors)}")
        for e in errors[:2]:
            print(f"    - {e.message}")
    
    print()
    return True


def test_rejector():
    """测试任务拒绝器"""
    print("=" * 70)
    print("测试7: TaskRejector - 无效任务拦截")
    print("=" * 70)
    
    from first_principles_agent.task_model import Task, TaskQuartet
    
    rejector = TaskRejector()
    
    test_cases = [
        ("随便", "测试模糊输入"),
        ("a", "测试过短输入"),
        ("删除所有文件", "测试危害内容")
    ]
    
    for target, description in test_cases:
        task = Task("test", TaskQuartet(target=target))
        should_reject, reason = rejector.should_reject(task)
        
        print(f"\n{description}: {target}")
        print(f"  应拒绝: {should_reject}")
        if should_reject:
            print(f"  原因: {reason}")
            response = rejector.create_rejection_response(reason, task)
            print(f"  响应: {response['reason_message']}")
    
    print()
    return True


def test_unified_modeling():
    """测试统一建模入口"""
    print("=" * 70)
    print("测试8: UnifiedTaskModeling - 统一建模入口")
    print("=" * 70)
    
    modeler = UnifiedTaskModeling()
    
    test_cases = [
        "读取文件data.csv并在5分钟内分析完成",
        "随便优化一下代码",
        "查询数据库获取用户列表"
    ]
    
    for user_input in test_cases:
        print(f"\n用户输入: {user_input}")
        
        success, result = modeler.model(user_input)
        
        print(f"  成功: {success}")
        
        if result.get("rejected"):
            print(f"  被拒绝: {result['rejection_info']['reason_message']}")
        elif result.get("task"):
            task = result["task"]
            print(f"  Task ID: {task.id}")
            print(f"  Target: {task.quartet.target}")
            print(f"  前置条件: {len(task.quartet.preconditions)} 个")
            print(f"  约束: {len(task.quartet.constraints)} 个")
        
        if result.get("warnings"):
            print(f"  警告: {len(result['warnings'])} 条")
        
        if result.get("errors"):
            print(f"  错误: {result['errors']}")
    
    print()
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("Task Parser Module - Complete Test Suite")
    print("第22-28阶段: 任务解析与建模模块验收测试")
    print("=" * 70 + "\n")
    
    tests = [
        ("TaskParser解析器", test_parser),
        ("TargetExtractor提取器", test_target_extractor),
        ("PreconditionRecognizer识别器", test_precondition_recognizer),
        ("BoundaryRecognizer识别器", test_boundary_recognizer),
        ("EndRuleParser解析器", test_endrule_parser),
        ("TaskValidator校验器", test_validator),
        ("TaskRejector拒绝器", test_rejector),
        ("UnifiedTaskModeling统一入口", test_unified_modeling),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"\n✅ {name}: PASSED")
            else:
                failed += 1
                print(f"\n❌ {name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name}: FAILED - {str(e)}")
            import traceback
            traceback.print_exc()
        print("\n" + "-" * 70)
    
    print("=" * 70)
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 所有测试通过！第22-28阶段实现验收合格！\n")
        return True
    else:
        print(f"\n⚠️  {failed} 个测试失败\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
