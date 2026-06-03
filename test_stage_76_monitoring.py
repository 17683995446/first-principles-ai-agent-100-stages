"""
第76阶段验收测试：系统监控与指标收集
"""

import sys
import time
import threading
from src.first_principles_agent import (
    MetricType,
    MetricsRegistry,
    Metric,
    AlertRule,
    AlertManager,
    MonitoringReporter,
    MonitoringManager,
    create_monitoring_manager,
    create_alert_rule
)


def test_1_basic_metrics():
    """测试1：基础指标收集"""
    print("\n" + "=" * 60)
    print("测试1：基础指标收集")
    print("=" * 60)

    registry = MetricsRegistry()

    # 计数器测试
    registry.increment("test_requests", 1.0)
    registry.increment("test_requests", 1.0)
    registry.increment("test_requests", 1.0)

    metric = registry.get_metric("test_requests")
    assert metric is not None
    assert metric.type == MetricType.COUNTER
    assert len(metric.values) == 3

    stats = metric.get_statistics()
    assert stats["count"] == 3
    assert stats["max"] == 3.0
    print(f"  ✓ 计数器统计: {stats}")

    # 仪表测试
    registry.set_gauge("test_gauge", 100.0)
    registry.set_gauge("test_gauge", 150.0)
    metric = registry.get_metric("test_gauge")
    assert metric is not None
    assert metric.values[-1].value == 150.0
    print("  ✓ 仪表设置成功")

    # 直方图测试
    for i in range(10):
        registry.record_value("test_histogram", float(i))
    metric = registry.get_metric("test_histogram")
    assert metric is not None
    assert len(metric.values) == 10
    print("  ✓ 直方图记录成功")

    all_stats = registry.get_statistics()
    assert len(all_stats) >= 3
    print(f"  ✓ 整体统计包含 {len(all_stats)} 个指标")

    print("\n✅ 测试1通过：基础指标收集正常")
    return True


def test_2_timer_context():
    """测试2：计时器上下文"""
    print("\n" + "=" * 60)
    print("测试2：计时器上下文")
    print("=" * 60)

    registry = MetricsRegistry()

    with registry.timer("test_operation"):
        time.sleep(0.01)

    metric = registry.get_metric("test_operation")
    assert metric is not None
    assert len(metric.values) == 1

    elapsed = metric.values[0].value
    print(f"  ✓ 计时器记录: {elapsed:.2f}ms")
    assert elapsed >= 1.0  # 至少1毫秒

    # 多次计时
    for _ in range(3):
        with registry.timer("test_repeated"):
            time.sleep(0.005)

    metric = registry.get_metric("test_repeated")
    assert metric is not None
    assert len(metric.values) == 3
    stats = metric.get_statistics()
    assert stats["p99"] >= 4.0  # 至少4毫秒
    print(f"  ✓ 多次计时统计: {stats}")

    print("\n✅ 测试2通过：计时器上下文正常")
    return True


def test_3_labels_and_snapshot():
    """测试3：标签与快照"""
    print("\n" + "=" * 60)
    print("测试3：标签与快照")
    print("=" * 60)

    registry = MetricsRegistry()

    # 带标签的指标
    registry.increment("api_calls", labels={"endpoint": "/users", "method": "GET"})
    registry.increment("api_calls", labels={"endpoint": "/posts", "method": "POST"})
    registry.increment("api_calls", labels={"endpoint": "/users", "method": "GET"})

    metric = registry.get_metric("api_calls")
    assert metric is not None
    assert len(metric.values) == 3

    # 快照
    snapshot = metric.get_snapshot()
    assert len(snapshot) == 3
    print(f"  ✓ 获取快照: {len(snapshot)} 个点")

    # 验证标签
    endpoints = set()
    for v in snapshot:
        if "endpoint" in v.labels:
            endpoints.add(v.labels["endpoint"])
    assert "/users" in endpoints
    assert "/posts" in endpoints
    print(f"  ✓ 标签正确: {endpoints}")

    print("\n✅ 测试3通过：标签与快照功能正常")
    return True


