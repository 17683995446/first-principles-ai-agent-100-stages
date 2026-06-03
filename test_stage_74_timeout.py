"""
第74阶段验收测试：任务超时管理与死锁检测
"""

import sys
import time
import threading
from src.first_principles_agent import (
    TaskTimeoutManager, TaskTimeoutConfig, TaskTimeoutStatus,
    DeadlockDetector, DeadlockStatus,
    TimeoutDeadlockManager,
    create_timeout_manager, create_deadlock_detector,
    create_timeout_deadlock_manager
)


def test_1_timeout_manager_basic():
    """测试1：超时管理器基础功能"""
    print("\n" + "=" * 60)
    print("测试1：超时管理器基础功能")
    print("=" * 60)

    config = TaskTimeoutConfig(
        default_timeout_seconds=1.0,
        enable_soft_timeout=True,
        soft_timeout_percentage=0.5
    )
    manager = create_timeout_manager(config)

    # 注册任务
    manager.register_task("task_1", timeout_seconds=2.0)
    assert manager.get_task_status("task_1") == TaskTimeoutStatus.RUNNING
    print("  ✓ 任务注册成功")

    # 等待一小段时间
    time.sleep(0.3)

    # 标记完成
    manager.mark_completed("task_1")
    assert manager.get_task_status("task_1") == TaskTimeoutStatus.COMPLETED
    print("  ✓ 任务标记完成")

    stats = manager.get_statistics()
    print(f"  ✓ 统计: 总任务={stats['total_tasks']}, 完成={stats['completed_tasks']}")

    manager.stop()
    print("\n✅ 测试1通过：超时管理器基础功能正常")
    return True


def test_2_timeout_detection():
    """测试2：超时检测"""
    print("\n" + "=" * 60)
    print("测试2：超时检测")
    print("=" * 60)

    config = TaskTimeoutConfig(
        default_timeout_seconds=0.5,
        enable_hard_timeout=True
    )
    manager = create_timeout_manager(config)
    manager.start()

    # 注册任务
    manager.register_task("timeout_task")
    assert manager.get_task_status("timeout_task") == TaskTimeoutStatus.RUNNING
    print("  ✓ 任务注册，运行中")

    # 等待超时
    time.sleep(0.6)

    status = manager.get_task_status("timeout_task")
    assert status == TaskTimeoutStatus.TIMEOUT
    print("  ✓ 任务已超时")

    timed_out = manager.get_timed_out_tasks()
    assert "timeout_task" in timed_out
    print(f"  ✓ 超时任务列表: {timed_out}")

    stats = manager.get_statistics()
    assert stats["timeout_tasks"] >= 1
    print(f"  ✓ 超时统计: timeout_tasks={stats['timeout_tasks']}")

    manager.stop()
    print("\n✅ 测试2通过：超时检测功能正常")
    return True


def test_3_timeout_callback():
    """测试3：超时回调"""
    print("\n" + "=" * 60)
    print("测试3：超时回调")
    print("=" * 60)

    callback_events = []

    def timeout_callback(task_id, event, info):
        callback_events.append((task_id, event))
        print(f"  ✓ 回调触发: task={task_id}, event={event}")

    config = TaskTimeoutConfig(
        default_timeout_seconds=0.3,
        enable_soft_timeout=True,
        soft_timeout_percentage=0.5
    )
    manager = create_timeout_manager(config)
    manager.start()

    # 注册带回调的任务
    manager.register_task("callback_task", callbacks=[timeout_callback])

    # 等待软超时和硬超时
    time.sleep(0.8)

    assert len(callback_events) >= 1
    print(f"  ✓ 回调事件数: {len(callback_events)}")

    manager.stop()
    print("\n✅ 测试3通过：超时回调功能正常")
    return True


