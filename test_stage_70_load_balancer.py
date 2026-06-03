"""
第70阶段验收测试：负载均衡与资源分配

验证5个维度：
1. 基础负载均衡功能
2. 多种策略验证
3. 资源分配管理
4. 健康状态管理
5. 集成调度器
"""

import sys
import time
from src.first_principles_agent import (
    LoadBalancer, ResourceAllocator, LoadBalancedScheduler,
    ResourceType, LoadBalanceStrategy, ResourceCapacity,
    ResourceUsage, WorkerNode, TaskResourceRequirement,
    create_load_balancer, create_resource_capacity, create_task_requirement
)


def test_1_basic_load_balancer():
    """测试1：基础负载均衡功能"""
    print("=" * 60)
    print("测试1：基础负载均衡功能")
    print("=" * 60)
    
    lb = LoadBalancer(LoadBalanceStrategy.ROUND_ROBIN)
    
    # 创建节点
    node1 = WorkerNode(
        node_id="node-1",
        name="Worker Node 1",
        capacity=ResourceCapacity(cpu_cores=8.0, memory_gb=32.0)
    )
    node2 = WorkerNode(
        node_id="node-2",
        name="Worker Node 2",
        capacity=ResourceCapacity(cpu_cores=8.0, memory_gb=32.0)
    )
    
    lb.register_node(node1)
    lb.register_node(node2)
    
    print(f"✓ 注册了 {len(lb.nodes)} 个节点")
    
    # 检查健康节点
    healthy_nodes = lb.get_healthy_nodes()
    assert len(healthy_nodes) == 2, "应该有2个健康节点"
    print(f"✓ 健康节点数：{len(healthy_nodes)}")
    
    # 验证统计信息
    stats = lb.get_statistics()
    assert stats["total_nodes"] == 2
    assert stats["healthy_nodes"] == 2
    print("✓ 统计信息正确")
    
    print("\n✅ 测试1通过：基础负载均衡功能正常\n")
    return True


def test_2_load_balance_strategies():
    """测试2：多种负载均衡策略"""
    print("=" * 60)
    print("测试2：多种负载均衡策略")
    print("=" * 60)
    
    # 测试轮询策略
    print("\n--- 测试轮询策略 ---")
    lb_rr = LoadBalancer(LoadBalanceStrategy.ROUND_ROBIN)
    
    node1 = WorkerNode(node_id="node-1", name="Node 1")
    node2 = WorkerNode(node_id="node-2", name="Node 2")
    node3 = WorkerNode(node_id="node-3", name="Node 3")
    
    lb_rr.register_node(node1)
    lb_rr.register_node(node2)
    lb_rr.register_node(node3)
    
    req = create_task_requirement("test-task", cpu_cores=0.1, memory_gb=0.1)
    
    selected = []
    for _ in range(6):
        node = lb_rr.select_node(req)
        selected.append(node.node_id)
    
    print(f"  选择顺序：{selected}")
    # 验证轮询正确性
    assert selected[0] == "node-1"
    assert selected[1] == "node-2"
    assert selected[2] == "node-3"
    print("✓ 轮询策略正确")
    
    # 测试最少连接策略
    print("\n--- 测试最少连接策略 ---")
    lb_lc = LoadBalancer(LoadBalanceStrategy.LEAST_CONNECTIONS)
    lb_lc.register_node(node1)
    lb_lc.register_node(node2)
    lb_lc.register_node(node3)
    
    # 模拟node1有更多任务
    node1.active_tasks = 5
    node2.active_tasks = 2
    node3.active_tasks = 0
    
    selected_node = lb_lc.select_node(req)
    assert selected_node.node_id == "node-3", "应该选择任务最少的节点"
    print(f"✓ 选择了最少连接节点：{selected_node.name}")
    
    # 测试最少资源使用策略
    print("\n--- 测试最少资源使用策略 ---")
    lb_lru = LoadBalancer(LoadBalanceStrategy.LEAST_RESOURCE_USAGE)
    lb_lru.register_node(node1)
    lb_lru.register_node(node2)
    lb_lru.register_node(node3)
    
    # 模拟不同负载
    node1.current_usage = ResourceUsage(cpu_usage=6.0, memory_used_gb=24.0)
    node2.current_usage = ResourceUsage(cpu_usage=3.0, memory_used_gb=12.0)
    node3.current_usage = ResourceUsage(cpu_usage=1.0, memory_used_gb=4.0)
    
    selected_node = lb_lru.select_node(req)
    assert selected_node.node_id == "node-3", "应该选择资源使用最少的节点"
    print(f"✓ 选择了最少资源使用节点：{selected_node.name}")
    
    print("\n✅ 测试2通过：多种负载均衡策略验证成功\n")
    return True


