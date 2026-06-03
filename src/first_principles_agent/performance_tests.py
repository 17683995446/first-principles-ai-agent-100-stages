"""
性能调优与系统稳定性测试模块 - 第84阶段
性能分析、稳定性测试、长运行测试
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple, Set
import threading
import time
import uuid
import gc
import sys
from collections import defaultdict, deque
from contextlib import contextmanager


class StabilityTestType(Enum):
    """稳定性测试类型"""
    LONG_RUN = "long_run"              # 长运行测试
    STRESS = "stress"                  # 压力稳定性测试
    MEMORY_LEAK = "memory_leak"        # 内存泄漏测试
    RESOURCE_LEAK = "resource_leak"    # 资源泄漏测试
    RECOVERY = "recovery"              # 恢复能力测试
    GRACEFUL_DEGRADATION = "graceful_degradation"  # 优雅降级测试


class PerformanceMetric(Enum):
    """性能指标类型"""
    LATENCY_AVG = "latency_avg"
    LATENCY_P50 = "latency_p50"
    LATENCY_P95 = "latency_p95"
    LATENCY_P99 = "latency_p99"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    THREAD_COUNT = "thread_count"
    ERROR_RATE = "error_rate"


@dataclass
class PerformanceSnapshot:
    """性能快照"""
    timestamp: float
    operation_count: int
    error_count: int
    total_duration: float
    avg_latency: float
    min_latency: float
    max_latency: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    cpu_usage: float
    memory_usage: float
    thread_count: int
    gc_counts: Tuple[int, ...]


@dataclass
class StabilityReport:
    """稳定性报告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    test_type: StabilityTestType = StabilityTestType.LONG_RUN
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    error_rate: float = 0.0
    average_latency: float = 0.0
    max_latency: float = 0.0
    throughput: float = 0.0
    memory_growth: float = 0.0  # 内存增长
    thread_growth: int = 0       # 线程增长
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    performance_snapshots: List[PerformanceSnapshot] = field(default_factory=list)
    passed: bool = True
    summary: str = ""


@dataclass
class PerformanceBaseline:
    """性能基线"""
    baseline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    created_at: float = field(default_factory=time.time)
    metrics: Dict[str, float] = field(default_factory=dict)
    conditions: Dict[str, Any] = field(default_factory=dict)


class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self):
        self.snapshots: List[PerformanceSnapshot] = []
        self.operations: List[Tuple[float, float, bool]] = []  # (start, end, success)
        self._lock = threading.Lock()
        self._operation_lock = threading.Lock()
    
    def record_operation(self, duration: float, success: bool = True):
        """记录操作"""
        with self._operation_lock:
            self.operations.append((time.time(), duration, success))
    
    @contextmanager
    def profile(self, operation_name: str = ""):
        """性能分析上下文管理器"""
        start = time.time()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration = time.time() - start
            self.record_operation(duration, success)
    
    def take_snapshot(self) -> PerformanceSnapshot:
        """获取性能快照"""
        snapshot = PerformanceSnapshot(
            timestamp=time.time(),
            operation_count=len(self.operations),
            error_count=sum(1 for _, _, s in self.operations if not s),
            total_duration=sum(d for _, d, _ in self.operations),
            avg_latency=0.0,
            min_latency=0.0,
            max_latency=0.0,
            p50_latency=0.0,
            p95_latency=0.0,
            p99_latency=0.0,
            cpu_usage=0.0,
            memory_usage=0.0,
            thread_count=threading.active_count(),
            gc_counts=gc.get_count()
        )
        
        # 计算延迟统计
        if self.operations:
            durations = sorted([d for _, d, _ in self.operations])
            n = len(durations)
            
            snapshot.avg_latency = sum(durations) / n
            snapshot.min_latency = durations[0]
            snapshot.max_latency = durations[-1]
            snapshot.p50_latency = durations[int(n * 0.5)]
            snapshot.p95_latency = durations[int(n * 0.95)] if n > 20 else durations[-1]
            snapshot.p99_latency = durations[int(n * 0.99)] if n > 100 else durations[-1]
        
        # 收集资源使用情况
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            snapshot.memory_usage = usage.ru_maxrss / 1024 / 1024  # MB
        except Exception:
            pass
        
        with self._lock:
            self.snapshots.append(snapshot)
        
        return snapshot
    
    def get_summary(self) -> Dict[str, float]:
        """获取性能摘要"""
        if not self.operations:
            return {}
        
        durations = [d for _, d, _ in self.operations]
        n = len(durations)
        
        total_time = time.time() - (self.operations[0][0] if self.operations else time.time())
        
        return {
            "operation_count": n,
            "success_count": sum(1 for _, _, s in self.operations if s),
            "error_count": sum(1 for _, _, s in self.operations if not s),
            "error_rate": sum(1 for _, _, s in self.operations if not s) / n * 100,
            "avg_latency": sum(durations) / n,
            "min_latency": min(durations),
            "max_latency": max(durations),
            "p50_latency": sorted(durations)[int(n * 0.5)],
            "p95_latency": sorted(durations)[int(n * 0.95)] if n > 20 else max(durations),
            "p99_latency": sorted(durations)[int(n * 0.99)] if n > 100 else max(durations),
            "throughput": n / total_time if total_time > 0 else 0
        }
    
    def reset(self):
        """重置分析器"""
        with self._lock:
            self.snapshots.clear()
        with self._operation_lock:
            self.operations.clear()


