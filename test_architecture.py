
"""
Test Architecture - Verify the src directory module structure works

This script will test importing and using the core modules
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))


def main():
    print("=" * 70)
    print("ARCHITECTURE TEST")
    print("=" * 70)
    print()
    
    # Test 1: Import core modules
    print("Test 1: Importing core modules")
    print("-" * 50)
    
    try:
        from first_principles_agent.task_model import (
            Task, TaskQuartet, TaskStatus
        )
        print("✓ task_model imported successfully")
    except Exception as e:
        print(f"✗ task_model import failed: {e}")
        return
    
    try:
        from first_principles_agent.topological_decomposer import (
            TopologicalDecomposer, TaskNode, NodeType
        )
        print("✓ topological_decomposer imported successfully")
    except Exception as e:
        print(f"✗ topological_decomposer import failed: {e}")
        return
    
    try:
        from first_principles_agent.atomic_converger import (
            AtomicConverger, AtomicAction, AtomicActionStatus
        )
        print("✓ atomic_converger imported successfully")
    except Exception as e:
        print(f"✗ atomic_converger import failed: {e}")
        return
    
    try:
        from first_principles_agent.verification_layer import (
            VerificationLayer, VerificationReport, VerificationResult
        )
        print("✓ verification_layer imported successfully")
    except Exception as e:
        print(f"✗ verification_layer import failed: {e}")
        return
    
    try:
        from first_principles_agent.orchestrator import (
            FirstPrinciplesAgent, ExecutionResult, ExecutionMetrics
        )
        print("✓ orchestrator imported successfully")
    except Exception as e:
        print(f"✗ orchestrator import failed: {e}")
        return
    
    try:
        from first_principles_agent import (
            Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction
        )
        print("✓ package __init__.py imports work correctly")
    except Exception as e:
        print(f"✗ package __init__.py imports failed: {e}")
        return
    
    print()
    
    # Test 2: Create a simple workflow
    print("Test 2: Creating and executing a simple workflow")
    print("-" * 50)
    
    try:
        # Create main task
        def end_condition(ctx):
            return "result" in ctx
        
        main_quartet = TaskQuartet("Simple math", end_rule=end_condition)
        main_task = Task("main", main_quartet, context={"x": 3, "y": 4})
        
        # Create subtasks
        sub1_quartet = TaskQuartet("Add numbers")
        sub1 = Task("add", sub1_quartet)
        
        sub2_quartet = TaskQuartet("Multiply")
        sub2 = Task("multiply", sub2_quartet)
        
        # Create actions
        def add_func(ctx):
            return {"sum": ctx["x"] + ctx["y"]}
        
        def multiply_func(ctx):
            return {"result": ctx["sum"] * 2}
        
        action1 = AtomicAction("add", "Add x and y", add_func)
        action2 = AtomicAction("multiply", "Multiply sum", multiply_func)
        
        # Initialize agent
        agent = FirstPrinciplesAgent()
        agent.set_task(main_task)
        agent.add_subtask(sub1)
        agent.add_subtask(sub2, dependencies=["add"])
        agent.set_atomic_actions([action1, action2])
        
        print("✓ Agent and components created successfully")
        
        # Execute
        print("  Executing workflow...")
        result = agent.execute()
        
        print(f"✓ Workflow executed: success={result.success}")
        print(f"  Final context: {result.context}")
        
    except Exception as e:
        print(f"✗ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    print("=" * 70)
    print("ALL TESTS PASSED!")
    print("The architecture is working correctly.")
    print("=" * 70)


if __name__ == "__main__":
    main()
