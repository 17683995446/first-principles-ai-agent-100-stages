#!/usr/bin/env python3
"""
简单压力测试演示 - 快速验证压力测试功能
"""

import time
import sys

from first_principles_agent.special_tests import (
    StressTestCase, TestSuite, SpecialTestManager,
    create_stress_test, run_stress_suite
)
from first_principles_agent import (
    Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction
)


def simple_calculation_test():
    """简单计算压力测试"""
    print("\nRunning simple calculation stress test...")
    
    counter = [0]
    
    def operation(index):
        # 执行简单的数学运算
        result = 0
        for i in range(100):
            result += i
        counter[0] += 1
        return True
    
    # 创建并运行压力测试
    test = create_stress_test(
        "Simple Calculation",
        duration=3.0,
        concurrency=3,
        operation_func=operation
    )
    
    manager = SpecialTestManager()
    suite = manager.create_suite("Quick Demo Suite")
    suite.add_test(test)
    
    start = time.time()
    results = suite.run_all()
    total_time = time.time() - start
    
    # 输出结果
    print(f"\n✓ Quick Demo Test Complete!")
    print(f"  Total operations: {test.metrics.operations_total}")
    print(f"  Success: {test.metrics.operations_success}")
    print(f"  Failed: {test.metrics.operations_failed}")
    print(f"  Duration: {total_time:.2f}s")
    print(f"  Throughput: {test.metrics.throughput:.2f} op/s")
    
    return len(suite.defects) == 0


def task_execution_test():
    """任务执行压力测试"""
    print("\nRunning task execution stress test...")
    
    def operation(index):
        try:
            # 快速创建并执行一个简单任务
            task_quartet = TaskQuartet(target=f"Quick task {index}")
            task = Task(f"t{index}", task_quartet, context={"x": 5, "y": 3})
            
            agent = FirstPrinciplesAgent()
            agent.set_task(task)
            
            def multiply(ctx):
                return {"result": ctx["x"] * ctx["y"]}
            
            action = AtomicAction("multiply", "Multiply", multiply)
            agent.set_atomic_actions([action])
            
            result = agent.execute()
            return result.success
        except Exception:
            return False
    
    test = create_stress_test(
        "Task Execution",
        duration=5.0,
        concurrency=2,
        operation_func=operation
    )
    
    suite = run_stress_suite("Task Execution Demo", [test])
    
    print(f"\n✓ Task Execution Test Complete!")
    print(f"  Status: {'PASSED' if not suite.defects else 'ISSUES FOUND'}")
    
    return len(suite.defects) == 0


def main():
    """运行演示"""
    print("=" * 70)
    print("STRESS TEST DEMO")
    print("=" * 70)
    
    try:
        passed = True
        passed &= simple_calculation_test()
        passed &= task_execution_test()
        
        print("\n" + "=" * 70)
        if passed:
            print("✅ ALL DEMO TESTS PASSED")
        else:
            print("⚠️ SOME DEMO TESTS FAILED")
        print("=" * 70)
        
        return 0 if passed else 1
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