class StabilityTester:
    """稳定性测试器"""
    
    def __init__(self, name: str):
        self.name = name
        self.test_type: StabilityTestType = StabilityTestType.LONG_RUN
        self.duration: float = 3600.0  # 默认1小时
        self.operations_per_second: float = 10.0
        self.profiler = PerformanceProfiler()
        self._stop_event = threading.Event()
        self._test_thread: Optional[threading.Thread] = None
    
    def configure(
        self,
        test_type: StabilityTestType,
        duration: float = 3600.0,
        operations_per_second: float = 10.0
    ):
        """配置测试"""
        self.test_type = test_type
        self.duration = duration
        self.operations_per_second = operations_per_second
    
    def _monitor_loop(self, operation_func: Callable[[], bool]):
        """监控循环"""
        initial_memory = self._get_memory_usage()
        initial_threads = threading.active_count()
        snapshots = []
        
        start_time = time.time()
        last_snapshot = start_time
        
        while not self._stop_event.is_set() and (time.time() - start_time) < self.duration:
            try:
                # 执行操作
                with self.profiler.profile():
                    success = operation_func()
                
                # 定期保存快照
                current_time = time.time()
                if current_time - last_snapshot >= 60.0:  # 每分钟
                    snapshot = self.profiler.take_snapshot()
                    snapshots.append(snapshot)
                    last_snapshot = current_time
                
                # 控制操作频率
                time.sleep(1.0 / self.operations_per_second)
                
            except Exception as e:
                print(f"Stability test error: {e}")
        
        # 最终快照
        snapshot = self.profiler.take_snapshot()
        snapshots.append(snapshot)
        
        return snapshots, initial_memory, initial_threads
    
    def _get_memory_usage(self) -> float:
        """获取内存使用"""
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024
        except Exception:
            return 0.0
    
    def run(self, operation_func: Callable[[], bool]) -> StabilityReport:
        """运行稳定性测试"""
        report = StabilityReport(test_type=self.test_type)
        report.start_time = time.time()
        
        # 开始监控线程
        self._stop_event.clear()
        
        def monitor():
            snapshots, initial_memory, initial_threads = self._monitor_loop(operation_func)
            report.performance_snapshots = snapshots
            report.memory_growth = self._get_memory_usage() - initial_memory
            report.thread_growth = threading.active_count() - initial_threads
        
        self._test_thread = threading.Thread(target=monitor, daemon=True)
        self._test_thread.start()
        
        # 等待测试完成
        self._test_thread.join(timeout=self.duration + 10)
        
        report.end_time = time.time()
        report.duration = report.end_time - report.start_time
        
        # 生成报告
        summary = self.profiler.get_summary()
        
        report.total_operations = summary.get("operation_count", 0)
        report.successful_operations = summary.get("success_count", 0)
        report.failed_operations = summary.get("error_count", 0)
        report.error_rate = summary.get("error_rate", 0.0)
        report.average_latency = summary.get("avg_latency", 0.0)
        report.max_latency = summary.get("max_latency", 0.0)
        report.throughput = summary.get("throughput", 0.0)
        
        # 检查问题
        self._check_issues(report)
        
        return report
    
    def stop(self):
        """停止测试"""
        self._stop_event.set()
        if self._test_thread:
            self._test_thread.join(timeout=5.0)
    
    def _check_issues(self, report: StabilityReport):
        """检查问题"""
        # 检查错误率
        if report.error_rate > 5.0:
            report.issues.append(f"High error rate: {report.error_rate:.2f}%")
        
        # 检查内存增长
        if report.memory_growth > 100:  # MB
            report.warnings.append(f"Significant memory growth: {report.memory_growth:.2f}MB")
        
        # 检查线程增长
        if report.thread_growth > 5:
            report.warnings.append(f"Thread leak detected: +{report.thread_growth} threads")
        
        # 检查延迟增长趋势
        if len(report.performance_snapshots) >= 2:
            early = report.performance_snapshots[0]
            late = report.performance_snapshots[-1]
            
            if late.avg_latency > early.avg_latency * 2:
                report.warnings.append("Latency degradation detected")
            
            if late.memory_usage > early.memory_usage * 1.5:
                report.warnings.append("Memory usage increasing over time")
        
        # 确定通过状态
        report.passed = len(report.issues) == 0
        
        # 生成摘要
        report.summary = self._generate_summary(report)
    
    def _generate_summary(self, report: StabilityReport) -> str:
        """生成摘要"""
        lines = []
        lines.append(f"Stability Test: {self.name}")
        lines.append(f"Type: {self.test_type.value}")
        lines.append(f"Duration: {report.duration:.2f}s")
        lines.append(f"Operations: {report.total_operations}")
        lines.append(f"Success Rate: {(100 - report.error_rate):.2f}%")
        lines.append(f"Throughput: {report.throughput:.2f} ops/s")
        
        if report.warnings:
            lines.append(f"\nWarnings: {len(report.warnings)}")
            for warning in report.warnings:
                lines.append(f"  - {warning}")
        
        if report.issues:
            lines.append(f"\nIssues: {len(report.issues)}")
            for issue in report.issues:
                lines.append(f"  - {issue}")
        
        lines.append(f"\nStatus: {'PASSED' if report.passed else 'FAILED'}")
        
        return "\n".join(lines)


