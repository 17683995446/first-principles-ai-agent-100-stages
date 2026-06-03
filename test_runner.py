
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from first_principles_agent import (
    Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction
)


def test_basic_functionality():
    print("测试基本功能...")
    
    # 创建任务四元组
    quartet = TaskQuartet(
        target="简单计算示例",
        end_rule=lambda ctx: "done" in ctx
    )
    
    # 创建主任务
    task = Task(
        id="test_task",
        quartet=quartet,
        context={"value": 5}
    )
    
    # 创建原子动作
    def action1_func(ctx):
        return {"value": ctx["value"] * 2}
    
    def action2_func(ctx):
        return {"done": True, "final_value": ctx["value"] + 10}
    
    action1 = AtomicAction(
        id="double",
        description="数值翻倍",
        execute_func=action1_func
    )
    
    action2 = AtomicAction(
        id="add_ten",
        description="加10",
        execute_func=action2_func
    )
    
    # 初始化并执行
    agent = FirstPrinciplesAgent()
    agent.set_task(task)
    agent.add_subtask(task)  # 添加自身作为子任务
    agent.set_atomic_actions([action1, action2])
    
    result = agent.execute()
    
    print(f"测试结果: {'✓ 通过' if result.success else '✗ 失败'}")
    print(f"最终上下文: {result.context}")
    
    return result.success


if __name__ == "__main__":
    print("=" * 60)
    print("基于第一性原理的 AI Agent 系统测试")
    print("=" * 60)
    print()
    
    success = test_basic_functionality()
    
    print()
    print("=" * 60)
    print(f"总体测试结果: {'✓ 成功' if success else '✗ 失败'}")
    print("=" * 60)
