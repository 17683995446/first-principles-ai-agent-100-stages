"""
第64阶段验收测试：资源管理与调度策略增强
测试维度：
1. 加权任务队列基础功能
2. 加权调度算法验证
3. 任务超时控制
4. 资源配额管理
5. 增强调度器集成测试
"""

import time
import sys
from pathlib import Path

# 添加src目录到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from first_principles_agent.enhanced_scheduler import (
    WeightedTaskQueue, EnhancedTaskScheduler, TaskConfig,
    ResourceQuota, create_task_config
)
from first_principles_agent.task_scheduler import TaskPriority
from first_principles_agent.task_model import Task, TaskQuartet


def print_header(title: str):
    """打印测试标题"""
    print("\n" + "=" * 80)
    print(f"🎯 {title}")
    print("=" * 80)


def print_pass(name: str, detail: str = ""):
    """打印通过"""
    message = f"✅ {name}"
    if detail:
        message += f" - {detail}"
    print(message)


def print_fail(name: str, detail: str = ""):
    """打印失败"""
    message = f"❌ {name}"
    if detail:
        message += f" - {detail}"
    print(message)


def create_test_task(task_id: str, target: str) -> Task:
    """创建测试任务的辅助函数"""
    quartet = TaskQuartet(target=target)
    return Task(task_id=task_id, quartet=quartet)


