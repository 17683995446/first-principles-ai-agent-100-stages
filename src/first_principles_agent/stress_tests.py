"""
压力测试模块 - Stress Test Module
针对核心功能的压力测试
"""

import time
import threading
import random
from typing import List, Dict, Any

from first_principles_agent import (
    Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction,
    ConfigManager, ConfigItem, ConfigType,
    PermissionManager, Permission, Role, User, Resource,
    PermissionType, ResourceType,
    get_logger, info, debug, warning, error
)
from first_principles_agent.special_tests import (
    StressTestCase, TestSuite, SpecialTestManager,
    create_stress_test, run_stress_suite
)


def create_simple_stress_test(name: str, duration: float, concurrency: int) -> StressTestCase:
    """创建简单压力测试用例 - 基础任务执行测试
    
    Args:
        name: 测试名称
        duration: 持续时间（秒）
        concurrency: 并发数
    """
    
    class SimpleTaskStressTest(StressTestCase):
        def __init__(self):
            super().__init__(name, duration, concurrency)
            self.task_counter = 0
            self._counter_lock = threading.Lock()
        
        def operation(self, index: int) -> bool:
            """执行简单的数学运算模拟简单任务"""
            try:
                task_quartet = TaskQuartet(
                    target=f"Stress test task {index}: Add numbers")
                
                task = Task(f"task_{index}", task_quartet, context={"x": 10, "y": 20})
                
                agent = FirstPrinciplesAgent()
                agent.set_task(task)
                
                def add(ctx):
                    return {"result": ctx["x"] + ctx["y"]}
                
                action = AtomicAction("add", "Add numbers", add)
                agent.set_atomic_actions([action])
                
                result = agent.execute()
                
                with self._counter_lock:
                    self.task_counter += 1
                
                return result.success
                
            except Exception as e:
                self.metrics.errors.append(f"Task error: {str(e)}")
                return False
    
    return SimpleTaskStressTest()


def create_config_stress_test(name: str, duration: float, concurrency: int) -> StressTestCase:
    """创建配置管理压力测试用例
    
    Args:
        name: 测试名称
        duration: 持续时间（秒）
        concurrency: 并发数
    """
    class ConfigStressTest(StressTestCase):
        def __init__(self):
            super().__init__(name, duration, concurrency)
            self._manager = ConfigManager()
            self._keys = []
            self._manager.register_config_item(ConfigItem(
                key="stress.test.key", type_=ConfigType.INTEGER, default=0))
        
        def operation(self, index: int) -> bool:
            """执行配置读写操作"""
            try:
                key = f"stress.key.{index % 100}"
                val = random.randint(1, 1000)
                
                # 注册新配置项
                if index % 10 == 0:
                    self._manager.register_config_item(ConfigItem(
                        key=key, type_=ConfigType.INTEGER, default=0))
                
                # 写配置
                self._manager.set(key, val)
                
                # 读配置
                read_val = self._manager.get(key, 0)
                
                return True
                
            except Exception as e:
                self.metrics.errors.append(f"Config error: {str(e)}")
                return False
    
    return ConfigStressTest()


def create_logging_stress_test(name: str, duration: float, concurrency: int) -> StressTestCase:
    """创建日志系统压力测试用例
    
    Args:
        name: 测试名称
        duration: 持续时间（秒）
        concurrency: 并发数
    """
    class LoggingStressTest(StressTestCase):
        def __init__(self):
            super().__init__(name, duration, concurrency)
            self.log_counter = 0
            self._counter_lock = threading.Lock()
        
        def operation(self, index: int) -> bool:
            """执行日志操作"""
            try:
                msg_types = ["info", "debug", "warning", "error"]
                msg_type = random.choice(msg_types)
                
                if msg_type == "info":
                    info(f"Stress test log message from worker {index}")
                elif msg_type == "debug":
                    debug(f"Stress test debug from worker {index}")
                elif msg_type == "warning":
                    warning(f"Stress test warning from worker {index}")
                else:
                    error(f"Stress test error from worker {index}")
                
                with self._counter_lock:
                    self.log_counter += 1
                
                return True
                
            except Exception as e:
                self.metrics.errors.append(f"Logging error: {str(e)}")
                return False
    
    return LoggingStressTest()


