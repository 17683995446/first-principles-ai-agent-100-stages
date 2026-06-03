
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from first_principles_agent import (
    Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction
)


def main():
    print("=" * 70)
    print("First Principles Agent - Simple Test")
    print("=" * 70)
    
    # Step 1: Create main task
    def end_condition(ctx):
        return "final_result" in ctx
    
    quartet = TaskQuartet(
        "Calculate simple arithmetic",
        end_func=end_condition
    )
    
    main_task = Task(
        "main_task",
        quartet,
        context_dict={"a": 5, "b": 3}
    )
    
    # Step 2: Create subtasks
    subtask1_quartet = TaskQuartet("Add numbers")
    subtask1 = Task("add_step", subtask1_quartet)
    
    subtask2_quartet = TaskQuartet("Multiply result")
    subtask2 = Task("multiply_step", subtask2_quartet)
    
    # Step 3: Create atomic actions
    def add_func(ctx):
        return {"sum_result": ctx["a"] + ctx["b"]}
    
    def multiply_func(ctx):
        return {"final_result": ctx["sum_result"] * 2}
    
    action1 = AtomicAction("add_action", "Add a and b", add_func)
    action2 = AtomicAction("multiply_action", "Multiply by 2", multiply_func)
    
    # Step 4: Initialize agent and run
    agent = FirstPrinciplesAgent(enable_logging=True)
    agent.set_task(main_task)
    agent.add_subtask(subtask1)
    agent.add_subtask(subtask2, dependencies=["add_step"])
    agent.set_atomic_actions([action1, action2])
    
    result = agent.execute()
    
    # Print results
    print("\n" + "=" * 70)
    print("Execution Complete!")
    print("=" * 70)
    print("Success:", result.success)
    print("Final Context:", result.context)
    print("Total Steps:", result.atomic_stats.get("total", 0))
    print("\nLogs:")
    for log in result.logs:
        print(f"  {log}")


if __name__ == "__main__":
    main()
