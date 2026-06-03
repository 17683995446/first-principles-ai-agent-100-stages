
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))

from first_principles_agent import (
    Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction
)


def main():
    print("=" * 60)
    print("基于第一性原理的 AI Agent 示例")
    print("=" * 60)

    # 1. 创建任务四元组
    quartet = TaskQuartet(
        target="计算两个数的和并乘以2",
        preconditions={"a": 0, "b": 0},
        constraints={"max_result": 100},
        end_rule=lambda ctx: "final_result" in ctx
    )

    # 2. 创建主任务
    main_task = Task(
        id="main_task",
        quartet=quartet,
        context={"a": 10, "b": 20}
    )

    # 3. 创建子任务
    subtask1_quartet = TaskQuartet(
        target="计算 a + b",
        end_rule=lambda ctx: "sum_result" in ctx
    )
    subtask1 = Task(
        id="subtask1",
        quartet=subtask1_quartet
    )

    subtask2_quartet = TaskQuartet(
        target="将结果乘以2",
        end_rule=lambda ctx: "final_result" in ctx
    )
    subtask2 = Task(
        id="subtask2",
        quartet=subtask2_quartet
    )

    # 4. 创建原子动作
    add_action = AtomicAction(
        id="add",
        description="执行加法运算",
        execute_func=lambda ctx: {"sum_result": ctx["a"] + ctx["b"]}
    )

    multiply_action = AtomicAction(
        id="multiply",
        description="执行乘法运算",
        execute_func=lambda ctx: {"final_result": ctx["sum_result"] * 2}
    )

    # 5. 初始化 Agent
    agent = FirstPrinciplesAgent()

    # 6. 设置任务和子任务
    agent.set_task(main_task)
    agent.add_subtask(subtask1)
    agent.add_subtask(subtask2, dependencies=["subtask1"])

    # 7. 设置原子动作
    agent.set_atomic_actions([add_action, multiply_action])

    # 8. 执行任务
    print("\n开始执行任务...\n")
    result = agent.execute()

    # 9. 输出结果
    print("\n" + "=" * 60)
    print("执行结果:")
    print("=" * 60)
    print(f"成功: {result.success}")
    print(f"最终上下文: {result.context}")
    print("\n执行日志:")
    for log in result.logs:
        print(f"  - {log}")

    if result.success:
        print(f"\n最终结果: {result.context.get('final_result')}")


if __name__ == "__main__":
    main()
