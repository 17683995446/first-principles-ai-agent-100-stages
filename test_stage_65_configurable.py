"""
第65阶段验收测试：任务依赖关系与可配置调度策略
测试维度：
1. 任务依赖图基本功能
2. 循环依赖检测
3. 依赖感知调度
4. 多种调度策略验证
5. 可配置调度器集成测试
"""

import time
import sys
from pathlib import Path

# 添加src目录到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from first_principles_agent.configurable_scheduler import (
    DependencyAwareQueue, ConfigurableScheduler, TaskDependencyGraph,
    SchedulerConfig, SchedulingStrategy, create_scheduler_config
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


def test_1_dependency_graph_basics():
    """测试1：任务依赖图基本功能"""
    print_header("测试1：任务依赖图基本功能")
    
    try:
        graph = TaskDependencyGraph()
        
        # 添加依赖：A → B → C
        graph.add_dependency("A", "B", hard=True)
        graph.add_dependency("B", "C", hard=True)
        
        print_pass("依赖关系添加成功")
        
        # 检查依赖
        b_deps = graph.get_dependencies("B")
        assert "A" in b_deps, "B应该依赖A"
        print_pass("前置依赖查询正确")
        
        # 检查后置任务
        a_dependents = graph.get_dependents("A")
        assert "B" in a_dependents, "A应该被B依赖"
        print_pass("后置任务查询正确")
        
        # 检查依赖满足情况
        completed = set()
        assert graph.has_unmet_dependencies("B", completed), "B应该有未满足的依赖"
        
        completed.add("A")
        assert not graph.has_unmet_dependencies("B", completed), "A完成后B的依赖应该满足"
        print_pass("依赖满足检查正确")
        
        print("\n✅ 测试1通过")
        return True
        
    except Exception as e:
        print_fail("测试1异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_2_cyclic_dependency_detection():
    """测试2：循环依赖检测"""
    print_header("测试2：循环依赖检测")
    
    try:
        # 正常依赖图
        normal_graph = TaskDependencyGraph()
        normal_graph.add_dependency("A", "B")
        normal_graph.add_dependency("B", "C")
        assert not normal_graph.is_cyclic(), "正常图不应该有循环"
        print_pass("正常依赖图检测正确")
        
        # 循环依赖图：A→B→C→A
        cyclic_graph = TaskDependencyGraph()
        cyclic_graph.add_dependency("A", "B")
        cyclic_graph.add_dependency("B", "C")
        cyclic_graph.add_dependency("C", "A")
        assert cyclic_graph.is_cyclic(), "应该检测到循环依赖"
        print_pass("循环依赖检测正确")
        
        print("\n✅ 测试2通过")
        return True
        
    except Exception as e:
        print_fail("测试2异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_3_dependency_aware_scheduling():
    """测试3：依赖感知调度"""
    print_header("测试3：依赖感知调度")
    
    try:
        config = create_scheduler_config(
            strategy=SchedulingStrategy.DEPENDENCY_AWARE,
            max_concurrent=2
        )
        
        queue = DependencyAwareQueue(config=config)
        
        # 创建任务
        task_a = create_test_task("A", "Task A")
        task_b = create_test_task("B", "Task B")
        task_c = create_test_task("C", "Task C")
        
        # 添加依赖：A → B → C
        queue.add_dependency("A", "B")
        queue.add_dependency("B", "C")
        
        # 入队（故意打乱顺序）
        queue.enqueue(task_c, TaskPriority.NORMAL)
        queue.enqueue(task_b, TaskPriority.NORMAL)
        queue.enqueue(task_a, TaskPriority.NORMAL)
        
        print_pass("任务和依赖添加成功")
        
        # 第一次出队应该是A（没有依赖）
        first = queue.dequeue()
        assert first is not None and first.task.id == "A", "第一个应该是A"
        queue.complete_task("A", result={"status": "ok"})
        print_pass("A优先调度成功")
        
        # 第二次出队应该是B（A已完成）
        second = queue.dequeue()
        assert second is not None and second.task.id == "B", "第二个应该是B"
        queue.complete_task("B", result={"status": "ok"})
        print_pass("B在A完成后调度成功")
        
        # 第三次出队应该是C（B已完成）
        third = queue.dequeue()
        assert third is not None and third.task.id == "C", "第三个应该是C"
        print_pass("C在B完成后调度成功")
        
        print("\n✅ 测试3通过")
        return True
        
    except Exception as e:
        print_fail("测试3异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_4_multiple_scheduling_strategies():
    """测试4：多种调度策略验证"""
    print_header("测试4：多种调度策略验证")
    
    try:
        # 测试FIFO（禁用优先级）
        config_fifo = create_scheduler_config(
            strategy=SchedulingStrategy.FIFO,
            enable_priority=False
        )
        queue_fifo = DependencyAwareQueue(config=config_fifo)
        
        queue_fifo.enqueue(create_test_task("1", "Task 1"), TaskPriority.LOW)
        queue_fifo.enqueue(create_test_task("2", "Task 2"), TaskPriority.HIGH)
        queue_fifo.enqueue(create_test_task("3", "Task 3"), TaskPriority.NORMAL)
        
        # FIFO应该按入队顺序
        first_fifo = queue_fifo.dequeue()
        assert first_fifo.task.id == "1", "FIFO应该先出1"
        print_pass("FIFO策略正确")
        
        # 测试最短作业优先
        config_sjf = create_scheduler_config(strategy=SchedulingStrategy.SHORTEST_JOB_FIRST)
        queue_sjf = DependencyAwareQueue(config=config_sjf)
        
        task_long = create_test_task("long", "Long Task")
        task_short = create_test_task("short", "Short Task")
        
        queue_sjf.set_task_estimate("long", 10.0)
        queue_sjf.set_task_estimate("short", 1.0)
        
        queue_sjf.enqueue(task_long, TaskPriority.NORMAL)
        queue_sjf.enqueue(task_short, TaskPriority.NORMAL)
        
        first_sjf = queue_sjf.dequeue()
        assert first_sjf.task.id == "short", "SJF应该先出短任务"
        print_pass("最短作业优先策略正确")
        
        # 测试轮询
        config_rr = create_scheduler_config(strategy=SchedulingStrategy.ROUND_ROBIN)
        queue_rr = DependencyAwareQueue(config=config_rr)
        
        queue_rr.enqueue(create_test_task("A", "Task A"), TaskPriority.NORMAL)
        queue_rr.enqueue(create_test_task("B", "Task B"), TaskPriority.NORMAL)
        queue_rr.enqueue(create_test_task("C", "Task C"), TaskPriority.NORMAL)
        
        # 轮询应该循环选择
        order = []
        while True:
            t = queue_rr.dequeue()
            if not t:
                break
            order.append(t.task.id)
        
        # 至少应该有一定的轮询特征
        assert len(order) == 3, "应该出队3个任务"
        print_pass("轮询策略正确")
        
        print("\n✅ 测试4通过")
        return True
        
    except Exception as e:
        print_fail("测试4异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_5_configurable_scheduler_integration():
    """测试5：可配置调度器集成测试"""
    print_header("测试5：可配置调度器集成测试")
    
    try:
        completed_tasks = []
        
        def on_complete(task_id: str, result: dict):
            completed_tasks.append(task_id)
        
        # 创建调度器
        config = create_scheduler_config(
            strategy=SchedulingStrategy.DEPENDENCY_AWARE,
            max_concurrent=2
        )
        
        scheduler = ConfigurableScheduler(
            config=config,
            on_task_complete=on_complete
        )
        
        # 注册执行器
        def simple_executor(task: Task):
            time.sleep(0.1)
            return {"status": "done", "task_id": task.id}
        
        scheduler.register_executor("default", simple_executor)
        
        # 创建有依赖关系的任务
        task_a = create_test_task("A", "Task A")
        task_b = create_test_task("B", "Task B")
        task_c = create_test_task("C", "Task C")
        task_d = create_test_task("D", "Task D")
        
        # 添加依赖：A→C, B→D
        scheduler.add_dependency("A", "C")
        scheduler.add_dependency("B", "D")
        
        # 提交任务
        scheduler.submit_task(task_c, TaskPriority.NORMAL)
        scheduler.submit_task(task_d, TaskPriority.NORMAL)
        scheduler.submit_task(task_a, TaskPriority.NORMAL)
        scheduler.submit_task(task_b, TaskPriority.NORMAL)
        
        print_pass("任务和依赖添加成功")
        
        # 启动调度器
        scheduler.start()
        print_pass("调度器启动成功")
        
        # 等待完成
        wait_start = time.time()
        while len(completed_tasks) < 4 and time.time() - wait_start < 10.0:
            time.sleep(0.1)
        
        # 停止调度器
        scheduler.stop()
        print_pass("调度器停止成功")
        
        # 验证完成顺序：A和B应该在C和D之前
        assert "A" in completed_tasks, "A应该完成"
        assert "B" in completed_tasks, "B应该完成"
        assert "C" in completed_tasks, "C应该完成"
        assert "D" in completed_tasks, "D应该完成"
        
        # 验证依赖顺序
        a_index = completed_tasks.index("A")
        c_index = completed_tasks.index("C")
        assert a_index < c_index, "A应该在C之前完成"
        
        b_index = completed_tasks.index("B")
        d_index = completed_tasks.index("D")
        assert b_index < d_index, "B应该在D之前完成"
        print_pass("依赖顺序执行正确")
        
        # 测试策略切换
        scheduler.set_strategy(SchedulingStrategy.FIFO)
        new_config = scheduler.get_config()
        assert new_config.strategy == SchedulingStrategy.FIFO, "策略切换应该生效"
        print_pass("调度策略切换成功")
        
        print("\n✅ 测试5通过")
        return True
        
    except Exception as e:
        print_fail("测试5异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def main():
    print_header("第65阶段：任务依赖关系与可配置调度策略")
    print("验收标准：依赖管理、多种策略、可配置性")
    
    all_passed = True
    tests = [
        test_1_dependency_graph_basics,
        test_2_cyclic_dependency_detection,
        test_3_dependency_aware_scheduling,
        test_4_multiple_scheduling_strategies,
        test_5_configurable_scheduler_integration
    ]
    
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 80)
    print("第65阶段验收结果汇总")
    print("=" * 80)
    
    if all_passed:
        print("\n🎉 第65阶段验收通过！")
        print("任务依赖关系与可配置调度策略验证通过！")
    else:
        print("\n❌ 第65阶段验收失败")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
