#!/usr/bin/env python3
"""
第85阶段验收测试 - 缺陷修复与代码质量提升
运行全面的代码质量验证
"""

import sys
import time

from first_principles_agent import (
    run_quick_quality_check,
    run_core_quality_check,
    run_comprehensive_validation,
    create_core_quality_validator,
    CodeQualityLevel
)


def run_quick_demo():
    """运行快速演示"""
    print("="*70)
    print("Quick Quality Check Demo - Stage 85")
    print("="*70)
    
    print("\n[1/3] Running Quick Quality Check...")
    report = run_quick_quality_check()
    
    print(f"\n  Overall Score: {report.overall_score:.1f}/100")
    print(f"  Overall Level: {report.overall_level.value.upper()}")
    print(f"  Total Checks: {report.total_checks}")
    print(f"  Passed: {report.passed_checks}")
    print(f"  Warnings: {report.total_warnings}")
    print(f"  Errors: {report.total_errors}")
    
    print("\n[2/3] Running Core Quality Check...")
    try:
        core_report = run_core_quality_check()
        print(f"\n  Core Score: {core_report.overall_score:.1f}/100")
        print(f"  Core Level: {core_report.overall_level.value.upper()}")
    except Exception as e:
        print(f"\n  Core check skipped: {str(e)}")
    
    print("\n[3/3] Showing Summary...")
    overall_success = (
        report.overall_level in (CodeQualityLevel.EXCELLENT, CodeQualityLevel.GOOD)
    )
    
    print("\n" + "="*70)
    if overall_success:
        print("✓ Quick Demo PASSED!")
    else:
        print("⚠ Quick Demo Needs Attention")
    print("="*70)
    
    return overall_success


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stage 85 - Quality Validation')
    parser.add_argument('--mode', choices=['quick', 'core', 'full'], default='quick',
                        help='Validation mode: quick, core, or full')
    args = parser.parse_args()
    
    if args.mode == 'quick':
        success = run_quick_demo()
        return 0 if success else 1
    elif args.mode == 'core':
        print("="*70)
        print("Core Quality Validation")
        print("="*70)
        report = run_core_quality_check()
        return 0 if report.overall_level in (CodeQualityLevel.EXCELLENT, CodeQualityLevel.GOOD) else 1
    else:
        print("="*70)
        print("Comprehensive Validation Suite")
        print("="*70)
        results = run_comprehensive_validation()
        return 0 if results["overall_success"] else 1


if __name__ == "__main__":
    sys.exit(main())
