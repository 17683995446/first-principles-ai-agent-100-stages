"""
第73阶段验收测试：任务熔断器与限流器
"""

import sys
import time
import random
from src.first_principles_agent import (
    CircuitBreaker, CircuitBreakerConfig, CircuitState,
    RateLimiter, RateLimitConfig, RateLimitStrategy,
    Bulkhead, ResilienceManager,
    create_circuit_breaker, create_rate_limiter,
    create_bulkhead, create_resilience_manager
)


def test_1_circuit_breaker_basic():
    """测试1：熔断器基础功能"""
    print("\n" + "=" * 60)
    print("测试1：熔断器基础功能")
    print("=" * 60)

    config = CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_seconds=1.0
    )
    cb = create_circuit_breaker("test_cb", config)

    # 初始状态应该是关闭
    assert cb.state == CircuitState.CLOSED
    print("  ✓ 初始状态: closed")

    # 记录失败调用
    for _ in range(3):
        cb.record_failure(10.0)
        time.sleep(0.05)

    # 应该转换到open状态
    assert cb.state == CircuitState.OPEN
    print("  ✓ 3次失败后状态: open")

    # 尝试调用应该被拒绝
    assert not cb.is_callable()
    print("  ✓ open状态下调用被拒绝")

    stats = cb.get_stats()
    assert stats.failed_calls == 3
    assert stats.rejected_calls >= 1
    print(f"  ✓ 统计: 失败={stats.failed_calls}, 拒绝={stats.rejected_calls}")

    print("\n✅ 测试1通过：熔断器基础功能正常")
    return True


def test_2_circuit_breaker_recovery():
    """测试2：熔断器恢复机制"""
    print("\n" + "=" * 60)
    print("测试2：熔断器恢复机制")
    print("=" * 60)

    config = CircuitBreakerConfig(
        failure_threshold=2,
        success_threshold=2,
        timeout_seconds=0.5
    )
    cb = create_circuit_breaker("recovery_cb", config)

    # 触发熔断
    cb.record_failure(10.0)
    cb.record_failure(10.0)
    time.sleep(0.1)

    assert cb.state == CircuitState.OPEN
    print("  ✓ 触发熔断: open")

    # 等待超时
    time.sleep(0.6)
    assert cb.state == CircuitState.HALF_OPEN
    print("  ✓ 超时后: half_open")

    # 半开状态下可以调用
    assert cb.is_callable()
    print("  ✓ half_open可以调用")

    # 记录成功
    cb.record_success(5.0)
    cb.record_success(5.0)

    assert cb.state == CircuitState.CLOSED
    print("  ✓ 恢复成功: closed")

    stats = cb.get_stats()
    print(f"  ✓ 总调用: {stats.total_calls}, 成功: {stats.successful_calls}")

    print("\n✅ 测试2通过：熔断器恢复机制正常")
    return True


def test_3_rate_limiter_token_bucket():
    """测试3：限流器-令牌桶"""
    print("\n" + "=" * 60)
    print("测试3：限流器-令牌桶")
    print("=" * 60)

    config = RateLimitConfig(
        max_requests=10,
        time_window_seconds=1.0,
        strategy=RateLimitStrategy.TOKEN_BUCKET,
        burst_size=5
    )
    rl = create_rate_limiter("token_bucket", config)

    # 快速获取5个令牌
    acquired = 0
    for _ in range(10):
        if rl.try_acquire("test"):
            acquired += 1

    assert acquired >= 5
    print(f"  ✓ 初始获取: {acquired} 个令牌")

    # 等待补充
    time.sleep(2.0)

    # 再次获取
    acquired2 = 0
    for _ in range(10):
        if rl.try_acquire("test"):
            acquired2 += 1

    assert acquired2 >= 5
    print(f"  ✓ 补充后获取: {acquired2} 个令牌")

    stats = rl.get_stats()
    print(f"  ✓ 总请求: {stats['total_requests']}, 拒绝: {stats['rejected_requests']}")

    print("\n✅ 测试3通过：限流器令牌桶功能正常")
    return True


