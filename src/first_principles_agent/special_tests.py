"""
专项测试框架 - Special Test Framework
第81-95阶段：专项测试缺陷闭环
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple, Set
import threading
import time
import uuid
import sys
from datetime import datetime


class TestPhase(Enum):
    """测试阶段"""
    PREPARE = "prepare"
    EXECUTE = "execute"
    VERIFY = "verify"
    CLEANUP = "cleanup"


class TestStatus(Enum):
    """测试状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class TestCategory(Enum):
    """测试分类"""
    STRESS = "stress"          # 压力测试
    LOAD = "load"              # 负载测试
    PERFORMANCE = "performance" # 性能测试
    FAULT_INJECTION = "fault_injection" # 故障注入
    CONCURRENT = "concurrent"  # 并发测试
    BOUNDARY = "boundary"      # 边界测试
    INTEGRATION = "integration" # 集成测试


@dataclass
class TestMetrics:
    """测试指标"""
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    operations_total: int = 0
    operations_success: int = 0
    operations_failed: int = 0
    errors: List[str] = field(default_factory=list)
    throughput: float = 0.0  # 每秒操作数
    avg_latency: float = 0.0 # 平均延迟
    p50_latency: float = 0.0 # p50延迟
    p95_latency: float = 0.0 # p95延迟
    p99_latency: float = 0.0 # p99延迟
    max_latency: float = 0.0 # 最大延迟
    min_latency: float = 0.0 # 最小延迟
    cpu_usage: float = 0.0 # CPU使用率
    memory_usage: float = 0.0 # 内存使用率
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def calculate(self):
        """计算指标"""
        self.duration = self.end_time - self.start_time
        if self.duration > 0:
            self.throughput = self.operations_success / self.duration


@dataclass
class TestCaseResult:
    """测试用例结果"""
    test_id: str
    test_name: str
    category: TestCategory
    status: TestStatus
    metrics: TestMetrics = field(default_factory=TestMetrics)
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Defect:
    """缺陷记录"""
    defect_id: str
    test_id: str
    test_name: str
    category: TestCategory
    description: str
    severity: str = "medium"  # low, medium, high, critical
    reproduction_steps: List[str] = field(default_factory=list)
    expected_behavior: str = ""
    actual_behavior: str = ""
    status: str = "open"  # open, investigating, fixed, verified, closed
    created_at: float = field(default_factory=time.time)
    closed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TestCase:
    """测试用例基类"""
    
    def __init__(self, name: str, category: TestCategory):
        self.test_id = str(uuid.uuid4())
        self.name = name
        self.category = category
        self.metrics = TestMetrics()
        self._phase = TestPhase.PREPARE
    
    def setup(self):
        """测试准备"""
        pass
    
    def execute(self):
        """执行测试 - 需子类实现"""
        raise NotImplementedError("execute method must be implemented")
    
    def verify(self):
        """测试验证"""
        return True
    
    def teardown(self):
        """测试清理"""
        pass
    
    def run(self) -> TestCaseResult:
        """运行测试用例"""
        result = TestCaseResult(
            test_id=self.test_id,
            test_name=self.name,
            category=self.category,
            status=TestStatus.RUNNING
        )
        result.start_time = time.time()
        self.metrics.start_time = result.start_time
        
        try:
            self._phase = TestPhase.PREPARE
            self.setup()
            
            self._phase = TestPhase.EXECUTE
            self.execute()
            
            self._phase = TestPhase.VERIFY
            passed = self.verify()
            
            self._phase = TestPhase.CLEANUP
            self.teardown()
            
            if passed:
                result.status = TestStatus.PASSED
            else:
                result.status = TestStatus.FAILED
                
        except TimeoutError as e:
            result.status = TestStatus.TIMEOUT
            result.error_message = str(e)
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            import traceback
            result.stack_trace = traceback.format_exc()
        finally:
            result.end_time = time.time()
            result.duration = result.end_time - result.start_time
            self.metrics.end_time = result.end_time
            self.metrics.calculate()
            result.metrics = self.metrics
        
        return result


class StressTestCase(TestCase):
    """压力测试用例基类"""
    
    def __init__(self, name: str, duration: float = 60.0, concurrency: int = 10):
        super().__init__(name, TestCategory.STRESS)
        self.duration = duration
        self.concurrency = concurrency
        self._stop_event = threading.Event()
        self._latencies = []
        self._latency_lock = threading.Lock()
    
    def operation(self, index: int) -> bool:
        """执行单个操作 - 需子类实现"""
        raise NotImplementedError("operation method must be implemented")
    
    def _worker(self, worker_id: int):
        """工作线程"""
        start_time = time.time()
        while not self._stop_event.is_set() and (time.time() - start_time) < self.duration:
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
    
    def execute(self):
        """执行压力测试"""
        threads = []
        self._stop_event.clear()
        self._latencies = []
        
        for i in range(self.concurrency):
            t = threading.Thread(target=self._worker, args=(i,), daemon=True)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=self.duration + 5)
        
        self._calculate_latency_metrics()
    
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