def test_1_weighted_queue_basics():
    """测试1：加权任务队列基础功能"""
    print_header("测试1：加权任务队列基础功能")
    
    try:
        queue = WeightedTaskQueue(max_concurrent=2)
        
        # 创建和入队任务
        task1 = create_test_task("wq1", "Weighted Queue Test 1")
        task2 = create_test_task("wq2", "Weighted Queue Test 2")
        
        config1 = create_task_config(weight=1)
        config2 = create_task_config(weight=3)
        
        queue.enqueue(task1, TaskPriority.NORMAL, config1)
        queue.enqueue(task2, TaskPriority.NORMAL, config2)
        
        print_pass("任务入队（带配置）")
        
        # 验证统计
        stats = queue.get_extended_stats()
        assert "used_resources" in stats, "应包含资源使用信息"
        assert "type_stats" in stats, "应包含类型统计"
        print_pass("扩展统计信息")
        
        # 出队任务
        dequeued = []
        while True:
            task = queue.dequeue()
            if not task:
                break
            dequeued.append(task.task.id)
            queue.complete_task(task.task.id, result={"ok": True})
        
        assert len(dequeued) == 2, "应出队2个任务"
        print_pass(f"出队任务数: {len(dequeued)}")
        
        print("\n✅ 测试1通过")
        return True
        
    except Exception as e:
        print_fail("测试1异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_2_weighted_scheduling():
    """测试2：加权调度算法验证"""
    print_header("测试2：加权调度算法验证")
    
    try:
        # 禁用优先级，只测试权重
        queue = WeightedTaskQueue(max_concurrent=1, enable_priority=False)
        
        # 创建不同权重的任务
        task_low = create_test_task("low", "Low Weight")
        task_high = create_test_task("high", "High Weight")
        
        config_low = create_task_config(weight=1)
        config_high = create_task_config(weight=10)
        
        # 测试多次选择
        selected_high = 0
        total_rounds = 200
        
        for _ in range(total_rounds):
            # 每次都重新入队
            queue.enqueue(task_low, TaskPriority.NORMAL, config_low)
            queue.enqueue(task_high, TaskPriority.NORMAL, config_high)
            
            # 直接调用加权选择
            with queue._lock:
                selected_idx = queue._weighted_select()
                if selected_idx is not None:
                    selected_task = queue.pending_queue[selected_idx]
                    if selected_task.task.id == "high":
                        selected_high += 1
            
            # 清空队列
            queue.clear()
        
        # 高权重任务应该被选中更多次
        high_ratio = selected_high / total_rounds
        print(f"DEBUG: 高权重选中 {selected_high}/{total_rounds} = {high_ratio:.2%}")
        
        # 期望值约为 10/(10+1) ≈ 90.9%
        # 接受 > 60% 以适应随机波动
        assert high_ratio > 0.6, f"高权重任务选中率应大于60%，实际: {high_ratio:.2%}"
        
        print_pass(f"高权重任务选中率: {high_ratio:.2%} (期望: ~90%)")
        
        print("\n✅ 测试2通过")
        return True
        
    except Exception as e:
        print_fail("测试2异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_3_timeout_control():
    """测试3：任务超时控制"""
    print_header("测试3：任务超时控制")
    
    try:
        timeout_occurred = []
        
        def on_timeout(task_id: str):
            timeout_occurred.append(task_id)
        
        def on_error(task_id: str, error: str):
            pass
        
        scheduler = EnhancedTaskScheduler(
            max_concurrent=1,
            on_task_timeout=on_timeout,
            on_task_error=on_error
        )
        
        # 注册一个执行时间较长的执行器
        def slow_executor(task: Task):
            time.sleep(2.0)  # 执行2秒
            return {"status": "done"}
        
        scheduler.register_executor("slow", slow_executor)
        
        # 提交一个超时任务（超时时间0.5秒）
        task = create_test_task("timeout_task", "Timeout Test")
        config = create_task_config(timeout_seconds=0.5, task_type="slow")
        
        scheduler.submit_task(task, TaskPriority.NORMAL, config)
        print_pass("超时任务提交")
        
        # 启动调度器
        scheduler.start()
        print_pass("调度器启动")
        
        # 等待超时发生
        wait_start = time.time()
        while len(timeout_occurred) == 0 and time.time() - wait_start < 5.0:
            time.sleep(0.1)
        
        # 停止调度器
        scheduler.stop()
        print_pass("调度器停止")
        
        # 验证超时发生
        assert len(timeout_occurred) > 0, "应检测到任务超时"
        assert timeout_occurred[0] == "timeout_task", "超时任务ID应匹配"
        print_pass("超时控制生效")
        
        print("\n✅ 测试3通过")
        return True
        
    except Exception as e:
        print_fail("测试3异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_4_resource_quota():
    """测试4：资源配额管理"""
    print_header("测试4：资源配额管理")
    
    try:
        # 创建带资源配额的队列
        resource_quota = ResourceQuota(
            cpu=4.0,
            memory_mb=2048,
            io_weight=10,
            network_mbps=1000
        )
        
        queue = WeightedTaskQueue(
            max_concurrent=3,
            resource_quota=resource_quota
        )
        
        # 验证统计信息包含资源数据
        stats = queue.get_extended_stats()
        
        assert stats["total_resources"]["cpu"] == 4.0, "CPU配额应正确"
        assert stats["total_resources"]["memory_mb"] == 2048, "内存配额应正确"
        print_pass("资源配额设置")
        
        # 创建带资源配置的任务
        task = create_test_task("resource_task", "Resource Task")
        config = create_task_config(cpu=0.5, memory_mb=256)
        queue.enqueue(task, TaskPriority.NORMAL, config)
        print_pass("带资源配置的任务入队")
        
        print("\n✅ 测试4通过")
        return True
        
    except Exception as e:
        print_fail("测试4异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_5_enhanced_scheduler_integration():
    """测试5：增强调度器集成测试"""
    print_header("测试5：增强调度器集成测试")
    
    try:
        completed = []
        errors = []
        
        def on_complete(task_id: str, result: dict):
            completed.append(task_id)
        
        def on_error(task_id: str, error: str):
            errors.append(task_id)
        
        scheduler = EnhancedTaskScheduler(
            max_concurrent=2,
            on_task_complete=on_complete,
            on_task_error=on_error
        )
        
        # 注册执行器
        def fast_executor(task: Task):
            time.sleep(0.1)
            return {"status": "fast"}
        
        scheduler.register_executor("fast", fast_executor)
        
        # 提交多种配置的任务
        tasks = [
            ("task1", create_task_config(weight=1, task_type="fast")),
            ("task2", create_task_config(weight=2, task_type="fast")),
            ("task3", create_task_config(weight=3, task_type="fast")),
            ("task4", create_task_config(weight=1, task_type="fast")),
            ("task5", create_task_config(weight=5, task_type="fast")),
        ]
        
        for task_id, config in tasks:
            task = create_test_task(task_id, f"Task {task_id}")
            scheduler.submit_task(task, TaskPriority.NORMAL, config)
        
        print_pass("批量任务提交")
        
        # 启动调度器
        scheduler.start()
        print_pass("调度器启动")
        
        # 等待完成
        wait_start = time.time()
        while len(completed) < len(tasks) and time.time() - wait_start < 10.0:
            time.sleep(0.1)
        
        # 停止调度器
        scheduler.stop()
        print_pass("调度器停止")
        
        # 验证
        assert len(completed) == len(tasks), f"应完成{len(tasks)}个任务"
        assert len(errors) == 0, "不应有错误"
        print_pass(f"所有任务完成: {len(completed)}/{len(tasks)}")
        
        # 验证增强统计
        stats = scheduler.get_enhanced_stats()
        assert "type_stats" in stats, "应包含类型统计"
        print_pass("增强统计正确")
        
        print("\n✅ 测试5通过")
        return True
        
    except Exception as e:
        print_fail("测试5异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def main():
    print_header("第64阶段：资源管理与调度策略增强")
    print("验收标准：加权调度、超时控制、资源配额")
    
    all_passed = True
    tests = [
        test_1_weighted_queue_basics,
        test_2_weighted_scheduling,
        test_3_timeout_control,
        test_4_resource_quota,
        test_5_enhanced_scheduler_integration
    ]
    
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 80)
    print("第64阶段验收结果汇总")
    print("=" * 80)
    
    if all_passed:
        print("\n🎉 第64阶段验收通过！")
        print("资源管理与调度策略增强验证通过！")
    else:
        print("\n❌ 第64阶段验收失败")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