class PerformanceBenchmark:
    """性能基准测试"""
    
    def __init__(self):
        self.baselines: Dict[str, PerformanceBaseline] = {}
        self.results: List[Dict[str, float]] = []
        self._lock = threading.Lock()
    
    def create_baseline(
        self,
        name: str,
        description: str = "",
        conditions: Optional[Dict[str, Any]] = None
    ) -> PerformanceBaseline:
        """创建性能基线"""
        baseline = PerformanceBaseline(
            name=name,
            description=description,
            conditions=conditions or {}
        )
        with self._lock:
            self.baselines[name] = baseline
        return baseline
    
    def record_baseline_metrics(
        self,
        name: str,
        metrics: Dict[str, float]
    ):
        """记录基线指标"""
        with self._lock:
            if name in self.baselines:
                self.baselines[name].metrics = metrics
    
    def compare_with_baseline(
        self,
        name: str,
        current_metrics: Dict[str, float],
        thresholds: Optional[Dict[str, float]] = None
    ) -> Tuple[bool, List[str]]:
        """与基线比较"""
        if name not in self.baselines:
            return False, ["Baseline not found"]
        
        baseline = self.baselines[name]
        deviations = []
        passed = True
        
        thresholds = thresholds or {
            "avg_latency": 1.2,  # 允许20%的性能下降
            "p95_latency": 1.3,
            "throughput": 0.8,     # 允许20%的吞吐量下降
            "error_rate": 1.0      # 不允许错误率增加
        }
        
        for metric, current_value in current_metrics.items():
            if metric in baseline.metrics:
                baseline_value = baseline.metrics[metric]
                
                if baseline_value > 0:
                    ratio = current_value / baseline_value
                    
                    if metric in thresholds:
                        threshold = thresholds[metric]
                        
                        # 对于延迟和错误率，越大越差
                        if metric in ["avg_latency", "p95_latency", "error_rate"]:
                            if ratio > threshold:
                                deviations.append(
                                    f"{metric}: {current_value:.2f} vs baseline {baseline_value:.2f} "
                                    f"(+{(ratio-1)*100:.1f}%)"
                                )
                                passed = False
                        # 对于吞吐量，越大越好
                        else:
                            if ratio < threshold:
                                deviations.append(
                                    f"{metric}: {current_value:.2f} vs baseline {baseline_value:.2f} "
                                    f"({(ratio-1)*100:.1f}%)"
                                )
                                passed = False
        
        return passed, deviations
    
    def run_benchmark(
        self,
        name: str,
        operations: Dict[str, Callable],
        iterations: int = 100
    ) -> Dict[str, Dict[str, float]]:
        """运行基准测试"""
        results = {}
        
        for op_name, operation in operations.items():
            profiler = PerformanceProfiler()
            
            for _ in range(iterations):
                with profiler.profile():
                    try:
                        operation()
                    except Exception:
                        pass
            
            summary = profiler.get_summary()
            results[op_name] = summary
        
        with self._lock:
            self.results.append({
                "name": name,
                "timestamp": time.time(),
                "results": results
            })
        
        return results


def create_stability_test(
    name: str,
    test_type: StabilityTestType,
    duration: float = 3600.0,
    operations_per_second: float = 10.0
) -> StabilityTester:
    """创建稳定性测试"""
    tester = StabilityTester(name)
    tester.configure(test_type, duration, operations_per_second)
    return tester


def run_long_running_test(
    name: str,
    operation_func: Callable[[], bool],
    duration: float = 3600.0,
    operations_per_second: float = 10.0
) -> StabilityReport:
    """运行长运行测试"""
    tester = create_stability_test(
        name, StabilityTestType.LONG_RUN, duration, operations_per_second
    )
    return tester.run(operation_func)


def run_memory_leak_test(
    name: str,
    operation_func: Callable[[], bool],
    duration: float = 1800.0,
    operations_per_second: float = 10.0
) -> StabilityReport:
    """运行内存泄漏测试"""
    tester = create_stability_test(
        name, StabilityTestType.MEMORY_LEAK, duration, operations_per_second
    )
    return tester.run(operation_func)