def create_resource_stress_test(name: str, duration: float, concurrency: int) -> StressTestCase:
    """创建权限管理压力测试用例
    
    Args:
        name: 测试名称
        duration: 持续时间（秒）
        concurrency: 并发数
    """
    class ResourceStressTest(StressTestCase):
        def __init__(self):
            super().__init__(name, duration, concurrency)
            self._manager = PermissionManager()
            self._setup()
        
        def _setup(self):
            """初始化测试数据"""
            self._manager.register_permission(Permission(
                name="stress.read", PermissionType.READ, ResourceType.TASK))
            self._manager.register_role(Role(
                name="stress.role", permissions={"stress.read"}))
        
        def operation(self, index: int) -> bool:
            """执行权限检查操作"""
            try:
                user = self._manager.create_user(f"stress_user_{index}")
                
                if index % 2 == 0:
                    self._manager.assign_role(user.id, "stress.role")
                
                self._manager.check_user_permission(
                    user.id, "test_resource", PermissionType.READ)
                
                return True
                
            except Exception as e:
                self.metrics.errors.append(f"Permission error: {str(e)}")
                return False
    
    return ResourceStressTest()


def create_memory_allocation_stress_test(name: str, duration: float, concurrency: int) -> StressTestCase:
    """创建内存分配压力测试用例
    
    Args:
        name: 测试名称
        duration: 持续时间（秒）
        concurrency: 并发数
    """
    class MemoryAllocationStressTest(StressTestCase):
        def __init__(self):
            super().__init__(name, duration, concurrency)
            self._allocations = []
            self._lock = threading.Lock()
        
        def operation(self, index: int) -> bool:
            """执行内存分配操作"""
            try:
                size = random.randint(100, 10000)
                data = [random.randint(0, 255) for _ in range(size)]
                
                with self._lock:
                    self._allocations.append(data)
                    if len(self._allocations) > 100:
                        self._allocations.pop(0)
                
                return True
                
            except Exception as e:
                self.metrics.errors.append(f"Memory allocation error: {str(e)}")
                return False
    
    return MemoryAllocationStressTest()


def create_mixed_workload_stress_test(name: str, duration: float, concurrency: int) -> StressTestCase:
    """创建混合工作负载压力测试用例
    
    Args:
        name: 测试名称
        duration: 持续时间（秒）
        concurrency: 并发数
    """
    class MixedWorkloadStressTest(StressTestCase):
        def __init__(self):
            super().__init__(name, duration, concurrency)
            self._config_manager = ConfigManager()
            self._config_manager.register_config_item(ConfigItem(
                key="mixed.test", type_=ConfigType.INTEGER, default=0))
        
        def operation(self, index: int) -> bool:
            """执行混合操作：任务 + 配置 + 日志"""
            try:
                op_type = random.randint(0, 3)
                
                if op_type == 0:
                    # 任务执行
                    task_quartet = TaskQuartet(target="Mixed test task")
                    task = Task(f"mixed_{index}", task_quartet)
                    agent = FirstPrinciplesAgent()
                    agent.set_task(task)
                
                elif op_type == 1:
                    # 配置操作
                    self._config_manager.set("mixed.test", index)
                
                elif op_type == 2:
                    # 日志操作
                    info(f"Mixed workload log from {index}")
                
                else:
                    # 简单计算
                    result = sum(range(1000))
                
                return True
                
            except Exception as e:
                self.metrics.errors.append(f"Mixed error: {str(e)}")
                return False
    
    return MixedWorkloadStressTest()


