
"""
First Principles Agent System - Working Demo
Based on the 100-stage plan
"""

import time
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AtomicActionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskQuartet:
    """Core Task Structure (target, preconditions, constraints, end condition)
    """
    def __init__(self, target, preconditions=None, constraints=None, end_rule=None):
        self.target = target
        self.preconditions = preconditions or {}
        self.constraints = constraints or {}
        self.end_rule = end_rule or (lambda ctx: False)
    
    def validate(self):
        if not self.target or len(self.target.strip()) < 2:
            return False, "Invalid task target"
        return True, ""
    
    def check_end_condition(self, context):
        try:
            return self.end_rule(context)
        except:
            return False


class Task:
    def __init__(self, task_id, quartet, context=None):
        self.id = task_id
        self.quartet = quartet
        self.status = TaskStatus.PENDING
        self.context = context or {}
        self.output = None
    
    def validate(self):
        q_ok, q_msg = self.quartet.validate()
        if not q_ok:
            return False, [q_msg]
        return True, []
    
    def mark_in_progress(self):
        self.status = TaskStatus.IN_PROGRESS
    
    def mark_completed(self, output_val=None):
        self.status = TaskStatus.COMPLETED
        if output_val is not None:
            self.output = output_val
    
    def mark_failed(self, error_msg):
        self.status = TaskStatus.FAILED


class AtomicAction:
    def __init__(self, action_id, description, execute_func):
        self.id = action_id
        self.description = description
        self.execute_func = execute_func
        self.status = AtomicActionStatus.PENDING
        self.output = None
        self.error = None
    
    def execute(self, context):
        self.status = AtomicActionStatus.RUNNING
        try:
            self.output = self.execute_func(context)
            self.status = AtomicActionStatus.COMPLETED
            return self.output
        except Exception as e:
            self.status = AtomicActionStatus.FAILED
            self.error = str(e)
            raise


class TaskNode:
    def __init__(self, node_id, task, dependencies=None):
        self.id = node_id
        self.task = task
        self.dependencies = set(dependencies or [])
        self.dependents = set()
        self.status = TaskStatus.PENDING
        self.output = None
    
    def is_ready(self, completed_nodes):
        return self.dependencies.issubset(completed_nodes) and self.status == TaskStatus.PENDING


class TopologicalDecomposer:
    def __init__(self):
        self.nodes = {}
        self.in_degree = {}
    
    def add_task(self, task, dependencies=None):
        deps = dependencies or []
        if task.id in self.nodes:
            return False
        
        for dep in deps:
            if dep not in self.nodes:
                return False
        
        node = TaskNode(task.id, task, deps)
        self.nodes[task.id] = node
        self.in_degree[task.id] = len(deps)
        
        for dep in deps:
            node.dependencies.add(dep)
            self.nodes[dep].dependents.add(task.id)
        
        return True
    
    def validate_dag(self):
        if not self.nodes:
            return False, ["No tasks in graph"]
        
        temp_in_degree = self.in_degree.copy()
        queue = []
        for node_id, degree in temp_in_degree.items():
            if degree == 0:
                queue.append(node_id)
        
        visited = 0
        
        while queue:
            node_id = queue.pop(0)
            visited += 1
            
            if node_id not in self.nodes:
                continue
            
            for dependent_id in self.nodes[node_id].dependents:
                temp_in_degree[dependent_id] -= 1
                if temp_in_degree[dependent_id] == 0:
                    queue.append(dependent_id)
        
        if visited != len(self.nodes):
            return False, ["Graph has cycle"]
        
        return True, []
    
    def get_execution_order(self):
        is_valid, errors = self.validate_dag()
        if not is_valid:
            raise ValueError("Invalid DAG: " + str(errors))
        
        temp_in_degree = self.in_degree.copy()
        result = []
        
        while True:
            current_level = []
            for node_id, degree in temp_in_degree.items():
                if degree == 0 and temp_in_degree[node_id] != -1:
                    current_level.append(node_id)
            
            if not current_level:
                break
            
            result.append(current_level)
            
            for node_id in current_level:
                temp_in_degree[node_id] = -1
                if node_id in self.nodes:
                    for dependent_id in self.nodes[node_id].dependents:
                        if temp_in_degree[dependent_id] > 0:
                            temp_in_degree[dependent_id] -= 1
        
        return result
    
    def get_node(self, node_id):
        return self.nodes.get(node_id)
    
    def get_all_nodes(self):
        return list(self.nodes.values())
    
    def clear(self):
        self.nodes.clear()
        self.in_degree.clear()