def test_3_resource_allocation():
    """测试3：资源分配管理"""
    print("=" * 60)
    print("测试3：资源分配管理")
    print("=" * 60)
    
    lb = LoadBalancer(LoadBalanceStrategy.LEAST_RESOURCE_USAGE)
    
    node1 = WorkerNode(
        node_id="node-1",
        name="Compute Node",
        capacity=ResourceCapacity(cpu_cores=8.0, memory_gb=32.0)
    )
    node2 = WorkerNode(
        node_id="node-2",
        name="Memory Node",
        capacity=ResourceCapacity(cpu_cores=4.0, memory_gb=64.0)
    )
    
    lb.register_node(node1)
    lb.register_node(node2)
    
    allocator = ResourceAllocator(lb)
    
    # 创建任务需求
    req1 = create_task_requirement("task-1", cpu_cores=2.0, memory_gb=8.0)
    req2 = create_task_requirement("task-2", cpu_cores=1.0, memory_gb=16.0)
    
    # 分配第一个任务
    decision1 = allocator.allocate(req1)
    assert decision1.success, "分配应该成功"
    print(f"✓ 任务 task-1 分配到节点：{decision1.node_id}")
    
    # 分配第二个任务（内存需求大，应选node2）
    decision2 = allocator.allocate(req2)
    assert decision2.success, "分配应该成功"
    print(f"✓ 任务 task-2 分配到节点：{decision2.node_id}")
    
    # 验证统计信息
    stats = allocator.get_statistics()
    assert stats["total_allocations"] == 2
    assert stats["success_rate"] == 1.0
    print(f"✓ 分配统计：总数={stats['total_allocations']}, 成功率={stats['success_rate']}")
    
    # 释放资源
    released = allocator.release("task-1")
    assert released, "释放应该成功"
    print("✓ 资源释放成功")
    
    print("\n✅ 测试3通过：资源分配管理功能正常\n")
    return True


def test_4_health_management():
    """测试4：健康状态管理"""
    print("=" * 60)
    print("测试4：健康状态管理")
    print("=" * 60)
    
    lb = LoadBalancer()
    
    node1 = WorkerNode(node_id="node-1", name="Healthy Node")
    node2 = WorkerNode(node_id="node-2", name="Unhealthy Node")
    
    lb.register_node(node1)
    lb.register_node(node2)
    
    # 初始都健康
    assert len(lb.get_healthy_nodes()) == 2
    
    # 标记node2为不健康
    lb.update_node_health("node-2", False)
    healthy_nodes = lb.get_healthy_nodes()
    assert len(healthy_nodes) == 1
    assert healthy_nodes[0].node_id == "node-1"
    print("✓ 不健康节点被正确过滤")
    
    # 更新资源使用
    new_usage = ResourceUsage(cpu_usage=2.0, memory_used_gb=8.0)
    updated = lb.update_node_usage("node-1", new_usage)
    assert updated, "更新应该成功"
    assert node1.current_usage.cpu_usage == 2.0
    print("✓ 资源使用更新成功")
    
    # 不健康节点不应被选择
    req = create_task_requirement("test-task", cpu_cores=1.0, memory_gb=2.0)
    selected = lb.select_node(req)
    assert selected and selected.node_id == "node-1"
    print("✓ 只有健康节点被选择")
    
    print("\n✅ 测试4通过：健康状态管理功能正常\n")
    return True


def test_5_integrated_scheduler():
    """测试5：集成调度器"""
    print("=" * 60)
    print("测试5：集成负载均衡调度器")
    print("=" * 60)
    
    scheduler = LoadBalancedScheduler(LoadBalanceStrategy.LEAST_RESOURCE_USAGE)
    
    # 添加工作节点
    capacity1 = create_resource_capacity(cpu_cores=16, memory_gb=64)
    capacity2 = create_resource_capacity(cpu_cores=8, memory_gb=32)
    
    scheduler.add_worker_node("worker-1", "High Performance Node", capacity1, weight=2.0)
    scheduler.add_worker_node("worker-2", "Standard Node", capacity2, weight=1.0)
    
    print(f"✓ 添加了 2 个工作节点")
    
    # 提交多个任务
    for i in range(5):
        req = create_task_requirement(
            f"job-{i}",
            cpu_cores=2.0,
            memory_gb=4.0,
            priority=8.0 if i == 0 else 5.0
        )
        decision = scheduler.submit_task(req)
        assert decision.success
        print(f"  任务 job-{i} 分配到：{decision.node_id}")
    
    # 获取系统统计
    stats = scheduler.get_system_statistics()
    print(f"\n✓ 系统统计：")
    print(f"  - 总节点数：{stats['load_balancer']['total_nodes']}")
    print(f"  - 健康节点：{stats['load_balancer']['healthy_nodes']}")
    print(f"  - 活动任务：{stats['load_balancer']['active_tasks']}")
    print(f"  - 平均负载：{stats['load_balancer']['average_load']:.2f}")
    print(f"  - 分配成功率：{stats['resource_allocator']['success_rate']:.0%}")
    
    # 完成任务
    for i in range(3):
        completed = scheduler.complete_task(f"job-{i}")
        assert completed
    
    print(f"\n✓ 完成了 3 个任务，资源已释放")
    
    print("\n✅ 测试5通过：集成调度器功能正常\n")
    return True


def run_all_tests():
    """运行所有验收测试"""
    print("\n" + "=" * 60)
    print("第70阶段验收测试：负载均衡与资源分配")
    print("=" * 60 + "\n")
    
    tests = [
        test_1_basic_load_balancer,
        test_2_load_balance_strategies,
        test_3_resource_allocation,
        test_4_health_management,
        test_5_integrated_scheduler
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
        print("\n🎉 所有验收测试通过！第70阶段完成！\n")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
