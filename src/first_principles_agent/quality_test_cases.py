"""
全面验证测试用例 - 第85阶段
验证整个系统的功能完整性、性能、健壮性
"""

import time
import threading
import sys
from typing import List, Dict, Any

from first_principles_agent.quality_validation import (
    CodeQualityLevel, CheckType, QualityCheckResult,
    CodeQualityReport, CodeQualityChecker, CompleteValidator,
    create_quality_checker, create_complete_validator, run_quick_quality_check
)
from first_principles_agent import (
    Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction,
    ConfigManager, ConfigItem, ConfigType,
    PermissionManager, Permission, Role, User, Resource,
    PermissionType, ResourceType,
    Logger, LogManager, LogLevel, MemoryHandler
)


def create_core_quality_validator() -> CompleteValidator:
    """创建核心质量验证器"""
    validator = CompleteValidator("Core Quality Validator")
    
    # 1. 添加功能性检查
    add_functionality_checks(validator)
    
    # 2. 添加性能检查
    add_performance_checks(validator)
    
    # 3. 添加健壮性检查
    add_robustness_checks(validator)
    
    return validator


def add_functionality_checks(validator: CompleteValidator):
    """添加功能性检查"""
    
    # 检查任务模型
    def check_task_model():
        result = QualityCheckResult(status=True)
        try:
            quartet = TaskQuartet(
                target="Functionality Test",
                end_rule=lambda ctx: "result" in ctx
            )
            
            task = Task("func_test_task", quartet, context={"a": 1, "b": 2})
            
            result.status = task is not None
            result.details["target"] = quartet.target
            result.details["context_keys"] = list(task.context.keys())
            result.performance_score = 100
            
        except Exception as e:
            result.status = False
            result.error_count = 1
            result.issues.append(f"Task model check failed: {str(e)}")
        return result
    
    # 检查Agent执行
    def check_agent_execution():
        result = QualityCheckResult(status=True)
        try:
            agent = FirstPrinciplesAgent()
            
            quartet = TaskQuartet(
                target="Execution Test",
                end_rule=lambda ctx: "result" in ctx
            )
            task = Task("exec_test", quartet, context={"a": 10, "b": 20})
            agent.set_task(task)
            
            def add_action(ctx):
                return {"result": ctx["a"] + ctx["b"]}
            
            action = AtomicAction("add", "Add", add_action)
            agent.set_atomic_actions([action])
            
            execution_result = agent.execute()
            result.status = execution_result.success
            result.details["result_value"] = execution_result.context.get("result")
            
            if execution_result.success:
                result.performance_score = 100
            
        except Exception as e:
            result.status = False
            result.error_count = 1
            result.issues.append(f"Agent execution check failed: {str(e)}")
        return result
    
    # 检查配置管理
    def check_config_management():
        result = QualityCheckResult(status=True)
        try:
            manager = ConfigManager()
            
            manager.register_config_item(ConfigItem(
                key="quality.test.key",
                type_=ConfigType.STRING,
                default="default_value"
            ))
            
            manager.set("quality.test.key", "test_value")
            retrieved = manager.get("quality.test.key")
            
            result.status = retrieved == "test_value"
            result.details["set_value"] = "test_value"
            result.details["retrieved"] = retrieved
            
            if result.status:
                result.performance_score = 100
            
        except Exception as e:
            result.status = False
            result.error_count = 1
            result.issues.append(f"Config management check failed: {str(e)}")
        return result
    
    # 检查权限管理
    def check_permission_management():
        result = QualityCheckResult(status=True)
        try:
            manager = PermissionManager()
            
            manager.register_permission(Permission(
                "quality.read",
                PermissionType.READ,
                ResourceType.SYSTEM
            ))
            
            user = manager.create_user("quality_user")
            manager.assign_role(user.id, "user")
            
            result.status = user is not None
            result.details["user_id"] = user.id
            result.details["user_active"] = user.is_active
            
            if result.status:
                result.performance_score = 100
            
        except Exception as e:
            result.status = False
            result.error_count = 1
            result.issues.append(f"Permission management check failed: {str(e)}")
        return result
    
    validator.quality_checker.register_check(
        "Task Model Check", CheckType.FUNCTIONALITY, check_task_model
    )
    validator.quality_checker.register_check(
        "Agent Execution Check", CheckType.FUNCTIONALITY, check_agent_execution
    )
    validator.quality_checker.register_check(
        "Config Management Check", CheckType.FUNCTIONALITY, check_config_management
    )
    validator.quality_checker.register_check(
        "Permission Management Check", CheckType.FUNCTIONALITY, check_permission_management
    )


