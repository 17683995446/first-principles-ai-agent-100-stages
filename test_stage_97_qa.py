#!/usr/bin/env python3
"""
第97阶段验收测试 - 最终QA - 全面质量检查
运行全面质量检查
"""

import sys
from first_principles_agent import run_phase_97_qa


def main():
    """主函数"""
    print("="*80)
    print("Stage 97: Final QA - Comprehensive Quality Check")
    print("="*80)
    
    # 运行第97阶段QA
    report = run_phase_97_qa()
    
    # 判断结果：所有需求验证通过且QA完成
    passed = report.qa_complete
    
    print("\n" + "="*80)
    if passed:
        print("✓ STAGE 97 COMPLETED - FINAL QA PASSED")
        print("✓ READY FOR PHASE 98: SECURITY SIGN-OFF")
    else:
        print("⚠ STAGE 97 INCOMPLETE")
        print("⚠ Please address failed requirements")
    print("="*80)
    
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
