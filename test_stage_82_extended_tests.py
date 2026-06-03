#!/usr/bin/env python3
"""
第82阶段验收测试 - 扩展专项测试
运行负载测试、边界测试、故障注入和性能基准测试
"""

import sys
import time

from first_principles_agent import (
    create_core_extended_tests,
    run_all_extended_tests,
    create_boundary_test,
    create_load_test,
    create_fault_injection_test,
    create_benchmark_test,
    BoundaryTestType,
    FaultType,
    LoadPattern
)
from first_principles_agent.special_tests import TestSuite


def run_quick_demo():
    """运行快速演示"""
    print("="*70)
    print("Quick Demo - Extended Tests")
    print("="*70)
    
    # 1. 简单边界测试
    print("\n[1/4] Running Simple Boundary Test...")
    
    def simple_test(value):
        """简单测试函数"""
        try:
            if value is None:
                return False
            result = value * 2 if isinstance(value, (int, float)) else len(value)
            return True
        except Exception:
            return False
    
    test_values = [
        (0, BoundaryTestType.ZERO, True),
        (-1, BoundaryTestType.NEGATIVE, True),
        (1000000, BoundaryTestType.MAXIMUM, True),
        ("", BoundaryTestType.EMPTY, True),
        (None, BoundaryTestType.NULL, False)
    ]
    
    boundary_test = create_boundary_test(
        "Simple Boundary Demo",
        simple_test,
        test_values
    )
    
    suite = TestSuite("Demo Suite")
    suite.add_test(boundary_test)
    
    start = time.time()
    results = suite.run_all()
    duration = time.time() - start
    
    for result in results:
        print(f"\n  Test: {result.test_name}")
        print(f"  Status: {result.status.value}")
        print(f"  Duration: {result.duration:.2f}s")
        print(f"  Operations: {result.metrics.operations_total}")
    
    # 2. 简单负载测试
    print("\n[2/4] Running Simple Load Test...")
    
    def load_operation(index):
        """简单负载操作"""
        return sum(range(100)) > 0
    
    load_test = create_load_test(
        "Simple Load Demo",
        load_operation,
        pattern=LoadPattern.CONSTANT,
        base_concurrency=2,
        max_concurrency=2,
        duration=5.0
    )
    
    suite2 = TestSuite("Load Demo")
    suite2.add_test(load_test)
    
    results2 = suite2.run_all()
    
    for result in results2:
        print(f"\n  Test: {result.test_name}")
        print(f"  Status: {result.status.value}")
        print(f"  Duration: {result.duration:.2f}s")
        print(f"  Throughput: {result.metrics.throughput:.2f} op/s")
    
    # 3. 简单基准测试
    print("\n[3/4] Running Simple Benchmark...")
    
    def func1(): return sum(range(100))
    def func2(): return len(list(range(1000)))
    
    benchmark_test = create_benchmark_test(
        "Simple Benchmark",
        {"Function 1": func1, "Function 2": func2},
        iterations=100
    )
    
    suite3 = TestSuite("Benchmark Demo")
    suite3.add_test(benchmark_test)
    
    results3 = suite3.run_all()
    
    for result in results3:
        print(f"\n  Test: {result.test_name}")
        print(f"  Status: {result.status.value}")
        
        if hasattr(benchmark_test, 'benchmark_results'):
            for func_name, metrics in benchmark_test.benchmark_results.items():
                print(f"\n    {func_name}:")
                print(f"      Throughput: {metrics.throughput:.2f} op/s")
                print(f"      Avg latency: {metrics.avg_latency * 1000:.2f}ms")
    
    # 4. 简单故障注入测试
    print("\n[4/4] Running Simple Fault Injection...")
    
    counter = [0]
    
    def fault_op():
        """简单操作"""
        counter[0] += 1
        return counter[0]
    
    fault_test = create_fault_injection_test(
        "Simple Fault Demo",
        fault_op,
        FaultType.EXCEPTION,
        rate=0.1,
        duration=5.0
    )
    
    suite4 = TestSuite("Fault Demo")
    suite4.add_test(fault_test)
    
    results4 = suite4.run_all()
    
    for result in results4:
        print(f"\n  Test: {result.test_name}")
        print(f"  Status: {result.status.value}")
        print(f"  Injected faults: {fault_test.injected_faults}")
        print(f"  Successful ops: {fault_test.successful_operations}")
    
    print("\n" + "="*70)
    print("Quick Demo Complete!")
    print("="*70)
    
    return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stage 82 - Extended Tests')
    parser.add_argument('--mode', choices=['demo', 'full'], default='demo',
                        help='Test mode: demo (quick) or full (complete)')
    args = parser.parse_args()
    
    if args.mode == 'demo':
        success = run_quick_demo()
        return 0 if success else 1
    else:
        print("\nRunning full extended test suite...")
        print("This will take several minutes...")
        suite = run_all_extended_tests()
        return 0 if len(suite.defects) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
