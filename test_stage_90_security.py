#!/usr/bin/env python3
"""
第90阶段验收测试 - 安全加固和最终安全审查
运行完整的安全审计
"""

import sys
from first_principles_agent import run_security_audit


def main():
    """主函数"""
    print("="*70)
    print("Stage 90: Security Hardening & Final Audit")
    print("="*70)
    
    # 运行安全审计
    report = run_security_audit()
    
    # 判断结果：没有严重问题且分数 >= 70 认为通过
    passed = (report.critical_issues == 0 and report.overall_score >= 70)
    
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