def test_4_deadlock_detector_basic():
    """测试4：死锁检测器基础"""
    print("\n" + "=" * 60)
    print("测试4：死锁检测器基础")
    print("=" * 60)

    detector = create_deadlock_detector()

    # 获取资源锁
    assert detector.acquire_lock("resource_a", "task_1", timeout_seconds=1.0)
    print("  ✓ task_1 获取 resource_a")

    assert detector.acquire_lock("resource_b", "task_2", timeout_seconds=1.0)
    print("  ✓ task_2 获取 resource_b")

    # 检查锁状态
    lock_a = detector.get_resource_lock("resource_a")
    assert lock_a is not None
    assert lock_a.holder_task_id == "task_1"
    print(f"  ✓ resource_a 持有者: {lock_a.holder_task_id}")

    # 检查任务持有的锁
    task1_locks = detector.get_task_locks("task_1")
    assert "resource_a" in task1_locks
    print(f"  ✓ task_1 持有的锁: {task1_locks}")

    # 释放锁
    assert detector.release_lock("resource_a", "task_1")
    print("  ✓ task_1 释放 resource_a")

    stats = detector.get_statistics()
    assert stats["total_acquires"] >= 2
    assert stats["total_releases"] >= 1
    print(f"  ✓ 统计: 获取={stats['total_acquires']}, 释放={stats['total_releases']}")

    print("\n✅ 测试4通过：死锁检测器基础功能正常")
    return True


def test_5_deadlock_detection():
    """测试5：死锁检测"""
    print("\n" + "=" * 60)
    print("测试5：死锁检测")
    print("=" * 60)

    detector = create_deadlock_detector()

    # 模拟死锁场景
    detector.acquire_lock("resource_1", "task_a", timeout_seconds=0.1)
    print("  ✓ task_a 获取 resource_1")

    detector.acquire_lock("resource_2", "task_b", timeout_seconds=0.1)
    print("  ✓ task_b 获取 resource_2")

    # 尝试获取对方持有的资源（会超时）
    result_a = detector.acquire_lock("resource_2", "task_a", timeout_seconds=0.2)
    result_b = detector.acquire_lock("resource_1", "task_b", timeout_seconds=0.2)

    # 至少一个会失败（死锁检测）
    assert result_a == False or result_b == False
    print(f"  ✓ 死锁检测: task_a={result_a}, task_b={result_b}")

    # 检查状态
    status = detector.get_status()
    print(f"  ✓ 检测器状态: {status.value}")

    stats = detector.get_statistics()
    print(f"  ✓ 潜在死锁: {stats['potential_deadlocks']}")

    print("\n✅ 测试5通过：死锁检测功能正常")
    return True


def test_6_unified_manager():
    """测试6：统一管理器"""
    print("\n" + "=" * 60)
    print("测试6：统一管理器")
    print("=" * 60)

    config = TaskTimeoutConfig(default_timeout_seconds=2.0)
    manager = create_timeout_deadlock_manager(config)

    manager.start()
    print("  ✓ 管理器已启动")

    # 注册任务
    manager.register_task("unified_task", timeout_seconds=3.0)
    print("  ✓ 任务已注册")

    # 获取资源
    acquired = manager.acquire_resource("unified_task", "resource_x")
    assert acquired
    print("  ✓ 资源已获取")

    # 完成任务
    manager.complete_task("unified_task")
    print("  ✓ 任务已完成")

    # 获取统计
    all_stats = manager.get_all_statistics()
    assert "timeout" in all_stats
    assert "deadlock" in all_stats
    print(f"  ✓ 统计信息: timeout={all_stats['timeout']['total_tasks']}, "
          f"deadlock={all_stats['deadlock']['total_acquires']}")

    manager.stop()
    print("\n✅ 测试6通过：统一管理器功能正常")
    return True


def run_all_tests():
    """运行所有验收测试"""
    print("\n" + "=" * 60)
    print("第74阶段验收测试：任务超时管理与死锁检测")
    print("=" * 60)

    tests = [
        test_1_timeout_manager_basic,
        test_2_timeout_detection,
        test_3_timeout_callback,
        test_4_deadlock_detector_basic,
        test_5_deadlock_detection,
        test_6_unified_manager
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
        print("\n🎉 所有验收测试通过！第74阶段完成！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
