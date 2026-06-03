"""
第72阶段：大规模并发测试
提供并发测试框架、压力测试工具和性能基准
"""

import time
import threading
import concurrent.futures
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict
from enum import Enum
import queue
import statistics


class ConcurrencyTestStatus(Enum):
    """并发测试状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ConcurrencyTestResult:
    """并发测试结果"""
    test_name: str
    status: ConcurrencyTestStatus
    start_time: float
    end_time: float
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_tps: float
    errors: List[str] = field(default_factory=list)
    additional_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskExecutionRecord:
    """单个任务执行记录"""
    task_id: str
    start_time: float
    end_time: float
    success: bool
    error: Optional[str] = None
    thread_id: Optional[int] = None


class ConcurrentTestSuite:
    """并发测试套件"""

    def __init__(self, name: str = "ConcurrentTestSuite"):
        self.name = name
        self.results: List[ConcurrencyTestResult] = []
        self._lock = threading.Lock()

    def run_concurrent_test(
        self,
        test_name: str,
        task_func: Callable[[int], Any],
        num_tasks: int,
        num_workers: int = 10,
        warmup_tasks: int = 0,
        delay_between_tasks: float = 0.0
    ) -> ConcurrencyTestResult:
        """
        运行并发测试

        参数:
            test_name: 测试名称
            task_func: 任务函数，接受任务索引返回结果
            num_tasks: 总任务数
            num_workers: 并发工作线程数
            warmup_tasks: 预热任务数
            delay_between_tasks: 任务间延迟
        """
        print(f"🚀 开始并发测试: {test_name}")
        print(f"   任务数: {num_tasks}, 工作线程: {num_workers}")

        start_time = time.time()
        records: List[TaskExecutionRecord] = []
        errors: List[str] = []
        completed = 0
        failed = 0

        # 预热阶段
        if warmup_tasks > 0:
            print(f"   预热阶段: {warmup_tasks} 个任务...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(task_func, i) for i in range(warmup_tasks)]
                concurrent.futures.wait(futures)
            print(f"   预热完成")

        # 正式测试
        print(f"   正式测试阶段...")
        test_start = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {}
            for i in range(num_tasks):
                future = executor.submit(
                    self._execute_task,
                    task_func,
                    i,
                    records
                )
                futures[future] = i
                if delay_between_tasks > 0:
                    time.sleep(delay_between_tasks)

            # 收集结果
            for future in concurrent.futures.as_completed(futures):
                task_idx = futures[future]
                try:
                    future.result()
                    completed += 1
                except Exception as e:
                    failed += 1
                    errors.append(f"任务 {task_idx} 失败: {str(e)}")

        test_end = time.time()

        # 计算统计信息
        latencies = [
            (r.end_time - r.start_time) * 1000
            for r in records
            if r.success
        ]

        avg_latency = statistics.mean(latencies) if latencies else 0
        p50 = _percentile(latencies, 50) if latencies else 0
        p95 = _percentile(latencies, 95) if latencies else 0
        p99 = _percentile(latencies, 99) if latencies else 0

        total_time = test_end - test_start
        throughput = num_tasks / total_time if total_time > 0 else 0

        result = ConcurrencyTestResult(
            test_name=test_name,
            status=ConcurrencyTestStatus.COMPLETED if failed == 0 else ConcurrencyTestStatus.FAILED,
            start_time=start_time,
            end_time=test_end,
            total_tasks=num_tasks,
            completed_tasks=completed,
            failed_tasks=failed,
            avg_latency_ms=avg_latency,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            throughput_tps=throughput,
            errors=errors[:50]  # 只保留前50个错误
        )

        with self._lock:
            self.results.append(result)

        # 打印结果摘要
        print(f"✅ 测试完成: {test_name}")
        print(f"   总耗时: {(test_end - test_start):.2f}s")
        print(f"   完成/失败: {completed}/{failed}")
        print(f"   平均延迟: {avg_latency:.2f}ms")
        print(f"   P50/P95/P99: {p50:.2f}/{p95:.2f}/{p99:.2f}ms")
        print(f"   吞吐量: {throughput:.2f} TPS")

        return result

    def _execute_task(
        self,
        task_func: Callable[[int], Any],
        task_idx: int,
        records: List[TaskExecutionRecord]
    ) -> Any:
        """执行单个任务并记录"""
        record = TaskExecutionRecord(
            task_id=str(task_idx),
            start_time=time.time(),
            end_time=0.0,
            success=False,
            thread_id=threading.get_ident()
        )

        try:
            result = task_func(task_idx)
            record.success = True
            return result
        except Exception as e:
            record.error = str(e)
            raise
        finally:
            record.end_time = time.time()
            records.append(record)

    def get_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        with self._lock:
            if not self.results:
                return {}

            total_tasks = sum(r.total_tasks for r in self.results)
            total_completed = sum(r.completed_tasks for r in self.results)
            total_failed = sum(r.failed_tasks for r in self.results)
            avg_throughput = statistics.mean(
                r.throughput_tps for r in self.results
            ) if self.results else 0

            return {
                "num_tests": len(self.results),
                "total_tasks": total_tasks,
                "total_completed": total_completed,
                "total_failed": total_failed,
                "avg_throughput_tps": avg_throughput,
                "tests": [
                    {
                        "name": r.test_name,
                        "throughput": r.throughput_tps,
                        "p95_latency": r.p95_latency_ms
                    }
                    for r in self.results
                ]
            }


class StressTester:
    """压力测试器"""

    def __init__(self):
        self.stopped = False

    def run_stress_test(
        self,
        name: str,
        task_func: Callable[[int], Any],
        initial_workers: int = 10,
        max_workers: int = 100,
        step_workers: int = 10,
        duration_per_step: float = 10.0,
        success_rate_threshold: float = 0.95
    ) -> List[ConcurrencyTestResult]:
        """
        运行阶梯式压力测试

        参数:
            name: 测试名称
            task_func: 任务函数
            initial_workers: 初始并发数
            max_workers: 最大并发数
            step_workers: 每步增加的并发数
            duration_per_step: 每步持续时间
            success_rate_threshold: 成功率阈值
        """
        results = []
        suite = ConcurrentTestSuite(f"{name}_stress")

        print(f"\n🔥 开始压力测试: {name}")
        print(f"   并发数: {initial_workers} -> {max_workers} (步长 {step_workers})")

        current_workers = initial_workers
        while current_workers <= max_workers and not self.stopped:
            # 计算该阶段的任务数
            tasks_per_step = max(100, current_workers * 10)

            print(f"\n   阶段: {current_workers} 并发")
            result = suite.run_concurrent_test(
                test_name=f"{name}_workers_{current_workers}",
                task_func=task_func,
                num_tasks=tasks_per_step,
                num_workers=current_workers,
                warmup_tasks=current_workers
            )

            results.append(result)

            # 检查是否继续
            success_rate = result.completed_tasks / result.total_tasks
            if success_rate < success_rate_threshold:
                print(f"⚠️  成功率 {success_rate:.1%} 低于阈值 {success_rate_threshold:.1%}")
                print(f"   停止压力测试")
                break

            current_workers += step_workers

        print(f"\n✅ 压力测试完成: {name}")
        return results

    def stop(self):
        """停止测试"""
        self.stopped = True


def _percentile(data: List[float], percentile: float) -> float:
    """计算百分位数"""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = int(len(sorted_data) * percentile / 100)
    return sorted_data[min(idx, len(sorted_data) - 1)]


def create_concurrent_test_suite(name: str = "ConcurrentTests") -> ConcurrentTestSuite:
    """创建并发测试套件"""
    return ConcurrentTestSuite(name)


def create_stress_tester() -> StressTester:
    """创建压力测试器"""
    return StressTester()
