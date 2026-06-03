"""
第71阶段简化验收测试：调度器性能优化
"""

import sys
import time
import random
from src.first_principles_agent import (
    PerformanceMonitor, LatencyTracker, ThroughputTracker,
    LRUCache, OptimizedScheduler,
    create_performance_monitor, create_lru_cache,
    WorkerNode, ResourceCapacity, TaskResourceRequirement,
    create_resource_capacity, create_task_requirement
)


def test_basic_monitoring():
    """测试基础监控"""
    print("测试：基础性能监控")
    monitor = create_performance_monitor()
    
    tracker = monitor.get_latency_tracker("test")
    for i in range(50):
        tracker.record(random.uniform(1, 10))
    
    stats = tracker.get_stats()
    assert stats.total_count == 50
    print(f"  ✓ 延迟统计: 平均={stats.avg_value:.2f}ms, P50={stats.p50:.2f}ms")
    return True


def test_lru_cache():
    """测试LRU缓存"""
    print("\n测试：LRU缓存")
    cache = create_lru_cache(max_size=20)
    
    for i in range(30):
        cache.put(f"key_{i}", f"val_{i}")
    
    assert len(cache.cache) == 20
    assert cache.get("key_0") is None
    assert cache.get("key_25") == "val_25"
    
    for i in range(10):
        cache.get(f"key_{i + 20}")
    
    hit_rate = cache.get_hit_rate()
    print(f"  ✓ 缓存: 大小={len(cache.cache)}, 命中率={hit_rate:.2%}")
    return True


def test_optimized_selection():
    """测试优化的调度选择"""
    print("\n测试：优化调度算法")
    scheduler = OptimizedScheduler()
    
    nodes = []
    for i in range(5):
        cap = create_resource_capacity(cpu_cores=8, memory_gb=32)
        node = WorkerNode(node_id=f"n{i}", name=f"Node{i}", capacity=cap)
        node.current_usage.cpu_usage = i * 1.0
        nodes.append(node)
    
    req = create_task_requirement("t1", cpu_cores=1, memory_gb=2)
    
    start = time.time()
    for _ in range(100):
        n = scheduler.optimized_select_node(req, nodes)
        assert n.node_id == "n0"
    elapsed = (time.time() - start) * 1000
    
    report = scheduler.get_performance_report()
    cache_stats = report["cache"]["node_selection"]
    print(f"  ✓ 调度: {elapsed:.2f}ms/100次, 缓存命中率={cache_stats['hit_rate']:.2%}")
    return True


def run_tests():
    """运行简化测试"""
    print("\n" + "=" * 60)
    print("第71阶段简化验收测试")
    print("=" * 60)
    
    all_passed = True
    
    try:
        if test_basic_monitoring():
            print("✅ 基础监控测试通过")
        else:
            all_passed = False
    except Exception as e:
        print(f"❌ 监控测试失败: {e}")
        all_passed = False
    
    try:
        if test_lru_cache():
            print("✅ LRU缓存测试通过")
        else:
            all_passed = False
    except Exception as e:
        print(f"❌ 缓存测试失败: {e}")
        all_passed = False
    
    try:
        if test_optimized_selection():
            print("✅ 优化调度测试通过")
        else:
            all_passed = False
    except Exception as e:
        print(f"❌ 调度测试失败: {e}")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！第71阶段完成！")
    else:
        print("⚠️  部分测试失败")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
