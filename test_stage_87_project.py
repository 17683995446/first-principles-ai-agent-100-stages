#!/usr/bin/env python3
"""
第87阶段验收测试 - 完整项目回顾与持续改进指南
运行项目回顾和改进建议生成
"""

import sys

from first_principles_agent import (
    generate_project_summary,
    create_project_reviewer,
    PriorityLevel
)


def run_project_review():
    """运行项目回顾"""
    print("="*70)
    print("Project Review & Continuous Improvement - Stage 87")
    print("="*70)
    
    # 1. 生成项目总结
    print("\n[1/3] Generating Project Summary...")
    summary = generate_project_summary()
    print(summary)
    
    # 2. 展示架构组件
    print("\n[2/3] Architecture Components:")
    reviewer = create_project_reviewer()
    for comp in reviewer.architecture_components:
        status_symbol = "✓" if comp.status == "stable" else "⚠"
        print(f"  {status_symbol} {comp.name}")
        print(f"    {comp.description}")
    
    # 3. 展示高优先级改进建议
    print("\n[3/3] High Priority Improvements:")
    high_priority = [s for s in reviewer.improvement_suggestions 
                    if s.priority in [PriorityLevel.HIGH, PriorityLevel.CRITICAL]]
    for suggestion in high_priority:
        print(f"\n  • [{suggestion.priority.value}] {suggestion.title}")
        print(f"    {suggestion.description}")
        print(f"    Effort: {suggestion.effort_estimate_days} days")
    
    print("\n" + "="*70)
    print("✓ Project Review Complete!")
    print("="*70)
    
    return True


def main():
    """主函数"""
    success = run_project_review()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
