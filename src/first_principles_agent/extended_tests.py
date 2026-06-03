"""
扩展专项测试模块 - 第82阶段
包含负载测试、边界测试、故障注入和性能基准测试
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple, Set, Union
import threading
import time
import random
import uuid
from collections import defaultdict, deque

from first_principles_agent.special_tests import (
    TestPhase, TestStatus, TestCategory,
    TestMetrics, TestCaseResult, Defect,
    TestCase, TestSuite, SpecialTestManager
)


class BoundaryTestType(Enum):
    """边界测试类型"""
    MINIMUM = "minimum"  # 最小值
    MAXIMUM = "maximum"  # 最大值
    ZERO = "zero"  # 零值
    EMPTY = "empty"  # 空值
    NULL = "null"  # 空指针/None
    NEGATIVE = "negative"  # 负数
    OVERFLOW = "overflow"  # 溢出值
    UNDERFLOW = "underflow"  # 下溢值
    EXTREME = "extreme"  # 极端值


class FaultType(Enum):
    """故障注入类型"""
    EXCEPTION = "exception"  # 异常注入
    DELAY = "delay"  # 延迟注入
    ERROR = "error"  # 错误返回
    CORRUPT_DATA = "corrupt_data"  # 数据损坏
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # 资源耗尽
    NETWORK_FAILURE = "network_failure"  # 网络故障
    DISK_FAILURE = "disk_failure"  # 磁盘故障
    PARTIAL_FAILURE = "partial_failure"  # 部分失败


class LoadPattern(Enum):
    """负载模式"""
    CONSTANT = "constant"  # 恒定负载
    STEP = "step"  # 阶梯式负载
    RAMP = "ramp"  # 斜坡式负载
    PEAK = "peak"  # 峰值负载
    BURSTY = "bursty"  # 突发式负载
    RANDOM = "random"  # 随机负载


@dataclass
class BoundaryTestCase:
    """边界测试用例"""
    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    boundary_type: BoundaryTestType
    value: Any
    expected_success: bool = True
    description: str = ""


@dataclass
class FaultInjectionConfig:
    """故障注入配置"""
    fault_type: FaultType
    rate: float = 0.1  # 故障发生概率
    delay_min: float = 0.1
    delay_max: float = 1.0
    exception_class: type = Exception
    exception_message: str = "Injected fault"
    custom_error: Any = None


@dataclass
class LoadTestConfig:
    """负载测试配置"""
    pattern: LoadPattern = LoadPattern.CONSTANT
    base_concurrency: int = 10
    max_concurrency: int = 50
    step_duration: float = 30.0
    ramp_steps: int = 10
    duration: float = 60.0


class BoundaryTestCase(TestCase):
    """边界测试用例"""
    
    def __init__(
        self,
        name: str,
        test_function: Callable[[Any], bool],
        boundary_values: List[BoundaryTestCase]
    ):
        super().__init__(name, TestCategory.BOUNDARY)
        self.test_function = test_function
        self.boundary_values = boundary_values
        self.results: List[Tuple[BoundaryTestCase, bool, Optional[str]]] = []
    
    def setup(self):
        """测试准备"""
        self.results = []
    
    def execute(self):
        """执行边界测试"""
        for case in self.boundary_values:
            try:
                success = self.test_function(case.value)
                self.results.append((case, success, None))
                
                # 如果预期成功但实际失败，或者反之
                if success != case.expected_success:
                    self.metrics.operations_failed += 1
                else:
                    self.metrics.operations_success += 1
                
            except Exception as e:
                self.results.append((case, False, str(e)))
                self.metrics.operations_failed += 1
                self.metrics.errors.append(f"Case {case.name}: {str(e)}")
            
            self.metrics.operations_total += 1
    
    def verify(self):
        """验证结果"""
        failed = sum(1 for _, success, _ in self.results if not success)
        return failed == 0


class FaultInjectionTestCase(TestCase):
    """故障注入测试用例"""
    
    def __init__(
        self,
        name: str,
        test_function: Callable,
        config: FaultInjectionConfig,
        duration: float = 30.0
    ):
        super().__init__(name, TestCategory.FAULT_INJECTION)
        self.test_function = test_function
        self.config = config
        self.duration = duration
        self.injected_faults = 0
        self.successful_operations = 0
        self._stop_event = threading.Event()
    
    def _should_inject_fault(self) -> bool:
        """决定是否注入故障"""
        return random.random() < self.config.rate
    
    def _inject_fault(self):
        """注入故障"""
        fault_type = self.config.fault_type
        
        if fault_type == FaultType.EXCEPTION:
            raise self.config.exception_class(self.config.exception_message)
        elif fault_type == FaultType.DELAY:
            delay = random.uniform(self.config.delay_min, self.config.delay_max)
            time.sleep(delay)
            return None
        elif fault_type == FaultType.ERROR:
            return self.config.custom_error
        elif fault_type == FaultType.CORRUPT_DATA:
            return "CORRUPTED_DATA"
        elif fault_type == FaultType.RESOURCE_EXHAUSTION:
            raise MemoryError("Resource exhaustion")
        
        return None
    
    def execute(self):
        """执行故障注入测试"""
        start_time = time.time()
        
        while not self._stop_event.is_set() and (time.time() - start_time) < self.duration:
            try:
                self.metrics.operations_total += 1
                
                if self._should_inject_fault():
                    self.injected_faults += 1
                    try:
                        self._inject_fault()
                    except Exception:
                        # 这里不记录为失败，因为故障是预期的
                        pass
                
                # 执行正常操作
                result = self.test_function()
                
                self.successful_operations += 1
                self.metrics.operations_success += 1
                
            except Exception as e:
                self.metrics.operations_failed += 1
                self.metrics.errors.append(str(e))
            
            # 小延迟，避免太密集
            time.sleep(0.001)


class LoadTestCase(TestCase):
    """负载测试用例"""
    
    def __init__(
        self,
        name: str,
        operation: Callable[[int], bool],
        config: LoadTestConfig
    ):
        super().__init__(name, TestCategory.LOAD)
        self.operation = operation
        self.config = config
        self._stop_event = threading.Event()
        self._workers: List[threading.Thread] = []
        self._current_concurrency = config.base_concurrency
        self._latencies = []
        self._latency_lock = threading.Lock()
    
    def _get_current_concurrency(self, elapsed: float) -> int:
        """获取当前并发数"""
        pattern = self.config.pattern
        
        if pattern == LoadPattern.CONSTANT:
            return self.config.base_concurrency
        elif pattern == LoadPattern.STEP:
            step_count = int(elapsed / self.config.step_duration)
            concurrency = self.config.base_concurrency + (
                (self.config.max_concurrency - self.config.base_concurrency) * 
                (step_count / self.config.ramp_steps)
            )
            return min(int(concurrency), self.config.max_concurrency)
        elif pattern == LoadPattern.RAMP:
            progress = elapsed / self.config.duration
            concurrency = self.config.base_concurrency + (
                (self.config.max_concurrency - self.config.base_concurrency) * progress
            )
            return min(int(concurrency), self.config.max_concurrency)
        elif pattern == LoadPattern.PEAK:
            progress = elapsed / self.config.duration
            if progress < 0.25 or progress > 0.75:
                return self.config.base_concurrency
            else:
                return self.config.max_concurrency
        elif pattern == LoadPattern.BURSTY:
            if random.random() < 0.3:
                return self.config.max_concurrency
            else:
                return self.config.base_concurrency
        elif pattern == LoadPattern.RANDOM:
            return random.randint(
                self.config.base_concurrency,
                self.config.max_concurrency
            )
        else:
            return self.config.base_concurrency
    
    def _worker(self, worker_id: int):
        """工作线程"""
        while not self._stop_event.is_set():
            try:
                op_start = time.time()
                success = self.operation(worker_id)
                op_end = time.time()
                
                with self._latency_lock:
                    self._latencies.append(op_end - op_start)
                
                if success:
                    self.metrics.operations_success += 1
                else:
                    self.metrics.operations_failed += 1
                
            except Exception as e:
                self.metrics.operations_failed += 1
                self.metrics.errors.append(str(e))
            
            self.metrics.operations_total += 1
            
            # 小延迟
            time.sleep(0.001)
    
    def _concurrency_manager(self):
        """并发数管理器"""
        start_time = time.time()
        while not self._stop_event.is_set() and (time.time() - start_time) < self.config.duration:
            elapsed = time.time() - start_time
            desired = self._get_current_concurrency(elapsed)
            
            if desired != self._current_concurrency:
                self._adjust_workers(desired)
                self._current_concurrency = desired
            
            time.sleep(1)
    
    def _adjust_workers(self, desired: int):
        """调整工作线程数量"""
        current = len(self._workers)
        
        while len(self._workers) < desired:
            worker = threading.Thread(
                target=self._worker,
                args=(len(self._workers),),
                daemon=True
            )
            worker.start()
            self._workers.append(worker)
        
        # 对于减少的情况，我们不主动停止，依靠_stop_event
    
    def execute(self):
        """执行负载测试"""
        start_time = time.time()
        
        # 启动并发管理器
        manager = threading.Thread(target=self._concurrency_manager, daemon=True)
        manager.start()
        
        # 等待测试完成
        time.sleep(self.config.duration)
        
        # 停止所有工作
        self._stop_event.set()
        
        # 等待所有线程结束
        for worker in self._workers:
            worker.join(timeout=2.0)
        
        # 计算指标
        self._calculate_latency_metrics()
        self.metrics.end_time = time.time()
    
    def _calculate_latency_metrics(self):
        """计算延迟指标"""
        if not self._latencies:
            return
        
        with self._latency_lock:
            sorted_latencies = sorted(self._latencies)
            n = len(sorted_latencies)
            
            self.metrics.min_latency = sorted_latencies[0]
            self.metrics.max_latency = sorted_latencies[-1]
            self.metrics.avg_latency = sum(sorted_latencies) / n
            self.metrics.p50_latency = sorted_latencies[int(n * 0.5)]
            self.metrics.p95_latency = sorted_latencies[int(n * 0.95)] if n > 20 else sorted_latencies[-1]
            self.metrics.p99_latency = sorted_latencies[int(n * 0.99)] if n > 100 else sorted_latencies[-1]


class BenchmarkTestCase(TestCase):
    """性能基准测试用例"""
    
    def __init__(
        self,
        name: str,
        functions_to_benchmark: Dict[str, Callable],
        iterations: int = 1000
    ):
        super().__init__(name, TestCategory.PERFORMANCE)
        self.functions_to_benchmark = functions_to_benchmark
        self.iterations = iterations
        self.benchmark_results: Dict[str, TestMetrics] = {}
    
    def execute(self):
        """执行基准测试"""
        for func_name, func in self.functions_to_benchmark.items():
            metrics = TestMetrics()
            metrics.start_time = time.time()
            
            latencies = []
            
            # 预热
            for _ in range(100):
                try:
                    func()
                except Exception:
                    pass
            
            # 正式测试
            for i in range(self.iterations):
                try:
                    start = time.time()
                    func()
                    end = time.time()
                    
                    latencies.append(end - start)
                    metrics.operations_success += 1
                    
                except Exception as e:
                    metrics.operations_failed += 1
                    metrics.errors.append(str(e))
                
                metrics.operations_total += 1
            
            # 计算指标
            metrics.end_time = time.time()
            metrics.duration = metrics.end_time - metrics.start_time
            
            if latencies:
                sorted_latencies = sorted(latencies)
                n = len(sorted_latencies)
                
                metrics.min_latency = sorted_latencies[0]
                metrics.max_latency = sorted_latencies[-1]
                metrics.avg_latency = sum(sorted_latencies) / n
                metrics.p50_latency = sorted_latencies[int(n * 0.5)]
                metrics.p95_latency = sorted_latencies[int(n * 0.95)] if n > 20 else sorted_latencies[-1]
                metrics.p99_latency = sorted_latencies[int(n * 0.99)] if n > 100 else sorted_latencies[-1]
                metrics.throughput = n / metrics.duration
            
            self.benchmark_results[func_name] = metrics
            self.metrics.operations_total += metrics.operations_total
            self.metrics.operations_success += metrics.operations_success
            self.metrics.operations_failed += metrics.operations_failed
    
    def get_result_summary(self) -> str:
        """获取结果摘要"""
        summary = []
        for func_name, metrics in self.benchmark_results.items():
            summary.append(f"\n{func_name}:")
            summary.append(f"  Throughput: {metrics.throughput:.2f} op/s")
            summary.append(f"  Avg latency: {metrics.avg_latency * 1000:.2f}ms")
            summary.append(f"  p95 latency: {metrics.p95_latency * 1000:.2f}ms")
            summary.append(f"  p99 latency: {metrics.p99_latency * 1000:.2f}ms")
            summary.append(f"  Operations: {metrics.operations_total}")
        return "\n".join(summary)


def create_load_test(
    name: str,
    operation: Callable[[int], bool],
    pattern: LoadPattern = LoadPattern.CONSTANT,
    base_concurrency: int = 10,
    max_concurrency: int = 50,
    duration: float = 60.0
) -> LoadTestCase:
    """创建负载测试用例"""
    config = LoadTestConfig(
        pattern=pattern,
        base_concurrency=base_concurrency,
        max_concurrency=max_concurrency,
        duration=duration
    )
    return LoadTestCase(name, operation, config)


def create_boundary_test(
    name: str,
    test_function: Callable[[Any], bool],
    values_to_test: List[Tuple[Any, BoundaryTestType, bool]]
) -> BoundaryTestCase:
    """创建边界测试用例"""
    cases = []
    for value, boundary_type, expect_success in values_to_test:
        case = BoundaryTestCase(
            name=f"{name}_{boundary_type.value}",
            boundary_type=boundary_type,
            value=value,
            expected_success=expect_success
        )
        cases.append(case)
    
    return BoundaryTestCase(name, test_function, cases)


def create_fault_injection_test(
    name: str,
    test_function: Callable,
    fault_type: FaultType,
    rate: float = 0.1,
    duration: float = 30.0
) -> FaultInjectionTestCase:
    """创建故障注入测试用例"""
    config = FaultInjectionConfig(fault_type=fault_type, rate=rate)
    return FaultInjectionTestCase(name, test_function, config, duration)


def create_benchmark_test(
    name: str,
    functions: Dict[str, Callable],
    iterations: int = 1000
) -> BenchmarkTestCase:
    """创建性能基准测试"""
    return BenchmarkTestCase(name, functions, iterations)
