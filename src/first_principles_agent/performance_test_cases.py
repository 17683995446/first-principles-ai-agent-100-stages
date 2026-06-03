"""
性能调优与稳定性测试用例 - 第84阶段
"""

import time
import threading
from typing import Dict, Callable

from first_principles_agent.performance_tests import (
    StabilityTestType, PerformanceMetric,
    PerformanceSnapshot, StabilityReport, PerformanceBaseline,
    PerformanceProfiler, StabilityTester, PerformanceBenchmark,
    create_stability_test, run_long_running_test, run_memory_leak_test
)
from first_principles_agent import (
    Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction,
    ConfigManager, ConfigItem, ConfigType
)


def create_core_performance_tests() -> Dict[str, StabilityTester]:
    """创建核心性能测试"""
    tests = {}
    
    # 1. 任务执行稳定性测试
    tests["task_execution"] = create_task_execution_stability_test()
    
    # 2. 配置操作稳定性测试
    tests["config_operations"] = create_config_stability_test()
    
    # 3. 并发任务稳定性测试
    tests["concurrent_tasks"] = create_concurrent_stability_test()
    
    return tests


def create_task_execution_stability_test() -> StabilityTester:
    """创建任务执行稳定性测试"""
    counter = {"value": 0}
    errors = {"count": 0}
    
    def task_operation() -> bool:
        """任务执行操作"""
        try:
            counter["value"] += 1
            
            quartet = TaskQuartet(target=f"Stability Test Task {counter['value']}")
            task = Task(f"stability_task_{counter['value']}", quartet)
            
            agent = FirstPrinciplesAgent()
            agent.set_task(task)
            
            def simple_action(ctx):
                return {"executed": True}
            
            action = AtomicAction("simple", "Simple", simple_action)
            agent.set_atomic_actions([action])
            
            result = agent.execute()
            return result.success
            
        except Exception as e:
            errors["count"] += 1
            return False
    
    tester = StabilityTester("Task Execution Stability")
    tester.configure(
        test_type=StabilityTestType.LONG_RUN,
        duration=300.0,  # 5分钟快速测试
        operations_per_second=2.0
    )
    
    return tester


def create_config_stability_test() -> StabilityTester:
    """创建配置操作稳定性测试"""
    config_manager = ConfigManager()
    counter = {"value": 0}
    
    # 预注册一些配置项
    for i in range(10):
        config_manager.register_config_item(ConfigItem(
            key=f"test.config.{i}",
            type_=ConfigType.INTEGER,
            default=i
        ))
    
    def config_operation() -> bool:
        """配置操作"""
        try:
            counter["value"] += 1
            key = f"test.config.{counter['value'] % 10}"
            
            # 混合操作
            config_manager.set(key, counter['value'])
            value = config_manager.get_int(key, 0)
            
            # 偶尔注册新配置
            if counter['value'] % 50 == 0:
                config_manager.register_config_item(ConfigItem(
                    key=f"test.new.{counter['value']}",
                    type_=ConfigType.STRING,
                    default="value"
                ))
            
            return True
            
        except Exception:
            return False
    
    tester = StabilityTester("Config Operations Stability")
    tester.configure(
        test_type=StabilityTestType.LONG_RUN,
        duration=300.0,
        operations_per_second=5.0
    )
    
    return tester


def create_concurrent_stability_test() -> StabilityTester:
    """创建并发任务稳定性测试"""
    active_agents = {"count": 0}
    max_agents = {"value": 0}
    
    def concurrent_operation() -> bool:
        """并发操作"""
        try:
            # 创建多个任务
            agents = []
            
            for i in range(5):
                quartet = TaskQuartet(target=f"Concurrent Task {i}")
                task = Task(f"concurrent_task_{i}", quartet)
                
                agent = FirstPrinciplesAgent()
                agent.set_task(task)
                
                def simple_action(ctx):
                    return {"result": True}
                
                action = AtomicAction("simple", "Simple", simple_action)
                agent.set_atomic_actions([action])
                
                agents.append(agent)
                active_agents["count"] += 1
            
            max_agents["value"] = max(max_agents["value"], active_agents["count"])
            
            # 并发执行
            threads = []
            for agent in agents:
                def execute_agent(a):
                    a.execute()
                    active_agents["count"] -= 1
                
                t = threading.Thread(target=execute_agent, args=(agent,))
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join(timeout=10.0)
            
            return True
            
        except Exception:
            return False
    
    tester = StabilityTester("Concurrent Tasks Stability")
    tester.configure(
        test_type=StabilityTestType.STRESS,
        duration=300.0,
        operations_per_second=1.0
    )
    
    return tester


def run_performance_comparison():
    """运行性能对比测试"""
    print("="*70)
    print("Performance Comparison Benchmark")
    print("="*70)
    
    benchmark = PerformanceBenchmark()
    
    # 创建基线
    baseline = benchmark.create_baseline(
        name="task_baseline",
        description="Task execution baseline",
        conditions={"concurrency": 1}
    )
    
    # 运行基线测试
    print("\nRunning baseline test...")
    
    def single_task_operation():
        quartet = TaskQuartet(target="Baseline Task")
        task = Task("baseline_task", quartet)
        agent = FirstPrinciplesAgent()
        agent.set_task(task)
        
        def simple_action(ctx):
            return {"result": True}
        
        action = AtomicAction("simple", "Simple", simple_action)
        agent.set_atomic_actions([action])
        
        agent.execute()
    
    results = benchmark.run_benchmark(
        name="task_baseline",
        operations={"single_task": single_task_operation},
        iterations=100
    )
    
    # 记录基线指标
    if "single_task" in results:
        baseline_metrics = results["single_task"]
        benchmark.record_baseline_metrics("task_baseline", baseline_metrics)
        print(f"\nBaseline metrics recorded:")
        print(f"  Avg latency: {baseline_metrics.get('avg_latency', 0)*1000:.2f}ms")
        print(f"  Throughput: {baseline_metrics.get('throughput', 0):.2f} ops/s")
    
    return benchmark, results