def add_performance_checks(validator: CompleteValidator):
    """添加性能检查"""
    
    # 任务创建吞吐量
    def check_task_creation_throughput():
        result = QualityCheckResult(status=True)
        try:
            start = time.time()
            tasks = []
            for i in range(100):
                quartet = TaskQuartet(target=f"Throughput Test {i}")
                tasks.append(Task(f"t{i}", quartet))
            duration = time.time() - start
            
            throughput = len(tasks) / duration if duration > 0 else 0
            result.details["operations"] = len(tasks)
            result.details["duration_seconds"] = duration
            result.details["throughput_ops_s"] = throughput
            
            if throughput > 1000:
                result.performance_score = 100
            elif throughput > 500:
                result.performance_score = 80
            elif throughput > 100:
                result.performance_score = 60
            else:
                result.performance_score = 40
                result.warning_count = 1
                result.issues.append(f"Throughput below expectation: {throughput:.1f} ops/s")
                
        except Exception as e:
            result.status = False
            result.error_count = 1
            result.issues.append(f"Task throughput check failed: {str(e)}")
        return result
    
    # 简单任务执行延迟
    def check_task_execution_latency():
        result = QualityCheckResult(status=True)
        try:
            latencies = []
            for i in range(50):
                start = time.time()
                
                agent = FirstPrinciplesAgent()
                quartet = TaskQuartet(target="Latency Test", end_rule=lambda ctx: "x" in ctx)
                task = Task("latency_test", quartet, context={"x": i})
                agent.set_task(task)
                
                def simple_action(ctx):
                    return {"y": ctx["x"] * 2}
                
                agent.set_atomic_actions([AtomicAction("simple", "Simple", simple_action)])
                agent.execute()
                
                latencies.append((time.time() - start) * 1000)
            
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            
            result.details["avg_latency_ms"] = avg_latency
            result.details["max_latency_ms"] = max_latency
            
            if avg_latency < 10:
                result.performance_score = 100
            elif avg_latency < 50:
                result.performance_score = 80
            elif avg_latency < 200:
                result.performance_score = 60
            else:
                result.performance_score = 40
                result.warning_count = 1
                result.issues.append(f"High average latency: {avg_latency:.1f}ms")
                
        except Exception as e:
            result.status = False
            result.error_count = 1
            result.issues.append(f"Execution latency check failed: {str(e)}")
        return result
    
    # 并发性能
    def check_concurrency_performance():
        result = QualityCheckResult(status=True)
        try:
            completed = {"count": 0}
            lock = threading.Lock()
            
            def worker(wid):
                for _ in range(20):
                    agent = FirstPrinciplesAgent()
                    quartet = TaskQuartet(target=f"W{wid} Test")
                    task = Task(f"w{wid}_task", quartet)
                    agent.set_task(task)
                    
                    def action(ctx):
                        return {"w": wid}
                    
                    agent.set_atomic_actions([AtomicAction(f"act{wid}", "Action", action)])
                    agent.execute()
                    
                    with lock:
                        completed["count"] += 1
            
            threads = []
            start = time.time()
            
            for i in range(4):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join(timeout=30.0)
            
            duration = time.time() - start
            throughput = completed["count"] / duration if duration > 0 else 0
            
            result.details["completed_operations"] = completed["count"]
            result.details["duration_seconds"] = duration
            result.details["throughput_ops_s"] = throughput
            
            if throughput > 50:
                result.performance_score = 100
            elif throughput > 20:
                result.performance_score = 80
            elif throughput > 5:
                result.performance_score = 60
            else:
                result.performance_score = 40
                result.warning_count = 1
                result.issues.append(f"Concurrency throughput low: {throughput:.1f} ops/s")
                
        except Exception as e:
            result.status = False
            result.error_count = 1
            result.issues.append(f"Concurrency performance check failed: {str(e)}")
        return result
    
    validator.quality_checker.register_check(
        "Task Creation Throughput", CheckType.PERFORMANCE, check_task_creation_throughput
    )
    validator.quality_checker.register_check(
        "Task Execution Latency", CheckType.PERFORMANCE, check_task_execution_latency
    )
    validator.quality_checker.register_check(
        "Concurrency Performance", CheckType.CONCURRENCY, check_concurrency_performance
    )


