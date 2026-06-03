"""
最终验证与交付准备 - 第86阶段
完整的系统最终验证和交付检查
"""

import time
import sys
from typing import Dict, List, Any

from first_principles_agent.final_validation import (
    DeliveryReadiness, VerificationPhase,
    VerificationResult, DeliveryChecklist,
    SystemReadinessReport, FinalSystemValidator,
    create_final_validator, run_system_final_validation
)


def create_end_to_end_demo_workflow():
    """创建端到端演示工作流"""
    print("="*70)
    print("End-to-End Demo Workflow")
    print("="*70)
    
    try:
        from first_principles_agent import (
            Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction,
            ConfigManager, ConfigItem, ConfigType,
            info, warning, error, debug
        )
        
        print("\nStep 1: Create Complex Task")
        complex_quartet = TaskQuartet(
            target="Complete Business Analytics Workflow",
            end_rule=lambda ctx: "final_analysis" in ctx
        )
        
        main_task = Task("e2e_demo", complex_quartet, context={
            "raw_data": ["A", "B", "C", "D"],
            "config": {"batch_size": 2, "priority": "high"}
        })
        
        agent = FirstPrinciplesAgent()
        agent.set_task(main_task)
        
        print("\nStep 2: Define Processing Steps")
        
        def validate_data(ctx):
            """第一步：验证数据"""
            info("Validating data...")
            validated = [item for item in ctx["raw_data"] if isinstance(item, str)]
            return {"validated_data": validated}
        
        def transform_data(ctx):
            """第二步：转换数据"""
            info("Transforming data...")
            transformed = [f"PROCESSED_{item}" for item in ctx["validated_data"]]
            return {"transformed_data": transformed}
        
        def analyze_data(ctx):
            """第三步：分析数据"""
            info("Analyzing data...")
            analysis = {
                "count": len(ctx["transformed_data"]),
                "items": ctx["transformed_data"],
                "completed": True
            }
            return {"analysis": analysis}
        
        def finalize_analysis(ctx):
            """第四步：完成分析"""
            info("Finalizing analysis...")
            return {"final_analysis": {
                "status": "SUCCESS",
                "timestamp": time.time(),
                "details": ctx["analysis"]
            }}
        
        print("\nStep 3: Register Actions")
        agent.set_atomic_actions([
            AtomicAction("validate", "Validate Data", validate_data),
            AtomicAction("transform", "Transform Data", transform_data),
            AtomicAction("analyze", "Analyze Data", analyze_data),
            AtomicAction("finalize", "Finalize Analysis", finalize_analysis),
        ])
        
        print("\nStep 4: Execute Workflow")
        start_time = time.time()
        execution_result = agent.execute()
        end_time = time.time()
        
        print("\n" + "="*70)
        print("Execution Summary")
        print("="*70)
        print(f"Status: {'SUCCESS' if execution_result.success else 'FAILED'}")
        print(f"Duration: {(end_time - start_time) * 1000:.2f}ms")
        
        if execution_result.success:
            final_analysis = execution_result.context.get("final_analysis", {})
            print(f"Final Analysis: {final_analysis}")
        
        print("\n" + "="*70)
        print("End-to-End Demo Complete")
        print("="*70)
        
        return execution_result.success
        
    except Exception as e:
        print(f"\nError during demo: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_delivery_validation():
    """运行交付验证"""
    print("="*70)
    print("Delivery Validation Suite - Stage 86")
    print("="*70)
    
    results = {}
    
    # 1. 最终系统验证
    print("\n[1/3] Running Final System Validation...")
    try:
        report = run_system_final_validation()
        results["final_validation"] = report
        print(f"\nOverall Status: {report.overall_status.value.upper()}")
        print(f"Overall Score: {report.overall_score:.1f}%")
    except Exception as e:
        print(f"Final validation failed: {str(e)}")
        results["final_validation"] = None
    
    # 2. 端到端演示
    print("\n[2/3] Running End-to-End Demo...")
    try:
        e2e_success = create_end_to_end_demo_workflow()
        results["e2e_demo"] = e2e_success
        print(f"E2E Demo: {'PASSED' if e2e_success else 'FAILED'}")
    except Exception as e:
        print(f"E2E demo failed: {str(e)}")
        results["e2e_demo"] = False
    
    # 3. 项目完整性检查
    print("\n[3/3] Running Project Completeness Check...")
    try:
        completeness_result = check_project_completeness()
        results["completeness"] = completeness_result
        print(f"Project Completeness: {'PASSED' if completeness_result['success'] else 'FAILED'}")
        print(f"Key Files Checked: {len(completeness_result['files'])}")
    except Exception as e:
        print(f"Completeness check failed: {str(e)}")
        results["completeness"] = {"success": False}
    
    # 总结
    print("\n" + "="*70)
    print("Delivery Validation Summary")
    print("="*70)
    
    overall_success = (
        (results.get("final_validation") and 
         results["final_validation"].overall_status in 
         (DeliveryReadiness.READY, DeliveryReadiness.COMPLETE)) and
        results.get("e2e_demo", False) and
        results.get("completeness", {}).get("success", False)
    )
    
    if overall_success:
        print("\n✓ System Ready for Delivery!")
    else:
        print("\n⚠ System Needs Further Attention")
    
    results["overall_success"] = overall_success
    return results


def check_project_completeness() -> Dict[str, Any]:
    """检查项目完整性"""
    import os
    
    result = {
        "success": False,
        "files": {},
        "missing": []
    }
    
    # 检查关键文件
    key_files = [
        "README.md",
        "PROJECT_SUMMARY.md",
        "QUICKSTART.md",
        "src/first_principles_agent/__init__.py",
        "src/first_principles_agent/atomic_converger.py",
        "src/first_principles_agent/orchestrator.py",
        "src/first_principles_agent/task_model.py",
        "src/first_principles_agent/topological_decomposer.py",
        "src/first_principles_agent/verification_layer.py",
    ]
    
    all_found = True
    
    for file_path in key_files:
        exists = os.path.exists(file_path)
        result["files"][file_path] = exists
        if not exists:
            result["missing"].append(file_path)
            all_found = False
    
    result["success"] = all_found
    
    # 检查示例目录
    if os.path.exists("examples"):
        result["examples_directory"] = True
    else:
        result["examples_directory"] = False
        all_found = False
    
    # 检查阶段文档
    if os.path.exists("stages"):
        result["stages_directory"] = True
    else:
        result["stages_directory"] = False
        all_found = False
    
    return result


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stage 86 - Final Validation')
    parser.add_argument('--mode', choices=['quick', 'full'], default='quick',
                        help='Validation mode: quick or full')
    args = parser.parse_args()
    
    if args.mode == 'quick':
        print("="*70)
        print("Quick Final Validation")
        print("="*70)
        
        print("\n[1/2] Final System Validation...")
        report = run_system_final_validation()
        
        print("\n[2/2] End-to-End Demo...")
        e2e_success = create_end_to_end_demo_workflow()
        
        overall_success = (
            report.overall_status in (DeliveryReadiness.READY, DeliveryReadiness.COMPLETE) and
            e2e_success
        )
        
        print("\n" + "="*70)
        if overall_success:
            print("✓ Quick Validation PASSED!")
        else:
            print("⚠ Quick Validation Needs Attention")
        print("="*70)
        
        return 0 if overall_success else 1
    else:
        results = run_delivery_validation()
        return 0 if results["overall_success"] else 1


if __name__ == "__main__":
    sys.exit(main())