def test_4_statistics_calculation():
    """测试4：统计计算"""
    print("\n" + "=" * 60)
    print("测试4：统计计算")
    print("=" * 60)

    registry = MetricsRegistry()

    # 生成更多数据点以获得稳定的百分位计算
    values = list(range(1, 101))  # 1-100
    for v in values:
        registry.record_value("test_data", float(v))

    metric = registry.get_metric("test_data")
    stats = metric.get_statistics()

    assert stats["count"] == 100
    assert stats["min"] == 1.0
    assert stats["max"] == 100.0
    assert 45.0 <= stats["mean"] <= 55.0
    assert 45.0 <= stats["median"] <= 55.0

    print(f"  ✓ 统计计算: count={stats['count']}, "
          f"min={stats['min']}, max={stats['max']}, "
          f"mean={stats['mean']:.2f}, median={stats['median']:.2f}")
    print(f"  ✓ 百分位: p50={stats['p50']:.2f}, "
          f"p90={stats['p90']:.2f}, p95={stats['p95']:.2f}, p99={stats['p99']:.2f}")

    print("\n✅ 测试4通过：统计计算功能正常")
    return True


def test_5_alert_rules():
    """测试5：告警规则"""
    print("\n" + "=" * 60)
    print("测试5：告警规则")
    print("=" * 60)

    registry = MetricsRegistry()
    alert_manager = AlertManager()

    # 创建告警规则：当最近值超过5时告警
    def high_error_condition(metric):
        if not metric.values:
            return False
        return metric.values[-1].value > 5.0

    rule = create_alert_rule(
        name="high_errors",
        metric_name="error_rate",
        condition=high_error_condition,
        message="Error rate too high",
        level="error",
        cooldown_seconds=10.0
    )
    alert_manager.add_rule(rule)

    # 先记录一些低值（不触发告警）
    registry.record_value("error_rate", 2.0)
    registry.record_value("error_rate", 3.0)
    alerts = alert_manager.check_rules(registry)
    assert len(alerts) == 0
    print("  ✓ 低值不触发告警")

    # 记录高值（触发告警）
    registry.record_value("error_rate", 6.0)
    alerts = alert_manager.check_rules(registry)
    assert len(alerts) == 1
    assert alerts[0]["level"] == "error"
    print(f"  ✓ 告警触发成功: {alerts[0]['message']}")

    # 再次检查（冷却期间不触发）
    alerts = alert_manager.check_rules(registry)
    assert len(alerts) == 0
    print("  ✓ 冷却期间不重复告警")

    # 获取最近告警
    recent = alert_manager.get_recent_alerts(limit=10)
    assert len(recent) >= 1
    print(f"  ✓ 获取最近告警: {len(recent)} 条")

    print("\n✅ 测试5通过：告警规则功能正常")
    return True


def test_6_monitoring_manager():
    """测试6：监控管理器"""
    print("\n" + "=" * 60)
    print("测试6：监控管理器")
    print("=" * 60)

    manager = create_monitoring_manager()

    # 记录各种指标
    manager.increment("requests", 1.0)
    manager.set_gauge("connections", 50.0)
    manager.record_value("latency", 10.5)

    with manager.timer("operation_latency"):
        time.sleep(0.005)

    # 获取单个指标
    metric = manager.get_metric("requests")
    assert metric is not None
    print("  ✓ 指标获取成功")

    # 获取报告
    report = manager.get_report()
    assert "timestamp" in report
    assert "metrics" in report
    assert "recent_alerts" in report
    assert len(report["metrics"]) >= 4
    print(f"  ✓ 报告生成成功，包含 {len(report['metrics'])} 个指标")

    # 检查告警
    alerts = manager.check_alerts()
    assert isinstance(alerts, list)
    print("  ✓ 告警检查成功")

    print("\n✅ 测试6通过：监控管理器功能正常")
    return True


def run_all_tests():
    """运行所有验收测试"""
    print("\n" + "=" * 60)
    print("第76阶段验收测试：系统监控与指标收集")
    print("=" * 60)

    tests = [
        test_1_basic_metrics,
        test_2_timer_context,
        test_3_labels_and_snapshot,
        test_4_statistics_calculation,
        test_5_alert_rules,
        test_6_monitoring_manager
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
        print("\n🎉 所有验收测试通过！第76阶段完成！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
