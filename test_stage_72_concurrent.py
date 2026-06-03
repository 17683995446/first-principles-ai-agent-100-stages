"""
第72阶段验收测试：大规模并发测试
"""

import sys
import time
import random
from src.first_principles_agent import (
    create_concurrent_test_suite,
    create_stress_tester,
    create_lru_cache,
    OptimizedScheduler,
    WorkerNode,
    create_resource_capacity,
    create_task_requirement
)


def test_1_basic_concurrent():
    """测试1：基础并发测试"""
    print("\n" + "=" * 60)
    print("测试1：基础并发测试")
    print("=" * 60)

    suite = create_concurrent_test_suite("BasicConcurrentTests")

    # 简单任务：模拟计算
    def simple_task(task_idx: int):
        time.sleep(random.uniform(0.001, 0.01))
        return task_idx * 2

    result = suite.run_concurrent_test(
        test_name="simple_100_tasks",
        task_func=simple_task,
        num_tasks=100,
        num_workers=10,
        warmup_tasks=10
    )

    assert result.status.value == "completed"
    assert result.failed_tasks == 0
    assert result.throughput_tps > 0

    print("\n✅ 测试1通过：基础并发测试正常")
    return True


def test_2_lru_cache_concurrent():
    """测试2：LRU缓存并发测试"""
    print("\n" + "=" * 60)
    print("测试2：LRU缓存并发测试")
    print("=" * 60)

    suite = create_concurrent_test_suite("LRUCacheTests")
    cache = create_lru_cache(max_size=1000)

    # 缓存任务
    def cache_task(task_idx: int):
        key = f"key_{task_idx % 100}"  # 100个不同的键
        if cache.get(key) is None:
            cache.put(key, task_idx)
        return cache.get(key)

    result = suite.run_concurrent_test(
        test_name="lru_cache_500_tasks",
        task_func=cache_task,
        num_tasks=500,
        num_workers=20,
        warmup_tasks=20
    )

    assert result.status.value == "completed"
    assert result.failed_tasks == 0

    # 检查缓存命中率
    hit_rate = cache.get_hit_rate()
    print(f"\n   缓存命中率: {hit_rate:.2%}")
    assert hit_rate > 0.7

    print("\n✅ 测试2通过：LRU缓存并发测试正常")
    return True


def test_3_scheduler_concurrent():
    """测试3：调度器并发测试"""
    print("\n" + "=" * 60)
    print("测试3：调度器并发测试")
    print("=" * 60)

    suite = create_concurrent_test_suite("SchedulerTests")
    scheduler = OptimizedScheduler()

    # 创建工作节点
    nodes = []
    for i in range(10):
        cap = create_resource_capacity(cpu_cores=16, memory_gb=64)
        node = WorkerNode(node_id=f"node_{i}", name=f"Node_{i}", capacity=cap)
        nodes.append(node)

    # 使用相同的资源需求，这样缓存会命中
    fixed_cpu = 1.0
    fixed_memory = 2.0

    # 调度任务
    def scheduler_task(task_idx: int):
        req = create_task_requirement(
            task_id=f"req_{task_idx}",
            cpu_cores=fixed_cpu,
            memory_gb=fixed_memory
        )
        return scheduler.submit_task_optimized(req, nodes)

    result = suite.run_concurrent_test(
        test_name="scheduler_200_tasks",
        task_func=scheduler_task,
        num_tasks=200,
        num_workers=15,
        warmup_tasks=15
    )

    assert result.status.value == "completed"
    assert result.failed_tasks == 0

    # 检查性能报告
    perf_report = scheduler.get_performance_report()
    cache_hit_rate = perf_report["cache"]["node_selection"]["hit_rate"]
    print(f"   调度器缓存命中率: {cache_hit_rate:.2%}")
    # 由于有预热阶段，命中率应该较高
    assert cache_hit_rate > 0.7

    print("\n✅ 测试3通过：调度器并发测试正常")
    return True


def test_4_scalability():
    """测试4：可扩展性测试"""
    print("\n" + "=" * 60)
    print("测试4：可扩展性测试")
    print("=" * 60)

    suite = create_concurrent_test_suite("ScalabilityTests")

    def scalable_task(task_idx: int):
        # 模拟一个可扩展的任务
        result = 0
        for i in range(100):
            result += i
        return result

    # 不同并发度的测试
    for workers in [5, 10, 20, 30]:
        print(f"\n--- 并发度 {workers} ---")
        result = suite.run_concurrent_test(
            test_name=f"scalability_workers_{workers}",
            task_func=scalable_task,
            num_tasks=workers * 20,
            num_workers=workers,
            warmup_tasks=workers
        )
        assert result.failed_tasks == 0

    summary = suite.get_summary()
    print(f"\n   总测试数: {summary['num_tests']}")
    print(f"   平均吞吐量: {summary['avg_throughput_tps']:.2f} TPS")

    print("\n✅ 测试4通过：可扩展性测试正常")
    return True


def test_5_mini_stress_test():
    """测试5：小型压力测试"""
    print("\n" + "=" * 60)
    print("测试5：小型压力测试")
    print("=" * 60)

    stress_tester = create_stress_tester()

    def stress_task(task_idx: int):
        # 轻量级压力任务
        time.sleep(0.001)
        return task_idx

    # 运行小型压力测试
    results = stress_tester.run_stress_test(
        name="mini_stress",
        task_func=stress_task,
        initial_workers=5,
        max_workers=25,
        step_workers=5,
        success_rate_threshold=0.9
    )

    assert len(results) > 0
    all_success = all(r.failed_tasks == 0 for r in results)
    assert all_success, "部分压力测试任务失败"

    # 打印压力测试结果
    print("\n--- 压力测试结果 ---")
    for r in results:
        print(f"   {r.test_name}: {r.throughput_tps:.1f} TPS, P95={r.p95_latency_ms:.2f}ms")

    print("\n✅ 测试5通过：小型压力测试正常")
    return True


def run_all_tests():
    """运行所有验收测试"""
    print("\n" + "=" * 60)
    print("第72阶段验收测试：大规模并发测试")
    print("=" * 60)

    tests = [
        test_1_basic_concurrent,
        test_2_lru_cache_concurrent,
        test_3_scheduler_concurrent,
        test_4_scalability,
        test_5_mini_stress_test
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ 测试失败: {test.__name__}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 所有验收测试通过！第72阶段完成！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
