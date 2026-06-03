"""
集成测试与缺陷排查模块 - 第83阶段
实现模块间集成测试、缺陷检测和系统稳定性验证
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple, Set
import threading
import time
import traceback
import uuid
from collections import defaultdict

from first_principles_agent.special_tests import (
    TestPhase, TestStatus, TestCategory,
    TestMetrics, TestCaseResult, Defect,
    TestCase, TestSuite, SpecialTestManager
)


class IntegrationLevel(Enum):
    """集成级别"""
    UNIT = "unit"           # 单元测试级别
    MODULE = "module"       # 模块内部集成
    MODULES = "modules"     # 模块间集成
    SYSTEM = "system"       # 系统级集成
    E2E = "e2e"             # 端到端测试


class DefectSeverity(Enum):
    """缺陷严重程度"""
    INFO = "info"           # 信息级
    LOW = "low"             # 低严重性
    MEDIUM = "medium"       # 中等严重性
    HIGH = "high"           # 高严重性
    CRITICAL = "critical"   # 严重/致命


class DefectType(Enum):
    """缺陷类型"""
    FUNCTIONAL = "functional"       # 功能性缺陷
    PERFORMANCE = "performance"     # 性能问题
    MEMORY_LEAK = "memory_leak"    # 内存泄漏
    RACE_CONDITION = "race_condition"  # 竞态条件
    DEADLOCK = "deadlock"           # 死锁
    RESOURCE_LEAK = "resource_leak"  # 资源泄漏
    TIMEOUT = "timeout"             # 超时问题
    INCONSISTENCY = "inconsistency"  # 数据不一致
    UNEXPECTED_BEHAVIOR = "unexpected_behavior"  # 意外行为


@dataclass
class IntegrationTestCase:
    """集成测试用例"""
    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    level: IntegrationLevel = IntegrationLevel.MODULES
    modules_involved: List[str] = field(default_factory=list)
    test_function: Optional[Callable] = None
    setup_function: Optional[Callable] = None
    teardown_function: Optional[Callable] = None
    timeout: float = 60.0
    retries: int = 1


@dataclass
class DefectReport:
    """缺陷报告"""
    defect_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    severity: DefectSeverity
    defect_type: DefectType
    modules: List[str] = field(default_factory=list)
    test_case_id: Optional[str] = None
    reproduction_steps: List[str] = field(default_factory=list)
    expected_behavior: str = ""
    actual_behavior: str = ""
    stack_trace: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    status: str = "open"  # open, investigating, fixed, verified, closed
    fixed_at: Optional[float] = None
    verified_at: Optional[float] = None
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealthMetrics:
    """系统健康指标"""
    timestamp: float = field(default_factory=time.time)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_threads: int = 0
    operation_count: int = 0
    error_count: int = 0
    average_latency: float = 0.0
    max_latency: float = 0.0
    success_rate: float = 100.0
    issues: List[str] = field(default_factory=list)


class IntegrationTestRunner:
    """集成测试运行器"""
    
    def __init__(self, name: str):
        self.name = name
        self.test_cases: List[IntegrationTestCase] = []
        self.results: List[TestCaseResult] = []
        self.defects: List[DefectReport] = []
        self.health_metrics: List[SystemHealthMetrics] = []
        self._lock = threading.Lock()
    
    def add_test(self, test_case: IntegrationTestCase):
        """添加集成测试用例"""
        with self._lock:
            self.test_cases.append(test_case)
    
    def add_tests(self, test_cases: List[IntegrationTestCase]):
        """批量添加集成测试用例"""
        for test in test_cases:
            self.add_test(test)
    
    def _run_single_test(self, test_case: IntegrationTestCase) -> TestCaseResult:
        """运行单个集成测试"""
        result = TestCaseResult(
            test_id=test_case.test_id,
            test_name=test_case.name,
            category=TestCategory.INTEGRATION,
            status=TestStatus.RUNNING
        )
        result.start_time = time.time()
        
        attempt = 0
        last_error = None
        
        while attempt <= test_case.retries:
            try:
                # Setup
                if test_case.setup_function:
                    test_case.setup_function()
                
                # Execute
                start = time.time()
                if test_case.timeout > 0:
                    # 带超时的执行
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(test_case.test_function)
                        try:
                            future.result(timeout=test_case.timeout)
                        except concurrent.futures.TimeoutError:
                            raise TimeoutError(f"Test timed out after {test_case.timeout}s")
                else:
                    test_case.test_function()
                
                # Teardown
                if test_case.teardown_function:
                    test_case.teardown_function()
                
                result.status = TestStatus.PASSED
                result.end_time = time.time()
                result.duration = result.end_time - result.start_time
                return result
                
            except TimeoutError as e:
                last_error = str(e)
                result.status = TestStatus.TIMEOUT
                self._record_defect(
                    title=f"Timeout in {test_case.name}",
                    description=f"Test timed out after {test_case.timeout}s",
                    severity=DefectSeverity.HIGH,
                    defect_type=DefectType.TIMEOUT,
                    modules=test_case.modules_involved,
                    test_case_id=test_case.test_id,
                    stack_trace=traceback.format_exc()
                )
                
            except Exception as e:
                last_error = str(e)
                attempt += 1
                
                if attempt > test_case.retries:
                    result.status = TestStatus.FAILED
                    result.error_message = last_error
                    result.stack_trace = traceback.format_exc()
                    
                    # 根据错误类型判断缺陷严重性
                    severity = self._determine_severity(e)
                    defect_type = self._determine_defect_type(e)
                    
                    self._record_defect(
                        title=f"Failure in {test_case.name}: {type(e).__name__}",
                        description=last_error,
                        severity=severity,
                        defect_type=defect_type,
                        modules=test_case.modules_involved,
                        test_case_id=test_case.test_id,
                        stack_trace=traceback.format_exc()
                    )
                else:
                    time.sleep(0.5)  # 重试前等待
        
        result.end_time = time.time()
        result.duration = result.end_time - result.start_time
        return result
    
    def _determine_severity(self, error: Exception) -> DefectSeverity:
        """确定缺陷严重性"""
        error_msg = str(error).lower()
        
        if "memory" in error_msg or "memoryerror" in error_msg:
            return DefectSeverity.CRITICAL
        elif "deadlock" in error_msg:
            return DefectSeverity.CRITICAL
        elif "timeout" in error_msg:
            return DefectSeverity.HIGH
        elif "permission" in error_msg or "access denied" in error_msg:
            return DefectSeverity.HIGH
        elif "null" in error_msg or "none" in error_msg:
            return DefectSeverity.MEDIUM
        else:
            return DefectSeverity.MEDIUM
    
    def _determine_defect_type(self, error: Exception) -> DefectType:
        """确定缺陷类型"""
        error_msg = str(error).lower()
        error_type = type(error).__name__
        
        if "timeout" in error_msg or error_type == "TimeoutError":
            return DefectType.TIMEOUT
        elif "memory" in error_msg:
            return DefectType.MEMORY_LEAK
        elif "deadlock" in error_msg or "dead lock" in error_msg:
            return DefectType.DEADLOCK
        elif "race" in error_msg:
            return DefectType.RACE_CONDITION
        elif "connection" in error_msg or "resource" in error_msg:
            return DefectType.RESOURCE_LEAK
        elif "performance" in error_msg or "slow" in error_msg:
            return DefectType.PERFORMANCE
        else:
            return DefectType.FUNCTIONAL
    
    def _record_defect(self, **kwargs):
        """记录缺陷"""
        defect = DefectReport(**kwargs)
        with self._lock:
            self.defects.append(defect)
    
    def run_all(self, level: Optional[IntegrationLevel] = None) -> List[TestCaseResult]:
        """运行所有集成测试"""
        self.results = []
        
        for test_case in self.test_cases:
            if level is None or test_case.level == level:
                result = self._run_single_test(test_case)
                self.results.append(result)
        
        return self.results
    
    def run_by_module(self, module: str) -> List[TestCaseResult]:
        """运行涉及特定模块的测试"""
        results = []
        for test_case in self.test_cases:
            if module in test_case.modules_involved:
                result = self._run_single_test(test_case)
                results.append(result)
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        summary = {
            "total": len(self.results),
            "passed": 0,
            "failed": 0,
            "error": 0,
            "timeout": 0,
            "by_level": {},
            "by_module": defaultdict(int),
            "defects": {
                "total": len(self.defects),
                "by_severity": defaultdict(int),
                "by_type": defaultdict(int),
                "open": 0,
                "fixed": 0,
                "closed": 0
            }
        }
        
        for result in self.results:
            if result.status == TestStatus.PASSED:
                summary["passed"] += 1
            elif result.status == TestStatus.FAILED:
                summary["failed"] += 1
            elif result.status == TestStatus.ERROR:
                summary["error"] += 1
            elif result.status == TestStatus.TIMEOUT:
                summary["timeout"] += 1
            
            # 按级别统计
            for test in self.test_cases:
                if test.test_id == result.test_id:
                    level = test.level.value
                    if level not in summary["by_level"]:
                        summary["by_level"][level] = {"total": 0, "passed": 0}
                    summary["by_level"][level]["total"] += 1
                    if result.status == TestStatus.PASSED:
                        summary["by_level"][level]["passed"] += 1
                    
                    # 按模块统计
                    for mod in test.modules_involved:
                        summary["by_module"][mod] += 1
        
        # 缺陷统计
        for defect in self.defects:
            summary["defects"]["by_severity"][defect.severity.value] += 1
            summary["defects"]["by_type"][defect.defect_type.value] += 1
            
            if defect.status == "open":
                summary["defects"]["open"] += 1
            elif defect.status in ("fixed", "verified"):
                summary["defects"]["fixed"] += 1
            elif defect.status == "closed":
                summary["defects"]["closed"] += 1
        
        return summary
    
    def generate_defect_report(self) -> str:
        """生成缺陷报告"""
        lines = []
        lines.append("="*70)
        lines.append("DEFECT REPORT")
        lines.append("="*70)
        lines.append(f"\nTotal Defects: {len(self.defects)}")
        
        if not self.defects:
            lines.append("\nNo defects found!")
            return "\n".join(lines)
        
        # 按严重性分组
        by_severity = defaultdict(list)
        for defect in self.defects:
            by_severity[defect.severity].append(defect)
        
        for severity in [DefectSeverity.CRITICAL, DefectSeverity.HIGH, 
                        DefectSeverity.MEDIUM, DefectSeverity.LOW, DefectSeverity.INFO]:
            defects = by_severity.get(severity, [])
            if not defects:
                continue
            
            lines.append(f"\n{'='*70}")
            lines.append(f"[{severity.value.upper()}] {len(defects)} defect(s)")
            lines.append('='*70)
            
            for i, defect in enumerate(defects, 1):
                lines.append(f"\n--- Defect #{i}: {defect.title} ---")
                lines.append(f"Type: {defect.defect_type.value}")
                lines.append(f"Modules: {', '.join(defect.modules)}")
                lines.append(f"Status: {defect.status}")
                lines.append(f"Created: {time.ctime(defect.created_at)}")
                lines.append(f"\nDescription:")
                lines.append(f"  {defect.description}")
                
                if defect.expected_behavior:
                    lines.append(f"\nExpected:")
                    lines.append(f"  {defect.expected_behavior}")
                
                if defect.actual_behavior:
                    lines.append(f"\nActual:")
                    lines.append(f"  {defect.actual_behavior}")
                
                if defect.stack_trace:
                    lines.append(f"\nStack Trace:")
                    for line in defect.stack_trace.split('\n'):
                        if line.strip():
                            lines.append(f"  {line}")
                
                if defect.notes:
                    lines.append(f"\nNotes:")
                    for note in defect.notes:
                        lines.append(f"  - {note}")
        
        lines.append("\n" + "="*70)
        lines.append("END OF REPORT")
        lines.append("="*70)
        
        return "\n".join(lines)


class SystemHealthMonitor:
    """系统健康监控器"""
    
    def __init__(self):
        self.metrics: List[SystemHealthMetrics] = []
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def record_metric(self, metric: SystemHealthMetrics):
        """记录健康指标"""
        with self._lock:
            self.metrics.append(metric)
            if len(self.metrics) > 1000:  # 保留最近1000条
                self.metrics = self.metrics[-1000:]
    
    def start_monitoring(self, interval: float = 5.0):
        """开始监控"""
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
    
    def _monitor_loop(self, interval: float):
        """监控循环"""
        while self._monitoring:
            try:
                metric = self._collect_metrics()
                self.record_metric(metric)
                
                # 检查问题
                if metric.issues:
                    print(f"Health issues detected: {metric.issues}")
                
                time.sleep(interval)
            except Exception as e:
                print(f"Health monitoring error: {e}")
    
    def _collect_metrics(self) -> SystemHealthMetrics:
        """收集当前指标"""
        metric = SystemHealthMetrics()
        
        try:
            import psutil
            process = psutil.Process()
            metric.cpu_usage = process.cpu_percent(interval=0.1)
            metric.memory_usage = process.memory_percent()
            metric.active_threads = process.num_threads()
        except ImportError:
            # psutil 不可用，使用基础信息
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            metric.memory_usage = usage.ru_maxrss / 1024 / 1024  # MB
            metric.active_threads = threading.active_count()
        except Exception:
            pass
        
        return metric
    
    def get_latest_metrics(self) -> Optional[SystemHealthMetrics]:
        """获取最新指标"""
        with self._lock:
            return self.metrics[-1] if self.metrics else None
    
    def get_average_metrics(self, window: int = 60) -> SystemHealthMetrics:
        """获取平均指标（最近window秒）"""
        with self._lock:
            cutoff = time.time() - window
            recent = [m for m in self.metrics if m.timestamp >= cutoff]
            
            if not recent:
                return SystemHealthMetrics()
            
            avg = SystemHealthMetrics()
            avg.cpu_usage = sum(m.cpu_usage for m in recent) / len(recent)
            avg.memory_usage = sum(m.memory_usage for m in recent) / len(recent)
            avg.active_threads = sum(m.active_threads for m in recent) / len(recent)
            avg.operation_count = recent[-1].operation_count - recent[0].operation_count
            avg.error_count = recent[-1].error_count - recent[0].error_count
            
            if avg.operation_count > 0:
                avg.success_rate = (avg.operation_count - avg.error_count) / avg.operation_count * 100
            
            return avg


def create_integration_test(
    name: str,
    test_function: Callable,
    modules: List[str],
    level: IntegrationLevel = IntegrationLevel.MODULES,
    description: str = "",
    setup: Optional[Callable] = None,
    teardown: Optional[Callable] = None,
    timeout: float = 60.0
) -> IntegrationTestCase:
    """创建集成测试用例"""
    return IntegrationTestCase(
        name=name,
        description=description,
        level=level,
        modules_involved=modules,
        test_function=test_function,
        setup_function=setup,
        teardown_function=teardown,
        timeout=timeout
    )
