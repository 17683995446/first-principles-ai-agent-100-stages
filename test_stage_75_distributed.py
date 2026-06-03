"""
第75阶段验收测试：分布式协调与基础共识
"""

import sys
import time
import threading
from src.first_principles_agent import (
    create_heartbeat_manager,
    create_distributed_lock_manager,
    create_configuration_center,
    create_distributed_coordinator,
    NodeStatus,
    ConsensusStatus
)


def test_1_heartbeat_manager_basic():
    """测试1：心跳管理器基础功能"""
    print("\n" + "=" * 60)
    print("测试1：心跳管理器基础功能")
    print("=" * 60)

    manager = create_heartbeat_manager("node_0", heartbeat_interval=1.0, timeout_threshold=3.0)

    manager.register_node("node_1", "192.168.1.101", 8080, {"role": "worker"})
    manager.register_node("node_2", "192.168.1.102", 8080, {"role": "controller"})
    print("  ✓ 注册2个节点")

    all_nodes = manager.get_all_nodes()
    assert len(all_nodes) == 2
    print(f"  ✓ 总节点数: {len(all_nodes)}")

    node1 = manager.get_node("node_1")
    assert node1 is not None
    assert node1.address == "192.168.1.101"
    assert node1.metadata["role"] == "worker"
    print(f"  ✓ 节点1地址: {node1.address}, 角色: {node1.metadata['role']}")

    print("\n✅ 测试1通过：心跳管理器基础功能正常")
    return True


def test_2_heartbeat_monitoring():
    """测试2：心跳监控与状态变化"""
    print("\n" + "=" * 60)
    print("测试2：心跳监控与状态变化")
    print("=" * 60)

    callback_events = []

    def heartbeat_callback(node_id: str, status: NodeStatus):
        callback_events.append((node_id, status.value))
        print(f"  ✓ 回调触发: {node_id} -> {status.value}")

    manager = create_heartbeat_manager("node_0", heartbeat_interval=0.5, timeout_threshold=1.5)
    manager.add_heartbeat_callback(heartbeat_callback)
    manager.start()

    node = manager.register_node("test_node", "127.0.0.1", 9000)
    print("  ✓ 注册测试节点")

    node.status = NodeStatus.ACTIVE
    manager.record_heartbeat("test_node")
    print("  ✓ 设置为活跃并记录心跳")

    active_nodes = manager.get_active_nodes()
    assert len(active_nodes) >= 1
    print(f"  ✓ 活跃节点数: {len(active_nodes)}")

    manager.stop()
    print("\n✅ 测试2通过：心跳监控功能正常")
    return True


def test_3_distributed_lock_basic():
    """测试3：分布式锁基础功能"""
    print("\n" + "=" * 60)
    print("测试3：分布式锁基础功能")
    print("=" * 60)

    lock_manager = create_distributed_lock_manager()

    lock = lock_manager.get_lock("resource_a")
    assert not lock.is_held()
    print("  ✓ 初始锁未被持有")

    assert lock.acquire("client_1", timeout_seconds=1.0)
    assert lock.is_held()
    assert lock.get_holder() == "client_1"
    print("  ✓ client_1 获取锁成功")

    assert not lock.acquire("client_2", timeout_seconds=0.5)
    print("  ✓ client_2 尝试获取锁被拒绝")

    assert lock.release("client_1")
    assert not lock.is_held()
    print("  ✓ client_1 释放锁")

    assert lock.acquire("client_2", timeout_seconds=1.0)
    print("  ✓ client_2 现在可以获取锁")

    active_locks = lock_manager.get_active_locks()
    assert "resource_a" in active_locks
    print(f"  ✓ 活跃锁: {active_locks}")

    print("\n✅ 测试3通过：分布式锁基础功能正常")
    return True