class AtomicConverger:
    def __init__(self):
        self.action_queue = []
    
    def add_action(self, action):
        self.action_queue.append(action)
        return True
    
    def add_actions(self, actions):
        action_count = 0
        errors = []
        for action in actions:
            if self.add_action(action):
                action_count += 1
        return action_count, errors
    
    def decompose_task(self, task):
        return self.action_queue.copy()
    
    def set_action_queue(self, actions):
        self.action_queue = []
        self.add_actions(actions)
    
    def get_statistics(self):
        total = len(self.action_queue)
        completed = len([a for a in self.action_queue if a.status == AtomicActionStatus.COMPLETED])
        return {"total": total, "completed": completed}
    
    def clear(self):
        self.action_queue = []


class FirstPrinciplesAgent:
    def __init__(self):
        self.task = None
        self.decomposer = TopologicalDecomposer()
        self.converger = AtomicConverger()
        self.context = {}
        self.completed_nodes = set()
        self.logs = []
    
    def _log(self, msg):
        self.logs.append("[%s] %s" % (time.strftime("%H:%M:%S"), msg))
    
    def set_task(self, task_obj):
        ok, errors = task_obj.validate()
        if not ok:
            self._log("Task validation failed: " + str(errors))
            return False
        self.task = task_obj
        self.context = task_obj.context.copy()
        self._log("Set task: " + task_obj.id)
        return True
    
    def add_subtask(self, subtask, dependencies=None):
        success = self.decomposer.add_task(subtask, dependencies)
        if success:
            self._log("Added subtask: " + subtask.id + " (deps: " + str(dependencies) + ")")
        else:
            self._log("Failed to add subtask: " + subtask.id)
        return success
    
    def set_atomic_actions(self, actions):
        count, _ = self.converger.add_actions(actions)
        self._log("Set " + str(count) + " atomic actions")
    
    def execute(self):
        start_time = time.time()
        
        if not self.task:
            return {
                "success": False,
                "logs": ["No task set"],
                "execution_time_ms": 0
            }
        
        self._log("=" * 60)
        self._log("Starting execution: " + self.task.id)
        self._log("=" * 60)
        
        self.task.mark_in_progress()
        
        try:
            is_valid, errors = self.decomposer.validate_dag()
            if not is_valid:
                self._log("DAG validation failed: " + str(errors))
                self.task.mark_failed("DAG invalid")
                return self._build_result(False, start_time)
            
            execution_order = self.decomposer.get_execution_order()
            self._log("Execution order: " + str(execution_order))
            
            for level_idx, level in enumerate(execution_order, 1):
                self._log("Processing level " + str(level_idx) + ": " + str(level))
                
                for node_id in level:
                    node = self.decomposer.get_node(node_id)
                    if not node:
                        continue
                    
                    missing = node.dependencies - self.completed_nodes
                    if missing:
                        self._log("Dependency check failed: Missing " + str(missing))
                        node.task.mark_failed("Dependency error")
                        return self._build_result(False, start_time)
                    
                    if not node.task.quartet.target:
                        self._log("Pre-check failed: No target")
                        node.task.mark_failed("Pre-check error")
                        return self._build_result(False, start_time)
                    
                    node.task.mark_in_progress()
                    self._log("Executing node: " + node_id)
                    
                    actions = self.converger.decompose_task(node.task)
                    
                    for action in actions:
                        self._log("  Running action: " + action.id)
                        try:
                            output = action.execute(self.context)
                            
                            if output is None:
                                self._log("  Post-check failed: No output")
                                node.task.mark_failed("Action failed")
                                return self._build_result(False, start_time)
                            
                            self.context.update(output)
                            node.output = output
                            self._log("  ✓ Action completed: " + action.id)
                        except Exception as e:
                            self._log("  ✗ Action failed: " + str(e))
                            node.task.mark_failed("Action failed")
                            return self._build_result(False, start_time)
                    
                    node.task.mark_completed(node.output)
                    self.completed_nodes.add(node.id)
                    self._log("✓ Node completed: " + node.id)
            
            end_ok = self.task.quartet.check_end_condition(self.context)
            if end_ok:
                self.task.mark_completed()
                self._log("✓ Task completed!")
                return self._build_result(True, start_time)
            else:
                self.task.mark_failed("End condition not met")
                self._log("✗ End condition not met")
                return self._build_result(False, start_time)
                
        except Exception as e:
            self._log("Unexpected error: " + str(e))
            self.task.mark_failed(str(e))
            return self._build_result(False, start_time)
    
    def _build_result(self, success, start_time):
        return {
            "success": success,
            "task_id": self.task.id if self.task else None,
            "context": self.context.copy(),
            "logs": self.logs.copy(),
            "execution_time_ms": (time.time() - start_time) * 1000,
            "completed_nodes": list(self.completed_nodes),
            "atomic_stats": self.converger.get_statistics()
        }
    
    def reset(self):
        self.task = None
        self.decomposer.clear()
        self.converger.clear()
        self.context = {}
        self.completed_nodes = set()
        self.logs = []


