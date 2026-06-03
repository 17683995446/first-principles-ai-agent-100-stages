#!/usr/bin/env python3
"""
第96阶段验收测试 - 正式交付版本冻结 - 版本锁定
运行版本锁定流程
"""

import sys
from first_principles_agent import run_phase_96_freeze


def main():
    """主函数"""
    print("="*80)
    print("Stage 96: Formal Delivery Version Freeze - Version Lock")
    print("="*80)
    
    # 运行第96阶段冻结
    report = run_phase_96_freeze()
    
    # 判断结果：版本已锁定且第96阶段检查点已完成
    passed = (
        report.lock_status.locked and
        report.completed_checkpoints >= 1 and
        any(cp.phase == 96 and cp.completed for cp in report.checkpoints)
    )
    
    print("\n" + "="*80)
    if passed:
        print("✓ STAGE 96 COMPLETED - VERSION LOCKED")
        print("✓ READY FOR PHASE 97: FINAL QA")
    else:
        print("⚠ STAGE 96 INCOMPLETE")
        print("⚠ Please check version lock status")
    print("="*80)
    
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