def create_core_stress_suite() -> TestSuite:
    """创建核心压力测试套件
    
    Returns:
        测试套件
    """
    manager = SpecialTestManager()
    suite = manager.create_suite("Core Stress Test Suite")
    
    # 1. 简单任务压力测试
    simple_test = create_simple_stress_test(
        "Simple Task Stress",
        duration=10.0,
        concurrency=5
    )
    
    # 2. 配置管理压力测试
    config_test = create_config_stress_test(
        "Config Management Stress",
        duration=10.0,
        concurrency=5
    )
    
    # 3. 日志系统压力测试
    logging_test = create_logging_stress_test(
        "Logging System Stress",
        duration=10.0,
        concurrency=5
    )
    
    # 4. 混合工作负载
    mixed_test = create_mixed_workload_stress_test(
        "Mixed Workload Stress",
        duration=15.0,
        concurrency=3
    )
    
    suite.add_tests([
        simple_test, config_test, logging_test, mixed_test])
    
    return suite


def run_all_core_stress_tests():
    """运行所有核心压力测试
    
    Returns:
        测试套件
    """
    print("=" * 70)
    print("CORE STRESS TESTS")
    print("=" * 70)
    
    suite = create_core_stress_suite()
    
    start_time = time.time()
    results = suite.run_all()
    total_time = time.time() - start_time
    
    print(f"\nTOTAL TIME: {total_time:.2f} seconds")
    print("=" * 70)
    
    summary = suite.get_summary()
    print(f"TEST SUMMARY:")
    print(f"  Total: {summary['total']}")
    print(f"  Passed: {summary.get('passed', 0)}")
    print(f"  Failed: {summary.get('failed', 0)}")
    print(f"  Errors: {summary.get('error', 0)}")
    print(f"  Defects: {summary['defects']}")
    print("\n" + "=" * 70)
    
    print("\nDETAILED RESULTS:")
    for result in results:
        print(f"\n  {result.test_name}")
        print(f"    Status: {result.status.value}")
        print(f"    Duration: {result.duration:.2f}s")
        print(f"    Operations: {result.metrics.operations_total}")
        print(f"    Success: {result.metrics.operations_success}")
        print(f"    Failed: {result.metrics.operations_failed}")
        print(f"    Throughput: {result.metrics.throughput:.2f} op/s")
        if result.metrics.avg_latency > 0:
            print(f"    Avg Latency: {result.metrics.avg_latency*1000:.2f}ms")
            print(f"    p95 Latency: {result.metrics.p95_latency*1000:.2f}ms")
            print(f"    p99 Latency: {result.metrics.p99_latency*1000:.2f}ms")
        if result.error_message:
            print(f"    Error: {result.error_message}")
    
    if suite.defects:
        print("\nDEFECTS FOUND:")
        for defect in suite.defects:
            print(f"  - {defect.defect_id}")
            print(f"    Test: {defect.test_name}")
            print(f"    Severity: {defect.severity}")
            print(f"    Description: {defect.description}")
    
    return suite


def run_targeted_stress_test(test_name: str, duration: float = 30.0, concurrency: int = 10):
    """运行指定的压力测试
    
    Args:
        test_name: 测试名称
        duration: 持续时间
        concurrency: 并发数
    
    Returns:
        测试套件
    """
    print(f"\nRunning targeted stress test: {test_name}")
    
    manager = SpecialTestManager()
    suite = manager.create_suite("Targeted Stress Test")
    
    if test_name == "task":
        test = create_simple_stress_test("Targeted Task Test", duration, concurrency)
    elif test_name == "config":
        test = create_config_stress_test("Targeted Config Test", duration, concurrency)
    elif test_name == "logging":
        test = create_logging_stress_test("Targeted Logging Test", duration, concurrency)
    else:
        test = create_mixed_workload_stress_test(f"Targeted Mixed Test", duration, concurrency)
    
    suite.add_test(test)
    suite.run_all()
    
    return suite
