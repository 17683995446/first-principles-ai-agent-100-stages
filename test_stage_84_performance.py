#!/usr/bin/env python3
"""
第84阶段验收测试 - 性能调优与系统稳定性测试
"""

import sys
import time

from first_principles_agent import (
    run_all_performance_tests,
    run_stability_tests,
    run_performance_comparison,
    PerformanceProfiler,
    StabilityTester,
    StabilityTestType
)


def run_quick_demo():
    """运行快速演示"""
    print("="*70)
    print("Quick Demo - Performance & Stability Tests")
    print("="*70)
    
    # 1. 快速性能分析
    print("\n[1/3] Running Quick Performance Profile...")
    
    profiler = PerformanceProfiler()
    
    def quick_operation():
        """快速操作"""
        result = 0
        for i in range(1000):
            result += i
        return result
    
    for _ in range(50):
        with profiler.profile():
            quick_operation()
    
    summary = profiler.get_summary()
    print(f"\n  Operations: {summary.get('operation_count', 0)}")
    print(f"  Avg Latency: {summary.get('avg_latency', 0)*1000:.2f}ms")
    print(f"  Throughput: {summary.get('throughput', 0):.2f} ops/s")
    
    # 2. 快速稳定性测试
    print("\n[2/3] Running Quick Stability Test...")
    
    counter = {"value": 0}
    
    def simple_operation() -> bool:
        counter["value"] += 1
        try:
            result = sum(range(100))
            return True
        except Exception:
            return False
    
    tester = StabilityTester("Quick Stability Demo")
    tester.configure(
        test_type=StabilityTestType.LONG_RUN,
        duration=10.0,  # 10秒快速测试
        operations_per_second=10.0
    )
    
    report = tester.run(simple_operation)
    
    print(f"\n  Operations: {report.total_operations}")
    print(f"  Success Rate: {(100 - report.error_rate):.2f}%")
    print(f"  Throughput: {report.throughput:.2f} ops/s")
    print(f"  Memory Growth: {report.memory_growth:.2f}MB")
    print(f"  Status: {'PASSED' if report.passed else 'NEEDS ATTENTION'}")
    
    # 3. 快速性能对比
    print("\n[3/3] Running Quick Performance Comparison...")
    
    from first_principles_agent import (
        PerformanceBenchmark, Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction
    )
    
    benchmark = PerformanceBenchmark()
    
    def operation_v1():
        """版本1"""
        result = sum(range(1000))
        return result
    
    def operation_v2():
        """版本2"""
        result = 0
        for i in range(1000):
            result += i
        return result
    
    results = benchmark.run_benchmark(
        "quick_comparison",
        {"v1": operation_v1, "v2": operation_v2},
        iterations=100
    )
    
    print("\n  Comparison Results:")
    for name, metrics in results.items():
        print(f"\n    {name}:")
        print(f"      Throughput: {metrics.get('throughput', 0):.2f} ops/s")
        print(f"      Avg Latency: {metrics.get('avg_latency', 0)*1000:.2f}ms")
    
    print("\n" + "="*70)
    print("✓ Quick Performance Demo Complete!")
    print("="*70)
    
    return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stage 84 - Performance Tests')
    parser.add_argument('--mode', choices=['demo', 'full'], default='demo',
                        help='Test mode: demo (quick) or full (complete)')
    args = parser.parse_args()
    
    if args.mode == 'demo':
        success = run_quick_demo()
        return 0 if success else 1
    else:
        print("\nRunning full performance test suite...")
        print("This will take several minutes...")
        success = run_all_performance_tests()
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
