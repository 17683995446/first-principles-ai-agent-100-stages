"""
第71阶段验收测试：调度器性能优化

验证5个维度：
1. 性能监控功能
2. LRU缓存功能
3. 批量处理功能
4. 调度算法优化
5. 综合性能测试
"""

import sys
import time
import random
from src.first_principles_agent import (
    PerformanceMonitor, LatencyTracker, ThroughputTracker,
    LRUCache, BatchProcessor, OptimizedScheduler,
    create_performance_monitor, create_lru_cache, create_batch_processor,
    WorkerNode, ResourceCapacity, TaskResourceRequirement,
    create_resource_capacity, create_task_requirement
)


def test_1_performance_monitoring():
    """测试1：性能监控功能"""
    print("=" * 60)
    print("测试1：性能监控功能")
    print("=" * 60)
    
    monitor = create_performance_monitor()
    
    latency_tracker = monitor.get_latency_tracker("test_operation")
    throughput_tracker = monitor.get_throughput_tracker("test_tasks")
    
    for i in range(100):
        latency = random.uniform(1.0, 10.0)
        latency_tracker.record(latency)
        throughput_tracker.record()
    
    time.sleep(0.1)
    
    stats = monitor.get_all_stats()
    
    assert "latency" in stats
    assert "test_operation" in stats["latency"]
    assert stats["latency"]["test_operation"].total_count == 100
    assert stats["latency"]["test_operation"].avg_value > 0
    
    assert "throughput" in stats
    assert "test_tasks" in stats["throughput"]
    assert stats["throughput"]["test_tasks"] > 0
    
    latency_stats = latency_tracker.get_stats()
    assert latency_stats.min_value >= 1.0
    assert latency_stats.max_value <= 10.0
    assert latency_stats.p50 > 0
    assert latency_stats.p95 > 0
    assert latency_stats.p99 > 0
    
    print(f"  延迟统计 - 平均: {latency_stats.avg_value:.2f}ms, "
          f"P50: {latency_stats.p50:.2f}ms, "
          f"P95: {latency_stats.p95:.2f}ms")
    print(f"  吞吐量: {stats['throughput']['test_tasks']:.2f} tasks/sec")
    print("✅ 测试1通过：性能监控功能正常\n")
    return True


def test_2_lru_cache():
    """测试2：LRU缓存功能"""
    print("=" * 60)
    print("测试2：LRU缓存功能")
    print("=" * 60)
    
    cache = create_lru_cache(max_size=10)
    
    for i in range(15):
        cache.put(f"key_{i}", f"value_{i}")
    
    assert len(cache.cache) == 10
    assert cache.get("key_0") is None
    assert cache.get("key_5") == "value_5"
    
    cache.get("key_10")
    cache.get("key_11")
    cache.get("key_12")
    
    for i in range(20, 30):
        cache.put(f"key_{i}", f"value_{i}")
    
    hit_rate = cache.get_hit_rate()
    assert hit_rate >= 0
    assert hit_rate <= 1.0
    
    print(f"  缓存大小: {len(cache.cache)}/{cache.max_size}")
    print(f"  命中次数: {cache.hits}, 未命中次数: {cache.misses}")
    print(f"  命中率: {hit_rate:.2%}")
    
    cache.clear()
    assert len(cache.cache) == 0
    assert cache.hits == 0
    assert cache.misses == 0
    
    print("✅ 测试2通过：LRU缓存功能正常\n")
    return True


def test_3_batch_processor():
    """测试3：批量处理功能"""
    print("=" * 60)
    print("测试3：批量处理功能")
    print("=" * 60)
    
    def process_items(items):
        return [item * 2 for item in items]
    
    processor = create_batch_processor(
        process_func=process_items,
        batch_size=5,
        flush_interval=0.5
    )
    
    processor.start()
    
    start = time.time()
    results = []
    for i in range(20):
        result = processor.submit(i)
        results.append(result)
    
    expected = [i * 2 for i in range(20)]
    assert results == expected
    
    elapsed = time.time() - start
    print(f"  处理 {len(results)} 个项目, 耗时: {elapsed:.3f}s")
    print(f"  结果验证通过: {results[:5]}...")
    
    batch_results = processor.submit_batch([100, 200, 300])
    assert batch_results == [200, 400, 600]
    
    processor.stop()
    print("✅ 测试3通过：批量处理功能正常\n")
    return True


