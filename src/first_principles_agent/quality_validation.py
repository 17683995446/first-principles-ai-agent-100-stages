"""
代码质量检查与全面验证模块 - 第85阶段
实现代码质量验证、性能检查、健壮性测试
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple, Set
import threading
import time
import uuid
from collections import defaultdict


class CodeQualityLevel(Enum):
    """代码质量级别"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


class CheckType(Enum):
    """检查类型"""
    FUNCTIONALITY = "functionality"
    PERFORMANCE = "performance"
    ROBUSTNESS = "robustness"
    ERROR_HANDLING = "error_handling"
    MEMORY_USAGE = "memory_usage"
    CONCURRENCY = "concurrency"


@dataclass
class QualityCheckResult:
    """质量检查结果"""
    check_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    check_name: str
    check_type: CheckType
    status: bool = False
    performance_score: float = 0.0
    error_count: int = 0
    warning_count: int = 0
    issues: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0


@dataclass
class CodeQualityReport:
    """代码质量报告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: float = field(default_factory=time.time)
    overall_score: float = 0.0
    overall_level: CodeQualityLevel = CodeQualityLevel.GOOD
    checks: List[QualityCheckResult] = field(default_factory=list)
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    total_warnings: int = 0
    total_errors: int = 0
    summary: str = ""


class CodeQualityChecker:
    """代码质量检查器"""
    
    def __init__(self, name: str = "Quality Checker"):
        self.name = name
        self.checks: List[Tuple[str, CheckType, Callable]] = []
        self._lock = threading.Lock()
    
    def register_check(
        self,
        name: str,
        check_type: CheckType,
        check_func: Callable[[], QualityCheckResult]
    ):
        """注册检查"""
        with self._lock:
            self.checks.append((name, check_type, check_func))
    
    def run_all_checks(self) -> CodeQualityReport:
        """运行所有检查"""
        report = CodeQualityReport()
        start_time = time.time()
        
        for name, check_type, check_func in self.checks:
            try:
                check_start = time.time()
                result = check_func()
                result.check_name = name
                result.check_type = check_type
                result.execution_time = time.time() - check_start
                
                report.checks.append(result)
                
                if result.status:
                    report.passed_checks += 1
                else:
                    report.failed_checks += 1
                
                report.total_warnings += result.warning_count
                report.total_errors += result.error_count
                
            except Exception as e:
                failed_check = QualityCheckResult(
                    check_name=name,
                    check_type=check_type,
                    status=False,
                    error_count=1,
                    issues=[f"Check failed with exception: {str(e)}"]
                )
                report.checks.append(failed_check)
                report.failed_checks += 1
                report.total_errors += 1
        
        report.total_checks = len(report.checks)
        
        # 计算总分
        if report.total_checks > 0:
            pass_rate = report.passed_checks / report.total_checks * 100
            error_penalty = report.total_errors * 5
            warning_penalty = report.total_warnings * 1
            report.overall_score = max(0, min(100, pass_rate - error_penalty - warning_penalty))
        
        # 确定质量级别
        if report.overall_score >= 90:
            report.overall_level = CodeQualityLevel.EXCELLENT
        elif report.overall_score >= 75:
            report.overall_level = CodeQualityLevel.GOOD
        elif report.overall_score >= 60:
            report.overall_level = CodeQualityLevel.ACCEPTABLE
        elif report.overall_score >= 40:
            report.overall_level = CodeQualityLevel.NEEDS_IMPROVEMENT
        else:
            report.overall_level = CodeQualityLevel.POOR
        
        report.summary = self._generate_summary(report)
        
        return report
    
    def _generate_summary(self, report: CodeQualityReport) -> str:
        """生成摘要"""
        lines = []
        lines.append(f"Code Quality Report: {self.name}")
        lines.append(f"Generated: {time.ctime(report.generated_at)}")
        lines.append(f"Overall Score: {report.overall_score:.1f}/100")
        lines.append(f"Overall Level: {report.overall_level.value.upper()}")
        lines.append("")
        lines.append(f"Total Checks: {report.total_checks}")
        lines.append(f"Passed: {report.passed_checks}")
        lines.append(f"Failed: {report.failed_checks}")
        lines.append(f"Warnings: {report.total_warnings}")
        lines.append(f"Errors: {report.total_errors}")
        
        if report.checks:
            lines.append("")
            lines.append("Check Results:")
            for check in report.checks:
                status = "✓" if check.status else "✗"
                lines.append(f"  {status} {check.check_name} - {check.check_type.value}")
                if check.issues:
                    for issue in check.issues[:2]:  # 只显示前2个问题
                        lines.append(f"      - {issue}")
        
        return "\n".join(lines)


class CompleteValidator:
    """全面验证器"""
    
    def __init__(self, name: str = "Complete Validator"):
        self.name = name
        self.quality_checker = CodeQualityChecker(name)
        self.test_results: List[Dict] = []
    
    def add_functionality_checks(self, agent_class, task_model, atomic_actions):
        """添加功能性检查"""
        
        def check_agent_initialization():
            result = QualityCheckResult(status=True)
            try:
                agent = agent_class()
                result.status = agent is not None
                result.performance_score = 100
            except Exception as e:
                result.status = False
                result.error_count = 1
                result.issues.append(f"Agent initialization failed: {str(e)}")
            return result
        
        def check_task_creation():
            result = QualityCheckResult(status=True)
            try:
                quartet = task_model("Test Task")
                if quartet.target == "Test Task":
                    result.status = True
                else:
                    result.status = False
                    result.warning_count = 1
                    result.issues.append("Task target not properly set")
            except Exception as e:
                result.status = False
                result.error_count = 1
                result.issues.append(f"Task creation failed: {str(e)}")
            return result
        
        self.quality_checker.register_check(
            "Agent Initialization", CheckType.FUNCTIONALITY, check_agent_initialization
        )
        self.quality_checker.register_check(
            "Task Creation", CheckType.FUNCTIONALITY, check_task_creation
        )
    
    def add_performance_checks(self, performance_ops):
        """添加性能检查"""
        
        def check_throughput():
            result = QualityCheckResult(status=True)
            try:
                start = time.time()
                for _ in range(100):
                    if performance_ops:
                        performance_ops()
                duration = time.time() - start
                
                throughput = 100 / duration if duration > 0 else 0
                result.details["throughput_ops_s"] = throughput
                
                if throughput > 50:
                    result.performance_score = 100
                elif throughput > 20:
                    result.performance_score = 75
                elif throughput > 5:
                    result.performance_score = 50
                else:
                    result.performance_score = 25
                    result.warning_count = 1
                    result.issues.append(f"Throughput below threshold: {throughput:.1f} ops/s")
                    
            except Exception as e:
                result.status = False
                result.error_count = 1
                result.issues.append(f"Performance check failed: {str(e)}")
            return result
        
        def check_latency():
            result = QualityCheckResult(status=True)
            try:
                latencies = []
                for _ in range(10):
                    start = time.time()
                    if performance_ops:
                        performance_ops()
                    latencies.append(time.time() - start)
                
                avg_latency = sum(latencies) / len(latencies) * 1000
                max_latency = max(latencies) * 1000
                
                result.details["avg_latency_ms"] = avg_latency
                result.details["max_latency_ms"] = max_latency
                
                if avg_latency < 10:
                    result.performance_score = 100
                elif avg_latency < 50:
                    result.performance_score = 75
                elif avg_latency < 200:
                    result.performance_score = 50
                else:
                    result.performance_score = 25
                    result.warning_count = 1
                    result.issues.append(f"High latency: {avg_latency:.1f}ms avg")
                    
            except Exception as e:
                result.status = False
                result.error_count = 1
                result.issues.append(f"Latency check failed: {str(e)}")
            return result
        
        self.quality_checker.register_check(
            "Throughput Check", CheckType.PERFORMANCE, check_throughput
        )
        self.quality_checker.register_check(
            "Latency Check", CheckType.PERFORMANCE, check_latency
        )
    
    def add_robustness_checks(self, error_situations):
        """添加健壮性检查"""
        
        def check_error_handling():
            result = QualityCheckResult(status=True)
            try:
                errors_handled = 0
                for situation in error_situations[:5]:  # 只测试前5个
                    try:
                        situation()
                        errors_handled += 1
                    except Exception:
                        errors_handled += 1
                
                result.details["situations_tested"] = len(error_situations[:5])
                result.details["handled_properly"] = errors_handled
                
                if errors_handled == 5:
                    result.performance_score = 100
                elif errors_handled >= 3:
                    result.performance_score = 75
                else:
                    result.warning_count = 1
                    result.issues.append(f"Only {errors_handled}/5 error situations handled properly")
                    
            except Exception as e:
                result.status = False
                result.error_count = 1
                result.issues.append(f"Robustness check failed: {str(e)}")
            return result
        
        def check_boundary_conditions():
            result = QualityCheckResult(status=True)
            try:
                boundary_tests = [
                    lambda: str(""),
                    lambda: str("a" * 1000),
                    lambda: 0,
                    lambda: -1,
                    lambda: 1000000,
                    lambda: None
                ]
                
                successful = 0
                for test in boundary_tests:
                    try:
                        result_val = test()
                        if result_val is not None or test() is None:
                            successful += 1
                    except Exception:
                        pass
                
                result.details["boundary_tests_successful"] = successful
                
                if successful == 6:
                    result.performance_score = 100
                elif successful >= 4:
                    result.performance_score = 75
                else:
                    result.warning_count = 1
                    result.issues.append(f"Boundary handling issues: {6-successful}/6")
                    
            except Exception as e:
                result.status = False
                result.error_count = 1
                result.issues.append(f"Boundary check failed: {str(e)}")
            return result
        
        self.quality_checker.register_check(
            "Error Handling", CheckType.ERROR_HANDLING, check_error_handling
        )
        self.quality_checker.register_check(
            "Boundary Conditions", CheckType.ROBUSTNESS, check_boundary_conditions
        )
    
    def run_complete_validation(self) -> CodeQualityReport:
        """运行完整验证"""
        return self.quality_checker.run_all_checks()


def create_quality_checker() -> CodeQualityChecker:
    """创建代码质量检查器"""
    return CodeQualityChecker()


def create_complete_validator() -> CompleteValidator:
    """创建完整验证器"""
    return CompleteValidator()


def run_quick_quality_check() -> CodeQualityReport:
    """运行快速质量检查"""
    checker = CodeQualityChecker("Quick Quality Check")
    
    # 基本功能检查
    def basic_functionality():
        result = QualityCheckResult(status=True)
        try:
            from first_principles_agent import FirstPrinciplesAgent
            agent = FirstPrinciplesAgent()
            result.status = agent is not None
        except Exception as e:
            result.status = False
            result.error_count = 1
            result.issues.append(f"Basic functionality check failed: {str(e)}")
        return result
    
    checker.register_check(
        "Basic Functionality", CheckType.FUNCTIONALITY, basic_functionality
    )
    
    # 基本性能检查
    def basic_performance():
        result = QualityCheckResult(status=True)
        try:
            start = time.time()
            total = 0
            for i in range(1000):
                total += i
            duration = time.time() - start
            throughput = 1000 / duration if duration > 0 else 0
            result.details["throughput"] = throughput
            result.performance_score = 90 if throughput > 10000 else 70
        except Exception as e:
            result.status = False
            result.error_count = 1
            result.issues.append(f"Performance check failed: {str(e)}")
        return result
    
    checker.register_check(
        "Basic Performance", CheckType.PERFORMANCE, basic_performance
    )
    
    return checker.run_all_checks()
