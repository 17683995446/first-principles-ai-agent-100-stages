#!/usr/bin/env python3
"""
第91阶段验收测试 - 最终文档和用户指南完善
运行文档生成和验证
"""

import sys
from first_principles_agent import generate_final_documentation


def main():
    """主函数"""
    print("="*80)
    print("Stage 91: Final Documentation and User Guide Completion")
    print("="*80)
    
    # 运行文档生成
    report = generate_final_documentation()
    
    # 判断结果
    passed = (
        report.total_apis >= 3 and
        report.total_tutorials >= 3 and
        report.completeness_score >= 90
    )
    
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
