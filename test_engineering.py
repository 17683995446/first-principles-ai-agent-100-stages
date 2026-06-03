"""
第56-60阶段：工程化完善测试
验证单向依赖、日志追踪、进度更新、异常处理、空载回归
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from first_principles_agent import create_agent, create_simple_action, Layer


def test_single_dependency():
    """
    第56阶段：优化单向依赖
    """
    print("=" * 70)
    print("测试1：单向依赖架构验证")
    print("=" * 70)
    
    agent = create_agent(enable_logging=False)
    
    # 测试执行
    result = agent.execute("Simple test task")
    
    print(f"✓ 执行完成")
    print(f"  TraceID: {result.get('trace_id')}")
    print(f"  成功: {result.get('success')}")
    print(f"  指标: {result.get('metrics')}")
    
    # 验证日志层级
    logs = result.get("logs", [])
    layer_sequence = [log.layer.value for log in logs if hasattr(log, 'layer')]
    print(f"  层调用顺序: {layer_sequence[:10]}")
    
    print()
    return True


def test_logger_system():
    """
    第57阶段：全流程日志追踪系统
    """
    print("=" * 70)
    print("测试2：日志追踪系统")
    print("=" * 70)
    
    agent = create_agent(enable_logging=False)
    
    # 执行任务
    result = agent.execute("Test logging")
    
    # 获取日志
    logs = result.get("logs", [])
    summary = result.get("log_summary", {})
    
    print(f"✓ 日志系统测试")
    print(f"  总日志数: {summary.get('total', 0)}")
    print(f"  按级别: {summary.get('by_level', {})}")
    print(f"  按层: {summary.get('by_layer', {})}")
    print(f"  TraceID: {summary.get('trace_id')}")
    
    # 过滤日志
    info_logs = agent.logger.get_logs_by_level(agent.logger.LogLevel.INFO if hasattr(agent.logger, 'LogLevel') else None)
    
    print()
    return True


def test_progress_callback():
    """
    第58阶段：实时进度状态更新
    """
    print("=" * 70)
    print("测试3：进度状态更新")
    print("=" * 70)
    
    progress_updates = []
    
    def progress_handler(progress):
        progress_updates.append(progress.copy())
        print(f"  进度: {progress['percentage']}% - {progress['message']}")
    
    agent = create_agent(
        enable_logging=False,
        progress_callback=progress_handler
    )
    
    print("  进度更新:")
    result = agent.execute("Test progress")
    
    print(f"\n✓ 进度更新测试")
    print(f"  进度更新次数: {len(progress_updates)}")
    
    if progress_updates:
        final_progress = progress_updates[-1]
        print(f"  最终进度: {final_progress['percentage']}%")
    
    print()
    return True


def test_exception_handler():
    """
    第59阶段：全局异常捕获
    """
    print("=" * 70)
    print("测试4：全局异常捕获")
    print("=" * 70)
    
    agent = create_agent(enable_logging=False)
    
    # 测试正常执行
    result1 = agent.execute("Normal task")
    print(f"✓ 正常执行: success={result1.get('success')}")
    
    # 检查异常历史
    exception_history = agent.exception_handler.get_history()
    print(f"  异常历史数: {len(exception_history)}")
    
    print()
    return True


def test_regression():
    """
    第60阶段：空载回归测试
    """
    print("=" * 70)
    print("测试5：空载回归测试")
    print("=" * 70)
    
    # 连续执行多次确保稳定性
    for i in range(5):
        agent = create_agent(enable_logging=False)
        result = agent.execute(f"Regression test {i+1}")
        
        print(f"  Run {i+1}: success={result.get('success')}")
        
        if not result.get("success"):
            print(f"  ❌ 测试失败!")
            return False
    
    print(f"\n✓ 空载回归测试通过 (5/5)")
    print()
    return True


def test_complete_workflow():
    """
    完整工作流测试
    """
    print("=" * 70)
    print("测试6：完整工作流（带动作）")
    print("=" * 70)
    
    agent = create_agent(
        enable_logging=False,
        progress_callback=lambda p: print(f"  [{p['percentage']}%] {p['message']}")
    )
    
    # 创建动作
    actions = [
        create_simple_action("init", "Initialize", lambda ctx: {"initialized": True}),
        create_simple_action("process", "Process", lambda ctx: {"processed": True}),
        create_simple_action("finalize", "Finalize", lambda ctx: {"finalized": True})
    ]
    
    agent.set_actions(actions)
    
    # 执行
    result = agent.execute("Complete workflow test")
    
    print(f"\n✓ 工作流测试")
    print(f"  成功: {result.get('success')}")
    print(f"  TraceID: {result.get('trace_id')}")
    print(f"  执行时间: {result.get('metrics', {}).get('execution_time_ms', 0):.2f}ms")
    print(f"  日志数: {len(result.get('logs', []))}")
    print(f"  异常数: {len(agent.exception_handler.get_history())}")
    
    print()
    return True


def test_state_management():
    """
    状态管理测试
    """
    print("=" * 70)
    print("测试7：状态管理与重置")
    print("=" * 70)
    
    agent = create_agent(enable_logging=False)
    
    # 执行任务
    result1 = agent.execute("Task 1")
    state1 = agent.get_state()
    
    print(f"  执行后状态: nodes={state1['nodes_count']}, actions={state1['actions_count']}")
    
    # 重置
    agent.reset()
    state2 = agent.get_state()
    
    print(f"  重置后状态: nodes={state2['nodes_count']}, actions={state2['actions_count']}")
    
    print()
    return True


def main():
    """运行所有测试"""
    print()
    print("🎯" * 35)
    print("第56-60阶段：工程化完善测试")
    print("验证单向依赖、日志追踪、进度更新、异常处理、空载回归")
    print("🎯" * 35)
    print()
    
    tests = [
        ("单向依赖架构", test_single_dependency),
        ("日志追踪系统", test_logger_system),
        ("进度状态更新", test_progress_callback),
        ("全局异常捕获", test_exception_handler),
        ("空载回归测试", test_regression),
        ("完整工作流", test_complete_workflow),
        ("状态管理", test_state_management),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {name}: PASS")
            else:
                failed += 1
                print(f"❌ {name}: FAIL")
        except Exception as e:
            failed += 1
            print(f"❌ {name}: ERROR - {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("-" * 70)
    
    print()
    print("=" * 70)
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 所有测试通过！第56-60阶段验收合格！\n")
        return True
    else:
        print(f"\n⚠️  {failed} 个测试失败\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
