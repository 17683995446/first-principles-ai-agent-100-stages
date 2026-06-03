"""
第63阶段验收测试：支持多任务并发调度基础能力
测试维度：
1. 任务队列基本功能
2. 优先级调度
3. 并发控制
4. 任务状态追踪
5. 调度器集成测试
"""

import time
import sys
from pathlib import Path

# 添加src目录到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from first_principles_agent.task_scheduler import (
    TaskQueue, TaskScheduler, TaskPriority, TaskQueueStatus
)
from first_principles_agent.task_model import Task, TaskStatus, TaskQuartet


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


def test_1_task_queue_basics():
    """测试1：任务队列基本功能"""
    print_header("测试1：任务队列基本功能")
    
    try:
        queue = TaskQueue(max_concurrent=2)
        
        # 创建测试任务
        task1 = create_test_task("task1", "Test 1")
        task2 = create_test_task("task2", "Test 2")
        
        # 测试入队
        id1 = queue.enqueue(task1, TaskPriority.NORMAL)
        id2 = queue.enqueue(task2, TaskPriority.NORMAL)
        
        assert id1 == "task1", "任务ID应该匹配"
        assert id2 == "task2", "任务ID应该匹配"
        print_pass("任务入队")
        
        # 测试统计
        stats = queue.get_stats()
        assert stats["total_enqueued"] == 2, "入队数量应该为2"
        assert stats["total_pending"] == 2, "待执行数量应该为2"
        print_pass("队列统计")
        
        # 测试出队
        qt1 = queue.dequeue()
        assert qt1 is not None, "应该能获取任务"
        assert qt1.task.id == "task1", "任务ID应该匹配"
        print_pass("任务出队")
        
        # 测试完成
        queue.complete_task("task1", result={"ok": True})
        stats = queue.get_stats()
        assert stats["total_completed"] == 1, "完成数量应该为1"
        assert stats["total_pending"] == 1, "待执行数量应该为1"
        print_pass("任务完成标记")
        
        # 测试获取任务
        task_info = queue.get_task("task1")
        assert task_info is not None, "应该能找到任务"
        assert task_info._get_status() == "completed", "状态应该为completed"
        print_pass("任务信息获取")
        
        print("\n✅ 测试1通过")
        return True
        
    except Exception as e:
        print_fail("测试1异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_2_priority_scheduling():
    """测试2：优先级调度"""
    print_header("测试2：优先级调度")
    
    try:
        queue = TaskQueue(max_concurrent=1, enable_priority=True)
        
        # 按低到高优先级入队
        queue.enqueue(create_test_task("low1", "Low 1"), TaskPriority.LOW)
        queue.enqueue(create_test_task("normal1", "Normal 1"), TaskPriority.NORMAL)
        queue.enqueue(create_test_task("high1", "High 1"), TaskPriority.HIGH)
        queue.enqueue(create_test_task("critical1", "Critical 1"), TaskPriority.CRITICAL)
        
        # 验证出队顺序：CRITICAL → HIGH → NORMAL → LOW
        order = []
        while True:
            task = queue.dequeue()
            if task is None:
                break
            order.append(task.task.id)
            queue.complete_task(task.task.id)
        
        expected_order = ["critical1", "high1", "normal1", "low1"]
        assert order == expected_order, f"期望顺序 {expected_order}，实际 {order}"
        print_pass(f"优先级调度顺序: {order}")
        
        print("\n✅ 测试2通过")
        return True
        
    except Exception as e:
        print_fail("测试2异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_3_concurrency_control():
    """测试3：并发控制"""
    print_header("测试3：并发控制")
    
    try:
        max_concurrent = 2
        queue = TaskQueue(max_concurrent=max_concurrent)
        
        # 入队多个任务
        for i in range(5):
            queue.enqueue(create_test_task(f"task{i}", f"Task {i}"))
        
        # 出队达到最大并发
        running = []
        for i in range(max_concurrent + 1):
            task = queue.dequeue()
            if task:
                running.append(task)
        
        assert len(running) == max_concurrent, f"并发数应该为{max_concurrent}"
        print_pass(f"并发控制 - 限制在{max_concurrent}个任务")
        
        stats = queue.get_stats()
        assert stats["total_running"] == max_concurrent, f"运行中数量应该为{max_concurrent}"
        assert stats["total_pending"] == 5 - max_concurrent, "待执行数量应该正确"
        print_pass("并发状态统计")
        
        # 完成一个任务，应该能再取一个
        queue.complete_task(running[0].task.id)
        next_task = queue.dequeue()
        assert next_task is not None, "应该能获取下一个任务"
        print_pass("任务完成后调度下一个")
        
        print("\n✅ 测试3通过")
        return True
        
    except Exception as e:
        print_fail("测试3异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_4_task_status_tracking():
    """测试4：任务状态追踪"""
    print_header("测试4：任务状态追踪")
    
    try:
        queue = TaskQueue()
        
        task = create_test_task("status_test", "Status Test")
        queue.enqueue(task)
        
        # 检查pending状态
        qt = queue.get_task("status_test")
        assert qt._get_status() == "pending", "初始状态应该为pending"
        print_pass("初始状态 - pending")
        
        # 检查running状态
        qt = queue.dequeue()
        assert qt._get_status() == "running", "开始后状态应该为running"
        print_pass("运行状态 - running")
        
        # 检查completed状态
        queue.complete_task("status_test", result={"done": True})
        qt = queue.get_task("status_test")
        assert qt._get_status() == "completed", "完成后状态应该为completed"
        print_pass("完成状态 - completed")
        
        # 检查to_dict
        info = qt.to_dict()
        assert "task_id" in info, "应该包含task_id"
        assert "status" in info, "应该包含status"
        assert "result" in info, "应该包含result"
        print_pass("任务信息序列化")
        
        print("\n✅ 测试4通过")
        return True
        
    except Exception as e:
        print_fail("测试4异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_5_scheduler_integration():
    """测试5：调度器集成测试"""
    print_header("测试5：调度器集成测试")
    
    try:
        completed_ids = []
        errors = []
        
        def on_complete(task_id: str, result: dict):
            completed_ids.append(task_id)
        
        def on_error(task_id: str, error: str):
            errors.append((task_id, error))
        
        scheduler = TaskScheduler(
            max_concurrent=2,
            on_task_complete=on_complete,
            on_task_error=on_error
        )
        
        # 注册执行器
        def sample_executor(task: Task):
            time.sleep(0.2)  # 模拟执行
            return {"task_id": task.id, "message": "Executed"}
        
        scheduler.register_executor("default", sample_executor)
        
        # 提交任务
        task_ids = []
        for i in range(5):
            task = create_test_task(f"sched_task{i}", f"Schedule {i}")
            tid = scheduler.submit_task(task, TaskPriority.NORMAL)
            task_ids.append(tid)
        
        print_pass("任务提交")
        
        # 启动调度器
        scheduler.start()
        print_pass("调度器启动")
        
        # 等待任务完成
        timeout = 5.0
        start_time = time.time()
        while len(completed_ids) < 5 and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # 停止调度器
        scheduler.stop()
        print_pass("调度器停止")
        
        # 验证
        assert len(completed_ids) == 5, f"应该完成5个任务，实际{len(completed_ids)}"
        assert set(completed_ids) == set(task_ids), "应该完成所有提交的任务"
        assert len(errors) == 0, f"不应该有错误，实际{len(errors)}"
        print_pass("所有任务完成")
        
        # 验证统计
        stats = scheduler.get_stats()
        assert stats["total_completed"] == 5, "完成数应该为5"
        assert stats["total_enqueued"] == 5, "入队数应该为5"
        print_pass("调度统计正确")
        
        print("\n✅ 测试5通过")
        return True
        
    except Exception as e:
        print_fail("测试5异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def main():
    print_header("第63阶段：支持多任务并发调度基础能力")
    print("验收标准：多任务并发调度基础能力")
    
    all_passed = True
    tests = [
        test_1_task_queue_basics,
        test_2_priority_scheduling,
        test_3_concurrency_control,
        test_4_task_status_tracking,
        test_5_scheduler_integration
    ]
    
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 80)
    print("第63阶段验收结果汇总")
    print("=" * 80)
    
    if all_passed:
        print("\n🎉 第63阶段验收通过！")
        print("多任务并发调度基础能力验证通过！")
    else:
        print("\n❌ 第63阶段验收失败")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
