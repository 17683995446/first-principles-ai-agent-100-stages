#!/usr/bin/env python3
"""
第81阶段：专项测试 - 压力测试运行脚本
运行核心压力测试用例
"""

import sys
import time

from first_principles_agent import (
    run_all_core_stress_tests, run_targeted_stress_test,
    create_core_stress_suite
)


def main():
    """主函数 - 运行压力测试"""
    print("=" * 70)
    print("STAGE 81: SPECIAL TESTS - STRESS TESTING")
    print("=" * 70)
    print(f"Started: {time.ctime()}")
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        duration = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
        concurrency = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        
        print(f"\nRunning targeted stress test: {test_type}")
        print(f"Duration: {duration}s, Concurrency: {concurrency}")
        suite = run_targeted_stress_test(test_type, duration, concurrency)
    else:
        print("\nRunning core stress test suite")
        suite = run_all_core_stress_tests()
    
    print("\n" + "=" * 70)
    print("STRESS TESTS COMPLETED")
    print("=" * 70)
    
    summary = suite.get_summary()
    if summary.get('defects', 0) > 0:
        print("\n⚠️  DEFECTS FOUND - PLEASE INVESTIGATE")
        print(f"Total defects: {summary['defects']}")
        return 1
    else:
        print("\n✅ ALL TESTS PASSED - NO DEFECTS FOUND")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
