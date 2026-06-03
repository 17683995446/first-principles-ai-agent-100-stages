#!/usr/bin/env python3
"""
第83阶段验收测试 - 集成测试与缺陷排查
运行模块间集成测试
"""

import sys
import time

from first_principles_agent import (
    run_all_integration_tests,
    IntegrationTestRunner,
    create_core_integration_tests,
    IntegrationLevel,
    create_integration_test
)


def run_quick_demo():
    """运行快速演示"""
    print("="*70)
    print("Quick Demo - Integration Tests")
    print("="*70)
    
    # 1. 快速集成测试
    print("\n[1/2] Running Quick Integration Test...")
    
    test_results = []
    
    def quick_test_1():
        """快速测试1"""
        from first_principles_agent import Task, TaskQuartet
        quartet = TaskQuartet(target="Quick Test")
        task = Task("quick_test", quartet)
        assert task is not None
    
    def quick_test_2():
        """快速测试2"""
        from first_principles_agent import ConfigManager, ConfigItem, ConfigType
        manager = ConfigManager()
        manager.register_config_item(ConfigItem(
            key="test",
            type_=ConfigType.STRING,
            default="value"
        ))
        assert manager.get("test") == "value"
    
    runner = IntegrationTestRunner("Quick Demo")
    
    runner.add_test(create_integration_test(
        name="Quick Module Test 1",
        test_function=quick_test_1,
        modules=["task_model"],
        level=IntegrationLevel.MODULE
    ))
    
    runner.add_test(create_integration_test(
        name="Quick Module Test 2",
        test_function=quick_test_2,
        modules=["config"],
        level=IntegrationLevel.MODULE
    ))
    
    results = runner.run_all()
    
    for result in results:
        print(f"\n  Test: {result.test_name}")
        print(f"  Status: {result.status.value}")
        print(f"  Duration: {result.duration:.4f}s")
        test_results.append(result.status == "passed")
    
    # 2. 端到端测试
    print("\n[2/2] Running End-to-End Workflow Test...")
    
    def e2e_test():
        """端到端测试"""
        from first_principles_agent import (
            Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction
        )
        
        quartet = TaskQuartet(
            target="E2E Test",
            end_rule=lambda ctx: "complete" in ctx
        )
        task = Task("e2e_task", quartet)
        
        agent = FirstPrinciplesAgent()
        agent.set_task(task)
        
        def complete_action(ctx):
            return {"complete": True}
        
        action = AtomicAction("complete", "Complete", complete_action)
        agent.set_atomic_actions([action])
        
        result = agent.execute()
        assert result.success, "E2E test failed"
    
    runner2 = IntegrationTestRunner("E2E Demo")
    runner2.add_test(create_integration_test(
        name="End-to-End Workflow",
        test_function=e2e_test,
        modules=["task_model", "orchestrator"],
        level=IntegrationLevel.E2E,
        timeout=30.0
    ))
    
    results2 = runner2.run_all()
    
    for result in results2:
        print(f"\n  Test: {result.test_name}")
        print(f"  Status: {result.status.value}")
        print(f"  Duration: {result.duration:.2f}s")
        test_results.append(result.status == "passed")
    
    print("\n" + "="*70)
    if all(test_results):
        print("✓ All Quick Demo Tests Passed!")
    else:
        print("⚠ Some Tests Failed")
    print("="*70)
    
    return all(test_results)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stage 83 - Integration Tests')
    parser.add_argument('--mode', choices=['demo', 'full'], default='demo',
                        help='Test mode: demo (quick) or full (complete)')
    args = parser.parse_args()
    
    if args.mode == 'demo':
        success = run_quick_demo()
        return 0 if success else 1
    else:
        print("\nRunning full integration test suite...")
        print("This will take several minutes...")
        runner = run_all_integration_tests()
        
        summary = runner.get_summary()
        if summary['defects']['total'] > 0:
            print("\n⚠ DEFECTS FOUND - See report above")
            return 1
        else:
            print("\n✓ ALL INTEGRATION TESTS PASSED!")
            return 0


if __name__ == "__main__":
    sys.exit(main())
