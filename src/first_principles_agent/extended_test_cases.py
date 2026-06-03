"""
扩展专项测试用例 - 第82阶段
包含边界测试、负载测试、故障注入和性能基准测试
"""

import time
import random
from typing import List, Tuple, Any

from first_principles_agent.extended_tests import (
    BoundaryTestType, FaultType, LoadPattern,
    LoadTestCase, BoundaryTestCase, FaultInjectionTestCase, BenchmarkTestCase,
    LoadTestConfig, FaultInjectionConfig,
    create_load_test, create_boundary_test,
    create_fault_injection_test, create_benchmark_test
)
from first_principles_agent.special_tests import TestSuite, SpecialTestManager
from first_principles_agent import (
    Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction,
    ConfigManager, ConfigItem, ConfigType,
    PermissionManager, Permission, Role, User, Resource,
    PermissionType, ResourceType
)


def create_core_extended_tests() -> TestSuite:
    """创建核心扩展测试套件"""
    suite = TestSuite("Core Extended Tests")
    
    # 1. 添加边界测试
    suite.add_test(create_task_quartet_boundary_test())
    suite.add_test(create_config_boundary_test())
    
    # 2. 添加负载测试
    suite.add_test(create_task_load_test())
    suite.add_test(create_config_load_test())
    
    # 3. 添加故障注入测试
    suite.add_test(create_fault_tolerance_test())
    
    # 4. 添加性能基准测试
    suite.add_test(create_performance_benchmark_test())
    
    return suite


def create_task_quartet_boundary_test() -> BoundaryTestCase:
    """创建任务四元组边界测试"""
    test_values: List[Tuple[Any, BoundaryTestType, bool]] = []
    
    # 空值测试
    test_values.append(("", BoundaryTestType.EMPTY, False))
    test_values.append(None, BoundaryTestType.NULL, False)
    
    # 空字符串
    test_values.append(("", BoundaryTestType.EMPTY, False))
    
    # 数值边界
    test_values.append((0, BoundaryTestType.ZERO, True))
    test_values.append((1, BoundaryTestType.MINIMUM, True))
    test_values.append((-1, BoundaryTestType.NEGATIVE, True))
    test_values.append((2**31-1, BoundaryTestType.MAXIMUM, True))
    test_values.append((-2**31, BoundaryTestType.MINIMUM, True))
    
    # 大数值
    test_values.append((10**100, BoundaryTestType.EXTREME, True))
    
    def test_task_creation(value):
        """测试任务创建"""
        try:
            quartet = TaskQuartet(target=f"Test {value}")
            task = Task(f"task_{value}", quartet, context={"value": value})
            return task is not None
        except Exception:
            return False
    
    return create_boundary_test(
        "Task Quartet Boundary Tests",
        test_task_creation,
        test_values
    )


def create_config_boundary_test() -> BoundaryTestCase:
    """创建配置边界测试"""
    test_values: List[Tuple[Any, BoundaryTestType, bool]] = []
    
    # 字符串边界
    test_values.append(("", BoundaryTestType.EMPTY, True))
    test_values.append(("a"*1000, BoundaryTestType.EXTREME, True))
    
    # 数值边界
    test_values.append((0, BoundaryTestType.ZERO, True))
    test_values.append((1000000, BoundaryTestType.MAXIMUM, True))
    test_values.append((-1000000, BoundaryTestType.MINIMUM, True))
    
    # 列表边界
    test_values.append(([], BoundaryTestType.EMPTY, True))
    test_values.append(([1]*1000, BoundaryTestType.EXTREME, True))
    
    manager = ConfigManager()
    
    def test_config(value):
        """测试配置操作"""
        try:
            key = f"test_{id(value)}"
            manager.register_config_item(ConfigItem(
                key=key,
                type_=ConfigType.STRING if isinstance(value, str) 
                       else ConfigType.INTEGER if isinstance(value, int)
                       else ConfigType.LIST if isinstance(value, list)
                       else ConfigType.STRING
            ))
            manager.set(key, value)
            retrieved = manager.get(key)
            return retrieved == value
        except Exception:
            return False
    
    return create_boundary_test(
        "Config Boundary Tests",
        test_config,
        test_values
    )


def create_task_load_test() -> LoadTestCase:
    """创建任务执行负载测试"""
    
    def task_operation(index):
        """任务执行操作"""
        try:
            quartet = TaskQuartet(target=f"Load Test Task {index}")
            task = Task(f"task_{index}", quartet, context={"index": index})
            
            agent = FirstPrinciplesAgent()
            agent.set_task(task)
            
            def simple_func(ctx):
                return {"result": ctx["index"] * 2}
            
            action = AtomicAction("double", "Double index", simple_func)
            agent.set_atomic_actions([action])
            
            result = agent.execute()
            return result.success
        except Exception:
            return False
    
    return create_load_test(
        "Task Execution Load Test",
        task_operation,
        pattern=LoadPattern.RAMP,
        base_concurrency=5,
        max_concurrency=30,
        duration=45.0
    )