def test_4_configuration_center():
    """测试4：配置中心功能"""
    print("\n" + "=" * 60)
    print("测试4：配置中心功能")
    print("=" * 60)

    config_center = create_configuration_center()

    config_center.set("max_workers", "10", created_by="admin")
    config_center.set("timeout", "30", created_by="system")
    print("  ✓ 设置2个配置项")

    value = config_center.get("max_workers")
    assert value == "10"
    print(f"  ✓ 获取配置: max_workers={value}")

    value_with_version = config_center.get_with_version("timeout")
    assert value_with_version is not None
    assert value_with_version[0] == "30"
    assert value_with_version[1] == 1
    print(f"  ✓ 带版本获取: timeout={value_with_version[0]}, version={value_with_version[1]}")

    config_center.set("timeout", "60")
    value_with_version = config_center.get_with_version("timeout")
    assert value_with_version[0] == "60"
    assert value_with_version[1] == 2
    print("  ✓ 更新配置，版本变为2")

    all_configs = config_center.get_all()
    assert len(all_configs) == 2
    print(f"  ✓ 总配置数: {len(all_configs)}")

    print("\n✅ 测试4通过：配置中心功能正常")
    return True


def test_5_config_watch():
    """测试5：配置监听功能"""
    print("\n" + "=" * 60)
    print("测试5：配置监听功能")
    print("=" * 60)

    config_center = create_configuration_center()
    watch_events = []

    def watch_callback(key: str, value: str, version: int):
        watch_events.append((key, value, version))
        print(f"  ✓ 监听事件: {key}={value} (v{version})")

    config_center.watch("log_level", watch_callback)
    print("  ✓ 注册配置监听")

    config_center.set("log_level", "INFO", created_by="admin")
    time.sleep(0.1)
    assert len(watch_events) == 1

    config_center.set("log_level", "DEBUG")
    time.sleep(0.1)
    assert len(watch_events) == 2

    config_center.delete("log_level")
    time.sleep(0.1)
    assert len(watch_events) == 3

    print("\n✅ 测试5通过：配置监听功能正常")
    return True


def test_6_distributed_coordinator():
    """测试6：分布式协调器"""
    print("\n" + "=" * 60)
    print("测试6：分布式协调器")
    print("=" * 60)

    coordinator = create_distributed_coordinator(
        node_id="coordinator_0",
        heartbeat_interval=1.0,
        timeout_threshold=5.0
    )

    print(f"  ✓ 创建协调器: node_id={coordinator.node_id}")

    coordinator.start()
    print("  ✓ 启动协调器")

    coordinator.heartbeat_manager.register_node("coord_node_1", "10.0.0.1", 8080)
    coordinator.heartbeat_manager.register_node("coord_node_2", "10.0.0.2", 8080)
    print("  ✓ 注册2个协调节点")

    coordinator.config_center.set("distributed_mode", "active")
    assert coordinator.config_center.get("distributed_mode") == "active"
    print("  ✓ 设置协调器配置")

    assert coordinator.lock_manager.try_acquire("coord_lock", "coordinator_0")
    print("  ✓ 获取协调锁")

    status = coordinator.get_status()
    assert status["node_id"] == coordinator.node_id
    assert status["total_nodes"] == 2
    assert status["consensus_status"] == ConsensusStatus.FOLLOWER.value
    print(f"  ✓ 协调器状态: {status}")

    coordinator.stop()
    print("  ✓ 停止协调器")

    print("\n✅ 测试6通过：分布式协调器功能正常")
    return True


def run_all_tests():
    """运行所有验收测试"""
    print("\n" + "=" * 60)
    print("第75阶段验收测试：分布式协调与基础共识")
    print("=" * 60)

    tests = [
        test_1_heartbeat_manager_basic,
        test_2_heartbeat_monitoring,
        test_3_distributed_lock_basic,
        test_4_configuration_center,
        test_5_config_watch,
        test_6_distributed_coordinator
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
        print("\n🎉 所有验收测试通过！第75阶段完成！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
