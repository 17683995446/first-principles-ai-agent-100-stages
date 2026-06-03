
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from first_principles_agent import (
    Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction
)


def main():
    print("=" * 70)
    print("基于第一性原理的 AI Agent 完整示例")
    print("=" * 70)
    print("\n场景: 一个简单的数据处理流程")
    print("  1. 验证输入数据")
    print("  2. 处理数据")
    print("  3. 生成报告")
    print("=" * 70)
    print()

    # 1. 创建主任务四元组
    main_quartet = TaskQuartet(
        target="完成数据处理并生成报告",
        preconditions={"data": None},
        constraints={"max_items": 100},
        end_rule=lambda ctx: "report_generated" in ctx and ctx["report_generated"]
    )

    main_task = Task(
        id="main_pipeline",
        quartet=main_quartet,
        context={"data": [1, 2, 3, 4, 5]}
    )

    # 2. 创建子任务
    # 子任务1: 验证数据
    validate_quartet = TaskQuartet(
        target="验证输入数据的有效性",
        end_rule=lambda ctx: "data_validated" in ctx
    )
    validate_task = Task(id="validate_data", quartet=validate_quartet)

    # 子任务2: 处理数据
    process_quartet = TaskQuartet(
        target="对数据进行处理",
        end_rule=lambda ctx: "data_processed" in ctx
    )
    process_task = Task(id="process_data", quartet=process_quartet)

    # 子任务3: 生成报告
    report_quartet = TaskQuartet(
        target="基于处理后的数据生成报告",
        end_rule=lambda ctx: "report_generated" in ctx
    )
    report_task = Task(id="generate_report", quartet=report_quartet)

    # 3. 创建原子动作
    def validate_data_func(ctx):
        data = ctx.get("data", [])
        if not data:
            raise ValueError("No data provided")
        print(f"  ✓ 验证数据: {len(data)} 个项目")
        return {
            "data_validated": True, "valid_count": len(data)}

    def process_data_func(ctx):
        data = ctx.get("data", [])
        processed = [x * 2 for x in data]
        print(f"  ✓ 处理数据: {data} -&gt; {processed}")
        return {
            "data_processed": True, "processed_data": processed, "sum": sum(processed)}

    def generate_report_func(ctx):
        processed = ctx.get("processed_data", [])
        total = ctx.get("sum", 0)
        print(f"  ✓ 生成报告:")
        print(f"    - 原始数据: {[x//2 for x in processed]}")
        print(f"    - 处理结果: {processed}")
        print(f"    - 总和: {total}")
        return {
            "report_generated": True,
            "report": {
                "summary": f"Processed {len(processed)} items, total: {total}"
            }
        }

    validate_action = AtomicAction(
        id="validate",
        description="验证输入数据",
        execute_func=validate_data_func
    )

    process_action = AtomicAction(
        id="process",
        description="处理数据",
        execute_func=process_data_func
    )

    report_action = AtomicAction(
        id="report",
        description="生成报告",
        execute_func=generate_report_func
    )

    # 4. 初始化并配置 Agent
    agent = FirstPrinciplesAgent()
    agent.set_task(main_task)
    
    # 添加子任务及其依赖关系
    agent.add_subtask(validate_task)
    agent.add_subtask(process_task, dependencies=["validate_data"])
    agent.add_subtask(report_task, dependencies=["process_data"])
    
    # 设置原子动作
    agent.set_atomic_actions([validate_action, process_action, report_action])

    # 5. 执行任务
    print("\n开始执行任务...\n")
    result = agent.execute()

    # 6. 显示结果
    print("\n" + "=" * 70)
    print("执行结果:")
    print("=" * 70)
    print(f"成功: {'✓ 是' if result.success else '✗ 否'}")
    print("\n执行日志:")
    for i, log in enumerate(result.logs, 1):
        print(f"  {i}. {log}")

    print(f"\n最终上下文: {result.context}")
    
    if result.success:
        print("\n报告:")
        if "report" in result.context:
            print(f"  {result.context['report']['summary']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