def test_4_optimized_scheduler():
    """测试4：调度算法优化"""
    print("=" * 60)
    print("测试4：调度算法优化")
    print("=" * 60)
    
    scheduler = OptimizedScheduler()
    
    nodes = []
    for i in range(10):
        capacity = create_resource_capacity(
            cpu_cores=8.0,
            memory_gb=32.0
        )
        node = WorkerNode(
            node_id=f"node_{i}",
            name=f"Node {i}",
            capacity=capacity
        )
        node.current_usage.cpu_usage = i * 0.5
        nodes.append(node)
    
    requirement = create_task_requirement(
        task_id="test_task",
        cpu_cores=1.0,
        memory_gb=2.0
    )
    
    start = time.time()
    for i in range(100):
        node = scheduler.submit_task_optimized(requirement, nodes)
        assert node is not None
        assert node.node_id == "node_0"
    elapsed = (time.time() - start) * 1000
    
    report = scheduler.get_performance_report()
    
    assert "latency" in report
    assert "throughput" in report
    assert "cache" in report
    
    cache_stats = report["cache"]["node_selection"]
    assert cache_stats["hits"] > 0
    assert cache_stats["hit_rate"] > 0.5
    
    print(f"  执行 100 次调度, 平均耗时: {elapsed / 100:.3f}ms/次")
    print(f"  缓存命中率: {cache_stats['hit_rate']:.2%}")
    print(f"  缓存命中: {cache_stats['hits']}, 未命中: {cache_stats['misses']}")
    print("✅ 测试4通过：调度算法优化正常\n")
    return True


def test_5_comprehensive_performance():
    """测试5：综合性能测试"""
    print("=" * 60)
    print("测试5：综合性能测试")
    print("=" * 60)
    
    monitor = create_performance_monitor()
    cache = monitor.get_cache("test_cache", max_size=100)
    latency_tracker = monitor.get_latency_tracker("operations")
    throughput_tracker = monitor.get_throughput_tracker("tasks")
    
    nodes = []
    for i in range(5):
        capacity = create_resource_capacity(cpu_cores=16.0, memory_gb=64.0)
        node = WorkerNode(node_id=f"node_{i}", name=f"Node {i}", capacity=capacity)
        nodes.append(node)
    
    scheduler = OptimizedScheduler(monitor=monitor)
    
    start_time = time.time()
    for i in range(500):
        req = create_task_requirement(
            task_id=f"task_{i}",
            cpu_cores=0.5,
            memory_gb=1.0
        )
        
        cache_key = f"task_{i % 20}"
        if cache.get(cache_key) is None:
            cache.put(cache_key, i)
        
        node = scheduler.submit_task_optimized(req, nodes)
        
        latency_tracker.record(random.uniform(0.1, 5.0))
        throughput_tracker.record()
    
    total_time = time.time() - start_time
    
    stats = monitor.get_all_stats()
    
    print(f"\n  综合性能报告:")
    print(f"    总任务数: 500")
    print(f"    总耗时: {total_time:.3f}s")
    print(f"    吞吐量: {500 / total_time:.2f} tasks/sec")
    
    if "latency" in stats and "scheduling" in stats["latency"]:
        sched_stats = stats["latency"]["scheduling"]
        print(f"    调度延迟 - P50: {sched_stats.p50:.3f}ms, "
              f"P95: {sched_stats.p95:.3f}ms")
    
    if "cache" in stats and "test_cache" in stats["cache"]:
        cache_stats = stats["cache"]["test_cache"]
        print(f"    缓存命中率: {cache_stats['hit_rate']:.2%}")
    
    assert total_time < 10.0
    print("\n✅ 测试5通过：综合性能测试正常\n")
    return True


def run_all_tests():
    """运行所有验收测试"""
    print("\n" + "=" * 60)
    print("第71阶段验收测试：调度器性能优化")
    print("=" * 60 + "\n")
    
    tests = [
        test_1_performance_monitoring,
        test_2_lru_cache,
        test_3_batch_processor,
        test_4_optimized_scheduler,
        test_5_comprehensive_performance
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
            print(f"\n❌ 测试失败：{test.__name__}")
            print(f"   错误：{e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果：{passed}/{len(tests)} 通过")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 所有验收测试通过！第71阶段完成！\n")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