def main():
    print("=" * 70)
    print("First Principles Agent - Working Demo")
    print("=" * 70)
    print("Based on the 100-stage complete plan")
    print()
    
    print("Example: Simple Math Workflow")
    print("-" * 70)
    print()
    
    # Create main task
    def end_condition(ctx):
        return "result" in ctx
    
    main_quartet = TaskQuartet(
        target="Calculate result",
        end_rule=end_condition
    )
    main_task = Task("main", main_quartet, context={"a": 5, "b": 3})
    
    # Create subtasks
    subtask1_quartet = TaskQuartet(target="Add numbers")
    subtask1 = Task("add", subtask1_quartet)
    
    subtask2_quartet = TaskQuartet(target="Multiply")
    subtask2 = Task("multiply", subtask2_quartet)
    
    # Create atomic actions
    def add_func(ctx):
        return {"sum": ctx["a"] + ctx["b"]}
    
    def multiply_func(ctx):
        return {"result": ctx["sum"] * 2}
    
    add_action = AtomicAction("add_action", "Add a and b", add_func)
    multiply_action = AtomicAction("multiply_action", "Multiply by two", multiply_func)
    
    # Initialize agent
    agent = FirstPrinciplesAgent()
    agent.set_task(main_task)
    agent.add_subtask(subtask1)
    agent.add_subtask(subtask2, dependencies=["add"])
    agent.set_atomic_actions([add_action, multiply_action])
    
    print("Starting execution...")
    print()
    result = agent.execute()
    
    print()
    print("=" * 70)
    print("Execution Result")
    print("=" * 70)
    print("Success:", result["success"])
    print("Context:", result["context"])
    print()
    print("Execution Logs:")
    for log in result["logs"]:
        print("  " + log)
    print()
    print("Atomic Actions Statistics:", result["atomic_stats"])
    print()
    
    print("=" * 70)
    print("Core Layers Implemented:")
    print("=" * 70)
    print("1. Task Quartet (Normative Layer): ✓")
    print("2. Topological Decomposer (DAG): ✓")
    print("3. Atomic Actions (Atomic Layer): ✓")
    print("4. Verification (Convergence): ✓")
    print()
    print("This implementation matches stages 1-50 of the 100-stage plan")
    print()


if __name__ == "__main__":
    main()
