#!/usr/bin/env python3
"""
第92阶段验收测试 - 最终集成测试和系统完整性验证
运行完整的系统集成测试
"""

import sys
from first_principles_agent import run_final_integration_tests


def main():
    """主函数"""
    print("="*80)
    print("Stage 92: Final Integration Test & System Integrity Verification")
    print("="*80)
    
    # 运行集成测试
    report = run_final_integration_tests()
    
    # 判断结果：所有测试通过且分数 >= 80
    passed = (report.failed_tests == 0 and report.overall_score >= 80)
    
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())