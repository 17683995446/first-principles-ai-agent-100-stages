
"""
Complete Workflow Example - First Principles Agent

This example demonstrates the full workflow of the First Principles Agent:
1. Task definition (Task Quartet)
2. Topological decomposition (DAG)
3. Atomic actions
4. Verification and execution
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from first_principles_agent import (
    Task,
    TaskQuartet,
    FirstPrinciplesAgent,
    AtomicAction,
    create_simple_action,
    create_validated_action
)


def main():
    print("=" * 70)
    print("FIRST PRINCIPLES AGENT - COMPLETE WORKFLOW EXAMPLE")
    print("=" * 70)
    print()
    
    # Step 1: Define the main task
    print("Step 1: Define main task")
    print("-" * 50)
    
    def end_condition(ctx):
        return "final_result" in ctx
    
    main_quartet = TaskQuartet(
        target="Calculate mathematical operations",
        end_rule=end_condition
    )
    
    main_task = Task(
        task_id="math_task",
        quartet=main_quartet,
        context={"a": 10, "b": 5}
    )
    
    print(f"Main task: {main_task.id}")
    print(f"Target: {main_task.quartet.target}")
    print(f"Initial context: {main_task.context}")
    print()
    
    # Step 2: Initialize agent and set up the task
    print("Step 2: Initialize agent")
    print("-" * 50)
    
    agent = FirstPrinciplesAgent()
    agent.set_task(main_task)
    print()
    
    # Step 3: Create subtasks (Topological DAG)
    print("Step 3: Define subtasks with dependencies")
    print("-" * 50)
    
    add_quartet = TaskQuartet(target="Add a and b")
    add_task = Task("add_step", add_quartet)
    
    multiply_quartet = TaskQuartet(target="Multiply sum by 2")
    multiply_task = Task("multiply_step", multiply_quartet)
    
    square_quartet = TaskQuartet(target="Square the product")
    square_task = Task("square_step", square_quartet)
    
    agent.add_subtask(add_task)
    agent.add_subtask(multiply_task, dependencies=["add_step"])
    agent.add_subtask(square_task, dependencies=["multiply_step"])
    
    print("Subtasks created:")
    print("- add_step (no dependencies)")
    print("- multiply_step (depends on add_step)")
    print("- square_step (depends on multiply_step)")
    print()
    
    # Step 4: Define atomic actions
    print("Step 4: Define atomic actions")
    print("-" * 50)
    
    def add_func(ctx):
        return {"sum": ctx["a"] + ctx["b"]}
    
    def multiply_func(ctx):
        return {"product": ctx["sum"] * 2}
    
    def square_func(ctx):
        return {"final_result": ctx["product"] ** 2}
    
    add_action = create_validated_action(
        action_id="add_numbers",
        description="Add a and b",
        execute_func=add_func,
        required_inputs=["a", "b"],
        expected_outputs=["sum"]
    )
    
    multiply_action = create_validated_action(
        action_id="multiply_sum",
        description="Multiply sum by 2",
        execute_func=multiply_func,
        required_inputs=["sum"],
        expected_outputs=["product"]
    )
    
    square_action = create_validated_action(
        action_id="square_product",
        description="Square the product",
        execute_func=square_func,
        required_inputs=["product"],
        expected_outputs=["final_result"]
    )
    
    agent.set_atomic_actions([add_action, multiply_action, square_action])
    
    print("Atomic actions created:")
    print("- add_numbers")
    print("- multiply_sum")
    print("- square_product")
    print()
    
    # Step 5: Execute
    print("Step 5: Execute workflow")
    print("-" * 50)
    print("Starting execution...")
    print()
    
    result = agent.execute()
    
    # Step 6: Print results
    print()
    print("=" * 70)
    print("EXECUTION RESULTS")
    print("=" * 70)
    print(f"Success: {result.success}")
    print(f"Execution time: {result.execution_time_ms:.2f}ms")
    print()
    
    print("Final context:")
    for key, value in result.context.items():
        print(f"  {key} = {value}")
    print()
    
    print("Atomic action statistics:")
    print(f"  Total: {result.atomic_stats.get('total', 0)}")
    print(f"  Completed: {result.atomic_stats.get('completed', 0)}")
    print(f"  Failed: {result.atomic_stats.get('failed', 0)}")
    print()
    
    print("Completed nodes:")
    for node_id in result.completed_nodes:
        print(f"  ✓ {node_id}")
    print()
    
    print("Execution log:")
    for log_entry in result.logs[-10:]:
        print(f"  {log_entry}")
    print()
    
    print("=" * 70)
    print("WORKFLOW COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
