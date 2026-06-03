#!/usr/bin/env python3
"""
第93阶段验收测试 - 交付准备与最终打包
运行交付打包验证
"""

import sys
from first_principles_agent import generate_delivery_package


def main():
    """主函数"""
    print("="*80)
    print("Stage 93: Delivery Preparation & Final Packaging")
    print("="*80)
    
    # 生成交付包
    report = generate_delivery_package()
    
    # 判断结果：完整度 >= 90%
    passed = report.completeness_score >= 90
    
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())