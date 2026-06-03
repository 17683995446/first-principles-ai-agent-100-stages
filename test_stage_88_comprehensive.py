#!/usr/bin/env python3
"""
第88阶段验收测试 - 完整综合示例与最终文档完善
运行端到端业务场景演示
"""

import sys
from first_principles_agent import run_comprehensive_demo


def main():
    """主函数"""
    print("="*70)
    print("Stage 88: Comprehensive Demo & Final Documentation")
    print("="*70)
    
    # 运行综合演示
    results = run_comprehensive_demo()
    
    # 返回结果
    return 0 if results.get("all_success", False) else 1


if __name__ == "__main__":
    sys.exit(main())