def run_stability_tests():
    """运行稳定性测试"""
    print("="*70)
    print("Stability Tests")
    print("="*70)
    
    # 运行任务执行稳定性测试
    print("\n[1/3] Running Task Execution Stability Test...")
    
    counter = {"value": 0}
    
    def task_operation() -> bool:
        try:
            counter["value"] += 1
            quartet = TaskQuartet(target=f"Test Task {counter['value']}")
            task = Task(f"test_task_{counter['value']}", quartet)
            
            agent = FirstPrinciplesAgent()
            agent.set_task(task)
            
            def simple_action(ctx):
                return {"done": True}
            
            action = AtomicAction("simple", "Simple", simple_action)
            agent.set_atomic_actions([action])
            
            return agent.execute().success
        except Exception:
            return False
    
    tester = StabilityTester("Quick Stability Test")
    tester.configure(
        test_type=StabilityTestType.LONG_RUN,
        duration=60.0,  # 1分钟快速测试
        operations_per_second=5.0
    )
    
    report = tester.run(task_operation)
    
    print(f"\n  Operations: {report.total_operations}")
    print(f"  Success Rate: {(100 - report.error_rate):.2f}%")
    print(f"  Throughput: {report.throughput:.2f} ops/s")
    print(f"  Avg Latency: {report.average_latency*1000:.2f}ms")
    print(f"  Memory Growth: {report.memory_growth:.2f}MB")
    
    if report.warnings:
        print(f"\n  Warnings:")
        for warning in report.warnings:
            print(f"    - {warning}")
    
    # 运行配置操作稳定性测试
    print("\n[2/3] Running Config Operations Stability Test...")
    
    config_manager = ConfigManager()
    for i in range(10):
        config_manager.register_config_item(ConfigItem(
            key=f"stability.config.{i}",
            type_=ConfigType.INTEGER,
            default=i
        ))
    
    def config_operation() -> bool:
        try:
            key = f"stability.config.{i % 10}"
            config_manager.set(key, i)
            return config_manager.get_int(key, 0) is not None
        except Exception:
            return False
    
    config_tester = StabilityTester("Config Stability Test")
    config_tester.configure(
        test_type=StabilityTestType.LONG_RUN,
        duration=60.0,
        operations_per_second=10.0
    )
    
    config_report = config_tester.run(config_operation)
    
    print(f"\n  Operations: {config_report.total_operations}")
    print(f"  Success Rate: {(100 - config_report.error_rate):.2f}%")
    print(f"  Throughput: {config_report.throughput:.2f} ops/s")
    
    # 运行并发测试
    print("\n[3/3] Running Concurrent Stability Test...")
    
    def concurrent_operation() -> bool:
        try:
            results = []
            
            def worker(wid):
                quartet = TaskQuartet(target=f"Worker {wid}")
                task = Task(f"worker_task_{wid}", quartet)
                agent = FirstPrinciplesAgent()
                agent.set_task(task)
                
                def action(ctx):
                    return {"wid": wid}
                
                agent.set_atomic_actions([AtomicAction(f"act_{wid}", "Action", action)])
                results.append(agent.execute().success)
            
            threads = []
            for i in range(3):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join(timeout=10.0)
            
            return all(results)
        except Exception:
            return False
    
    concurrent_tester = StabilityTester("Concurrent Stability Test")
    concurrent_tester.configure(
        test_type=StabilityTestType.STRESS,
        duration=60.0,
        operations_per_second=2.0
    )
    
    concurrent_report = concurrent_tester.run(concurrent_operation)
    
    print(f"\n  Operations: {concurrent_report.total_operations}")
    print(f"  Success Rate: {(100 - concurrent_report.error_rate):.2f}%")
    print(f"  Throughput: {concurrent_report.throughput:.2f} ops/s")
    
    # 总结
    print("\n" + "="*70)
    print("Stability Test Summary")
    print("="*70)
    
    all_passed = (
        report.passed and 
        config_report.passed and 
        concurrent_report.passed
    )
    
    if all_passed:
        print("✓ All stability tests passed!")
    else:
        print("⚠ Some stability tests had issues")
        if not report.passed:
            print(f"  - Task Execution: {len(report.issues)} issues")
        if not config_report.passed:
            print(f"  - Config Operations: {len(config_report.issues)} issues")
        if not concurrent_report.passed:
            print(f"  - Concurrent: {len(concurrent_report.issues)} issues")
    
    return all_passed


def run_all_performance_tests():
    """运行所有性能测试"""
    print("="*70)
    print("Stage 84: Performance Tuning & Stability Tests")
    print("="*70)
    
    # 1. 性能基准测试
    benchmark, baseline_results = run_performance_comparison()
    
    # 2. 稳定性测试
    stability_passed = run_stability_tests()
    
    print("\n" + "="*70)
    print("All Performance Tests Complete")
    print("="*70)
    
    return stability_passed
