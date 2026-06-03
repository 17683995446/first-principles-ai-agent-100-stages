#!/usr/bin/env python3
"""
第86阶段验收测试 - 系统最终验证与交付准备
运行完整的系统最终验证和交付检查
"""

import sys
import time

from first_principles_agent import (
    run_system_final_validation,
    create_end_to_end_demo_workflow,
    run_delivery_validation,
    DeliveryReadiness
)


def run_quick_demo():
    """运行快速演示"""
    print("="*70)
    print("Quick Final Validation Demo - Stage 86")
    print("="*70)
    
    print("\n[1/2] Running Final System Validation...")
    report = run_system_final_validation()
    
    print(f"\nOverall Status: {report.overall_status.value.upper()}")
    print(f"Overall Score: {report.overall_score:.1f}%")
    
    print("\n[2/2] Running End-to-End Demo...")
    e2e_success = create_end_to_end_demo_workflow()
    
    overall_success = (
        report.overall_status in (DeliveryReadiness.READY, DeliveryReadiness.COMPLETE) and
        e2e_success
    )
    
    print("\n" + "="*70)
    if overall_success:
        print("✓ Quick Final Validation PASSED!")
    else:
        print("⚠ Quick Final Validation Needs Attention")
    print("="*70)
    
    return overall_success


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stage 86 - Final Validation')
    parser.add_argument('--mode', choices=['quick', 'full'], default='quick',
                        help='Validation mode: quick or full')
    args = parser.parse_args()
    
    if args.mode == 'quick':
        success = run_quick_demo()
        return 0 if success else 1
    else:
        print("="*70)
        print("Full Delivery Validation Suite")
        print("="*70)
        results = run_delivery_validation()
        return 0 if results["overall_success"] else 1


if __name__ == "__main__":
    sys.exit(main())