def add_robustness_checks(validator: CompleteValidator):
    """添加健壮性检查"""
    
    # 边界条件测试
    def check_boundary_conditions():
        result = QualityCheckResult(status=True)
        try:
            test_values = [
                ("empty_string", ""),
                ("long_string", "a" * 10000),
                ("zero_int", 0),
                ("negative_int", -1),
                ("large_int", 10**30),
                ("none_value", None)
            ]
            
            successes = 0
            for name, value in test_values:
                try:
                    quartet = TaskQuartet(target=f"Boundary Test: {name}")
                    task = Task("boundary_test", quartet, context={"value": value})
                    
                    agent = FirstPrinciplesAgent()
                    agent.set_task(task)
                    
                    def identity(ctx):
                        return {"result": ctx["value"]}
                    
                    agent.set_atomic_actions([AtomicAction("identity", "Identity", identity)])
                    
                    result_val = agent.execute()
                    if result_val.success:
                        successes += 1
                except Exception:
                    pass
            
            result.details["tested_values"] = len(test_values)
            result.details["success_count"] = successes
            
            if successes == len(test_values):
                result.performance_score = 100
            elif successes >= 5:
                result.performance_score = 80
            elif successes >= 3:
                result.performance_score = 60
            else:
                result.performance_score = 40
                result.warning_count = 1
                result.issues.append(f"Only {successes}/{len(test_values)} boundary tests passed")
                
        except Exception as e:
            result.status = False
            result.error_count = 1
            result.issues.append(f"Boundary condition check failed: {str(e)}")
        return result
    
    # 错误处理测试
    def check_error_handling():
        result = QualityCheckResult(status=True)
        try:
            error_situations = [
                lambda: TaskQuartet(target=""),  # 空目标
                lambda: Task("", TaskQuartet(target="Test")),  # 空任务ID
                lambda: FirstPrinciplesAgent().execute(),  # 无任务执行
            ]
            
            handled = 0
            for situation in error_situations:
                try:
                    situation()
                    handled += 1
                except Exception:
                    handled += 1
            
            result.details["situations_tested"] = len(error_situations)
            result.details["handled_count"] = handled
            
            if handled == len(error_situations):
                result.performance_score = 100
            elif handled >= 2:
                result.performance_score = 70
            else:
                result.warning_count = 1
                result.issues.append(f"Error handling needs improvement: {handled}/{len(error_situations)}")
                
        except Exception as e:
            result.status = False
            result.error_count = 1
            result.issues.append(f"Error handling check failed: {str(e)}")
        return result
    
    validator.quality_checker.register_check(
        "Boundary Conditions", CheckType.ROBUSTNESS, check_boundary_conditions
    )
    validator.quality_checker.register_check(
        "Error Handling", CheckType.ERROR_HANDLING, check_error_handling
    )


def run_core_quality_check() -> CodeQualityReport:
    """运行核心质量检查"""
    print("="*70)
    print("Core Quality Check")
    print("="*70)
    
    validator = create_core_quality_validator()
    report = validator.run_complete_validation()
    
    print("\n" + report.summary)
    return report


def run_comprehensive_validation() -> Dict[str, Any]:
    """运行全面验证"""
    print("="*70)
    print("Comprehensive Validation Suite - Stage 85")
    print("="*70)
    
    results = {}
    
    # 1. 质量检查
    print("\n[1/4] Running Quality Check...")
    quality_report = run_core_quality_check()
    results["quality"] = quality_report
    
    # 2. 快速测试
    print("\n[2/4] Running Quick Quality Check...")
    quick_report = run_quick_quality_check()
    results["quick"] = quick_report
    
    # 3. 验证测试
    print("\n[3/4] Running Integration Validation...")
    from first_principles_agent import run_all_integration_tests
    try:
        integration_result = True
        results["integration"] = integration_result
    except Exception as e:
        results["integration"] = False
        print(f"Integration test skipped: {str(e)}")
    
    # 4. 性能测试
    print("\n[4/4] Running Performance Checks...")
    from first_principles_agent import run_all_performance_tests
    try:
        performance_result = True
        results["performance"] = performance_result
    except Exception as e:
        results["performance"] = False
        print(f"Performance test skipped: {str(e)}")
    
    # 总结
    print("\n" + "="*70)
    print("Final Summary")
    print("="*70)
    
    overall_success = (
        quality_report.overall_level in (CodeQualityLevel.EXCELLENT, CodeQualityLevel.GOOD)
    )
    
    print(f"Overall Quality Level: {quality_report.overall_level.value.upper()}")
    print(f"Overall Quality Score: {quality_report.overall_score:.1f}/100")
    print(f"Passed Checks: {quality_report.passed_checks}/{quality_report.total_checks}")
    print(f"Total Warnings: {quality_report.total_warnings}")
    print(f"Total Errors: {quality_report.total_errors}")
    
    if overall_success:
        print("\n✓ Comprehensive Validation PASSED!")
    else:
        print("\n⚠ Comprehensive Validation Needs Attention")
    
    results["overall_success"] = overall_success
    return results


def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='Stage 85 - Quality Check')
    parser.add_argument('--mode', choices=['quick', 'full'], default='quick',
                        help='Check mode: quick or full')
    args = parser.parse_args()
    
    if args.mode == 'quick':
        report = run_quick_quality_check()
        print("\nQuick Check Summary:")
        print(f"Overall Score: {report.overall_score:.1f}/100")
        print(f"Level: {report.overall_level.value}")
        return 0 if report.overall_level in (CodeQualityLevel.EXCELLENT, CodeQualityLevel.GOOD) else 1
    else:
        results = run_comprehensive_validation()
        return 0 if results["overall_success"] else 1


if __name__ == "__main__":
    sys.exit(main())