def test_4_rate_limiter_sliding_window():
    """测试4：限流器-滑动窗口"""
    print("\n" + "=" * 60)
    print("测试4：限流器-滑动窗口")
    print("=" * 60)

    config = RateLimitConfig(
        max_requests=5,
        time_window_seconds=1.0,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    )
    rl = create_rate_limiter("sliding_window", config)

    # 获取5个请求
    for i in range(5):
        assert rl.try_acquire("test")
        print(f"  ✓ 请求 {i+1}: 成功")

    # 第6个应该被拒绝
    assert not rl.try_acquire("test")
    print("  ✓ 第6个请求: 拒绝")

    # 等待窗口滑动
    time.sleep(1.1)

    # 应该可以再次获取
    assert rl.try_acquire("test")
    print("  ✓ 窗口滑动后: 成功")

    stats = rl.get_stats()
    print(f"  ✓ 总请求: {stats['total_requests']}, 拒绝率: {stats['rejection_rate']:.2%}")

    print("\n✅ 测试4通过：限流器滑动窗口功能正常")
    return True


def test_5_bulkhead():
    """测试5：舱壁隔离"""
    print("\n" + "=" * 60)
    print("测试5：舱壁隔离")
    print("=" * 60)

    bulkhead = create_bulkhead(max_concurrent=3, max_queue=2)

    def slow_task():
        time.sleep(0.1)
        return "done"

    # 执行3个并发任务
    results = []
    for i in range(3):
        result = bulkhead.execute(slow_task)
        results.append(result)

    assert len(results) == 3
    print(f"  ✓ 并发执行3个任务: {results}")

    stats = bulkhead.get_stats()
    print(f"  ✓ 活跃调用: {stats['active_calls']}, 总调用: {stats['total_calls']}")

    print("\n✅ 测试5通过：舱壁隔离功能正常")
    return True


def test_6_resilience_manager():
    """测试6：弹性管理器"""
    print("\n" + "=" * 60)
    print("测试6：弹性管理器")
    print("=" * 60)

    manager = create_resilience_manager("test_manager")

    # 注册组件
    manager.register_circuit_breaker("service_a", CircuitBreakerConfig(failure_threshold=3))
    manager.register_rate_limiter("api", RateLimitConfig(max_requests=100))
    manager.register_bulkhead("tasks", max_concurrent=10)

    print("  ✓ 注册了: 1个熔断器, 1个限流器, 1个舱壁")

    # 获取并使用组件
    cb = manager.get_circuit_breaker("service_a")
    assert cb is not None
    cb.record_failure(10.0)
    print(f"  ✓ 熔断器状态: {cb.state.value}")

    rl = manager.get_rate_limiter("api")
    assert rl is not None
    assert rl.try_acquire()
    print(f"  ✓ 限流器可用: True")

    bh = manager.get_bulkhead("tasks")
    assert bh is not None
    print(f"  ✓ 舱壁活跃: {bh.get_stats()['active_calls']}")

    # 获取所有统计
    all_stats = manager.get_all_stats()
    assert "circuit_breakers" in all_stats
    assert "rate_limiters" in all_stats
    assert "bulkheads" in all_stats
    print(f"  ✓ 统计信息完整: {list(all_stats.keys())}")

    print("\n✅ 测试6通过：弹性管理器功能正常")
    return True


def run_all_tests():
    """运行所有验收测试"""
    print("\n" + "=" * 60)
    print("第73阶段验收测试：任务熔断器与限流器")
    print("=" * 60)

    tests = [
        test_1_circuit_breaker_basic,
        test_2_circuit_breaker_recovery,
        test_3_rate_limiter_token_bucket,
        test_4_rate_limiter_sliding_window,
        test_5_bulkhead,
        test_6_resilience_manager
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
        print("\n🎉 所有验收测试通过！第73阶段完成！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