def create_config_load_test() -> LoadTestCase:
    """创建配置负载测试"""
    manager = ConfigManager()
    
    def config_operation(index):
        """配置操作"""
        try:
            key = f"config_{index % 100}"
            value = random.randint(0, 1000000)
            
            # 混合操作
            if index % 3 == 0:
                # 读取操作
                val = manager.get(key, 0)
                return isinstance(val, (int, type(None)))
            elif index % 3 == 1:
                # 写入操作
                error = manager.set(key, value)
                return error is None
            else:
                # 注册配置项
                manager.register_config_item(ConfigItem(
                    key=f"new_{key}",
                    type_=ConfigType.INTEGER,
                    default=0
                ))
                return True
        except Exception:
            return False
    
    return create_load_test(
        "Config Load Test",
        config_operation,
        pattern=LoadPattern.BURSTY,
        base_concurrency=3,
        max_concurrency=15,
        duration=30.0
    )


def create_fault_tolerance_test() -> FaultInjectionTestCase:
    """创建容错测试"""
    operation_count = 0
    
    def test_operation():
        """测试操作"""
        nonlocal operation_count
        operation_count += 1
        
        # 模拟一些处理
        result = 0
        for i in range(100):
            result += i
        
        return result
    
    config = FaultInjectionConfig(
        fault_type=FaultType.EXCEPTION,
        rate=0.05,  # 5% 的错误率
        exception_class=RuntimeError,
        exception_message="Simulated fault"
    )
    
    return FaultInjectionTestCase(
        "Fault Tolerance Test",
        test_operation,
        config,
        duration=30.0
    )


def create_performance_benchmark_test() -> BenchmarkTestCase:
    """创建性能基准测试"""
    
    def task_creation():
        """任务创建基准"""
        quartet = TaskQuartet(target="Benchmark Task")
        task = Task("benchmark_task", quartet, context={"x": 1})
        return task
    
    def simple_calculation():
        """简单计算基准"""
        return sum(range(1000))
    
    def list_manipulation():
        """列表操作基准"""
        lst = list(range(1000))
        lst.reverse()
        lst.sort()
        return len(lst)
    
    def config_operation():
        """配置操作基准"""
        manager = ConfigManager()
        manager.register_config_item(ConfigItem(
            key="benchmark",
            type_=ConfigType.INTEGER,
            default=0
        ))
        manager.set("benchmark", 42)
        val = manager.get("benchmark")
        return val == 42
    
    functions = {
        "Task Creation": task_creation,
        "Simple Calculation": simple_calculation,
        "List Manipulation": list_manipulation,
        "Config Operation": config_operation
    }
    
    return create_benchmark_test(
        "Performance Benchmark",
        functions,
        iterations=1000
    )


def run_all_extended_tests():
    """运行所有扩展测试"""
    print("="*70)
    print("Running Extended Tests (Stage 82)")
    print("="*70)
    
    suite = create_core_extended_tests()
    results = suite.run_all()
    
    print("\n" + "="*70)
    print("Test Results Summary")
    print("="*70)
    
    for result in results:
        print(f"\n{result.test_name} ({result.category.value}):")
        print(f"  Status: {result.status.value}")
        print(f"  Duration: {result.duration:.2f}s")
        print(f"  Operations: {result.metrics.operations_total}")
        print(f"  Success: {result.metrics.operations_success}")
        print(f"  Failed: {result.metrics.operations_failed}")
        
        if result.metrics.throughput > 0:
            print(f"  Throughput: {result.metrics.throughput:.2f} op/s")
        
        if result.metrics.avg_latency > 0:
            print(f"  Avg latency: {result.metrics.avg_latency * 1000:.2f}ms")
            print(f"  p95 latency: {result.metrics.p95_latency * 1000:.2f}ms")
        
        if result.error_message:
            print(f"  Error: {result.error_message}")
    
    summary = suite.get_summary()
    print("\n" + "="*70)
    print("Overall Summary")
    print("="*70)
    print(f"Total tests: {summary['total']}")
    print(f"Passed: {summary.get('passed', 0)}")
    print(f"Failed: {summary.get('failed', 0)}")
    print(f"Defects: {summary.get('defects', 0)}")
    
    return suite