class TestSuite:
    """测试套件"""
    
    def __init__(self, name: str):
        self.suite_id = str(uuid.uuid4())
        self.name = name
        self.test_cases: List[TestCase] = []
        self.results: List[TestCaseResult] = []
        self.defects: List[Defect] = []
        self._lock = threading.Lock()
    
    def add_test(self, test_case: TestCase):
        """添加测试用例"""
        with self._lock:
            self.test_cases.append(test_case)
    
    def add_tests(self, test_cases: List[TestCase]):
        """批量添加测试用例"""
        for test in test_cases:
            self.add_test(test)
    
    def run_all(self) -> List[TestCaseResult]:
        """运行所有测试"""
        self.results = []
        
        for test in self.test_cases:
            result = test.run()
            self.results.append(result)
            
            if result.status in (TestStatus.FAILED, TestStatus.ERROR, TestStatus.TIMEOUT):
                self._record_defect(result)
        
        return self.results
    
    def run_by_category(self, category: TestCategory) -> List[TestCaseResult]:
        """按分类运行测试"""
        results = []
        for test in self.test_cases:
            if test.category == category:
                result = test.run()
                results.append(result)
                if result.status in (TestStatus.FAILED, TestStatus.ERROR, TestStatus.TIMEOUT):
                    self._record_defect(result)
        return results
    
    def _record_defect(self, result: TestCaseResult):
        """记录缺陷"""
        defect = Defect(
            defect_id=str(uuid.uuid4()),
            test_id=result.test_id,
            test_name=result.test_name,
            category=result.category,
            description=result.error_message or "Test failed",
            severity="high" if result.status == TestStatus.ERROR else "medium"
        )
        self.defects.append(defect)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        summary = {
            "total": len(self.results),
            "passed": 0,
            "failed": 0,
            "error": 0,
            "timeout": 0,
            "defects": len(self.defects),
            "categories": {}
        }
        
        for result in self.results:
            summary[result.status.value] = summary.get(result.status.value, 0) + 1
            
            cat = result.category.value
            if cat not in summary["categories"]:
                summary["categories"][cat] = {"total": 0, "passed": 0}
            summary["categories"][cat]["total"] += 1
            if result.status == TestStatus.PASSED:
                summary["categories"][cat]["passed"] += 1
        
        return summary


class SpecialTestManager:
    """专项测试管理器"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self.test_suites: Dict[str, TestSuite] = {}
        self.defects: List[Defect] = []
        self.global_metrics: Dict[str, Any] = {}
    
    def create_suite(self, name: str) -> TestSuite:
        """创建测试套件"""
        with self._lock:
            suite = TestSuite(name)
            self.test_suites[suite.suite_id] = suite
            return suite
    
    def get_suite(self, suite_id: str) -> Optional[TestSuite]:
        """获取测试套件"""
        return self.test_suites.get(suite_id)
    
    def record_defect(self, defect: Defect):
        """记录缺陷"""
        with self._lock:
            self.defects.append(defect)
    
    def get_defects(self, status: Optional[str] = None, 
                  category: Optional[TestCategory] = None,
                  severity: Optional[str] = None) -> List[Defect]:
        """获取缺陷列表"""
        with self._lock:
            defects = self.defects
            
            if status:
                defects = [d for d in defects if d.status == status]
            if category:
                defects = [d for d in defects if d.category == category]
            if severity:
                defects = [d for d in defects if d.severity == severity]
            
            return defects
    
    def update_defect_status(self, defect_id: str, new_status: str):
        """更新缺陷状态"""
        with self._lock:
            for defect in self.defects:
                if defect.defect_id == defect_id:
                    defect.status = new_status
                    if new_status in ("fixed", "verified", "closed"):
                        defect.closed_at = time.time()
    
    def get_all_summaries(self) -> Dict[str, Any]:
        """获取所有测试摘要"""
        with self._lock:
            summaries = {}
            for suite_id, suite in self.test_suites.items():
                summaries[suite_id] = suite.get_summary()
            return summaries


def create_stress_test(name: str, duration: float, concurrency: int, 
                     operation_func: Callable[[int], bool]) -> StressTestCase:
    """创建压力测试用例
    
    Args:
        name: 测试名称
        duration: 测试持续时间（秒）
        concurrency: 并发数
        operation_func: 操作函数，接收index参数返回是否成功
    
    Returns:
        StressTestCase 实例
    """
    class CustomStressTest(StressTestCase):
        def __init__(self):
            super().__init__(name, duration, concurrency)
        
        def operation(self, index: int) -> bool:
            return operation_func(index)
    
    return CustomStressTest()


def run_stress_suite(test_name: str, test_cases: List[StressTestCase]) -> TestSuite:
    """运行压力测试套件
    
    Args:
        test_name: 测试套件名称
        test_cases: 测试用例列表
    
    Returns:
        测试套件实例
    """
    manager = SpecialTestManager()
    suite = manager.create_suite(test_name)
    suite.add_tests(test_cases)
    suite.run_all()
    return suite
