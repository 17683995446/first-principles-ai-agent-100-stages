"""
性能基准测试和最终优化验证 - 第89阶段
完整的性能基准测试框架
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Callable
import time
import statistics
from first_principles_agent import (
    Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction
)


@dataclass
class BenchmarkResult:
    """性能基准测试结果"""
    name: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    median_time_ms: float
    std_dev_ms: float
    ops_per_sec: float
    success_rate: float
    details: Dict[str, Any] = field(default_factory=dict)


class PerformanceBenchmarkFinal:
    """最终性能基准测试"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.baseline_results: Dict[str, BenchmarkResult] = {}
    
    def run_benchmark(self, name: str, 
                     test_func: Callable, 
                     iterations: int = 100,
                     warmup: int = 10) -> BenchmarkResult:
        """运行性能基准测试"""
        # 预热
        for _ in range(warmup):
            test_func()
        
        # 正式测试
        times_ms = []
        success_count = 0
        
        for i in range(iterations):
            start = time.time()
            try:
                result = test_func()
                success = result if isinstance(result, bool) else True
                if success:
                    success_count += 1
            except Exception:
                success = False
            end = time.time()
            times_ms.append((end - start) * 1000)
        
        # 计算统计
        total_time = sum(times_ms)
        avg_time = total_time / len(times_ms)
        min_time = min(times_ms)
        max_time = max(times_ms)
        median_time = statistics.median(times_ms)
        std_dev = statistics.stdev(times_ms) if len(times_ms) > 1 else 0
        ops_per_sec = (iterations * 1000) / total_time if total_time > 0 else 0
        success_rate = success_count / iterations
        
        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            median_time_ms=median_time,
            std_dev_ms=std_dev,
            ops_per_sec=ops_per_sec,
            success_rate=success_rate
        )
        
        self.results.append(result)
        return result
    
    def create_simple_task_test(self) -> Callable:
        """创建简单任务测试"""
        def test():
            quartet = TaskQuartet(
                target="Simple task",
                end_rule=lambda ctx: "result" in ctx
            )
            task = Task("simple_test", quartet, {"x": 1, "y": 2})
            agent = FirstPrinciplesAgent()
            agent.set_task(task)
            
            def add(ctx):
                return {"result": ctx["x"] + ctx["y"]}
            
            agent.set_atomic_actions([AtomicAction("add", "Add", add)])
            result = agent.execute()
            return result.success
        
        return test
    
    def create_complex_task_test(self) -> Callable:
        """创建复杂任务测试"""
        def test():
            quartet = TaskQuartet(
                target="Complex workflow",
                end_rule=lambda ctx: "final" in ctx
            )
            task = Task("complex_test", quartet, {"data": list(range(50))})
            agent = FirstPrinciplesAgent()
            agent.set_task(task)
            
            def step1(ctx):
                return {"sum1": sum(ctx["data"])}
            
            def step2(ctx):
                return {"sum2": ctx["sum1"] * 2}
            
            def step3(ctx):
                return {"final": ctx["sum2"] + 100}
            
            agent.set_atomic_actions([
                AtomicAction("s1", "Step1", step1),
                AtomicAction("s2", "Step2", step2),
                AtomicAction("s3", "Step3", step3)
            ])
            result = agent.execute()
            return result.success
        
        return test
    
    def create_context_test(self, size: int) -> Callable:
        """创建上下文大小测试"""
        def test():
            large_context = {f"key_{i}": i for i in range(size)}
            quartet = TaskQuartet(
                target=f"Test context size {size}",
                end_rule=lambda ctx: "processed" in ctx
            )
            task = Task(f"context_{size}", quartet, large_context)
            agent = FirstPrinciplesAgent()
            agent.set_task(task)
            
            def process(ctx):
                total = sum(v for k, v in ctx.items() if k.startswith("key_"))
                return {"processed": total}
            
            agent.set_atomic_actions([AtomicAction("proc", "Process", process)])
            result = agent.execute()
            return result.success
        
        return test
    
    def run_full_suite(self) -> Dict[str, Any]:
        """运行完整的性能基准测试套件"""
        print("="*70)
        print("Performance Benchmark Suite - Stage 89")
        print("="*70)
        
        # 简单任务测试
        print("\n1. Simple Task Execution")
        self.run_benchmark(
            "Simple Task", 
            self.create_simple_task_test(),
            iterations=200,
            warmup=20
        )
        
        # 复杂任务测试
        print("\n2. Complex Task Execution")
        self.run_benchmark(
            "Complex Task", 
            self.create_complex_task_test(),
            iterations=100,
            warmup=10
        )
        
        # 上下文大小测试
        print("\n3. Context Size Test")
        for size in [10, 50, 100]:
            self.run_benchmark(
                f"Context Size {size}",
                self.create_context_test(size),
                iterations=50,
                warmup=5
            )
        
        return self.generate_summary()
    
    def generate_summary(self) -> Dict[str, Any]:
        """生成基准测试总结"""
        print("\n" + "="*70)
        print("Benchmark Summary")
        print("="*70)
        
        summary = {
            "results": [],
            "all_passed": True
        }
        
        for result in self.results:
            result_data = {
                "name": result.name,
                "iterations": result.iterations,
                "avg_ms": round(result.avg_time_ms, 4),
                "min_ms": round(result.min_time_ms, 4),
                "max_ms": round(result.max_time_ms, 4),
                "ops_sec": round(result.ops_per_sec, 2),
                "success_rate": round(result.success_rate * 100, 2)
            }
            summary["results"].append(result_data)
            
            if result.success_rate < 1.0:
                summary["all_passed"] = False
            
            print(f"\n{result.name}")
            print(f"  Iterations: {result.iterations}")
            print(f"  Avg: {result.avg_time_ms:.4f}ms")
            print(f"  Min: {result.min_time_ms:.4f}ms")
            print(f"  Max: {result.max_time_ms:.4f}ms")
            print(f"  Throughput: {result.ops_per_sec:.2f} ops/s")
            print(f"  Success: {result.success_rate * 100:.1f}%")
        
        print("\n" + "="*70)
        overall = "✓ ALL BENCHMARKS PASSED" if summary["all_passed"] else "⚠ Some issues found"
        print(f"Overall: {overall}")
        print("="*70)
        
        return summary


def create_final_benchmark() -> PerformanceBenchmarkFinal:
    """创建最终基准测试器"""
    return PerformanceBenchmarkFinal()


def run_final_benchmarks() -> Dict[str, Any]:
    """运行最终基准测试"""
    benchmark = create_final_benchmark()
    return benchmark.run_full_suite()
