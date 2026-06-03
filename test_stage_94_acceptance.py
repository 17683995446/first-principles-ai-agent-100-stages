#!/usr/bin/env python3
"""
第94阶段验收测试 - 最终验收测试与系统确认
运行完整的最终验收测试
"""

import sys
from first_principles_agent import run_final_acceptance_tests


def main():
    """主函数"""
    print("="*80)
    print("Stage 94: Final Acceptance Test & System Confirmation")
    print("="*80)
    
    # 运行最终验收测试
    report = run_final_acceptance_tests()
    
    # 判断结果：得分 >= 80 且验收级别不是 NOT ACCEPTABLE
    passed = (report.overall_score >= 80 and "NOT ACCEPTABLE" not in report.acceptance_level)
    
    print("\n" + "="*80)
    if passed:
        print("✓ FINAL ACCEPTANCE TEST PASSED!")
        print(f"System is ready for delivery with score: {report.overall_score:.1f}%")
    else:
        print("⚠ FINAL ACCEPTANCE TEST NEEDS ATTENTION")
        print(f"Current score: {report.overall_score:.1f}%")
    print("="*80)
    
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())