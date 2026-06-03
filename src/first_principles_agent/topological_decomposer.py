from enum import Enum
from typing import List, Dict, Any, Optional, Set
from .task_model import Task, TaskStatus


class NodeType(Enum):
    PARALLEL = "parallel"
    SERIAL = "serial"


class TaskNode:
    def __init__(
        self,
        node_id: str,
        task: Task,
        dependencies: Optional[List[str]] = None,
        node_type: Optional[NodeType] = None
    ):
        self.id = node_id
        self.task = task
        self.dependencies: Set[str] = set(dependencies or [])
        self.dependents: Set[str] = set()
        self.type = node_type or NodeType.SERIAL
        self.status = TaskStatus.PENDING
        self.output = None
        self.inputs: Dict[str, Any] = {}
        self.outputs: Dict[str, Any] = {}
    
    def is_ready(self, completed_nodes: Set[str]) -> bool:
        return (
            self.dependencies.issubset(completed_nodes) and
            self.status == TaskStatus.PENDING
        )
    
    def mark_in_progress(self):
        self.status = TaskStatus.IN_PROGRESS
    
    def mark_completed(self, output: Any = None):
        self.status = TaskStatus.COMPLETED
        if output is not None:
            self.output = output
    
    def mark_failed(self, error_msg: str = ""):
        self.status = TaskStatus.FAILED
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task.id,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
            "type": self.type.value,
            "status": self.status.value,
            "output": self.output
        }


class TopologicalIssue:
    def __init__(self, issue_type: str, description: str, affected_nodes: List[str] = None):
        self.type = issue_type
        self.description = description
        self.affected_nodes = affected_nodes or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "description": self.description,
            "affected_nodes": self.affected_nodes
        }


class TopologicalDecomposer:
    def __init__(self):
        self.nodes: Dict[str, TaskNode] = {}
        self.in_degree: Dict[str, int] = {}
        self.issues: List[TopologicalIssue] = []
    
    def add_task(
        self,
        task: Task,
        dependencies: Optional[List[str]] = None,
        node_type: Optional[NodeType] = None
    ) -> bool:
        """
        第31-32阶段：添加子任务
        """
        deps = dependencies or []
        
        if task.id in self.nodes:
            self.issues.append(TopologicalIssue(
                "duplicate_node",
                f"Duplicate node: {task.id}",
                [task.id]
            ))
            return False
        
        for dep in deps:
            if dep not in self.nodes:
                self.issues.append(TopologicalIssue(
                    "missing_dependency",
                    f"Missing dependency: {dep}",
                    [task.id, dep]
                ))
                return False
        
        node = TaskNode(task.id, task, deps, node_type)
        self.nodes[task.id] = node
        self.in_degree[task.id] = len(deps)
        
        for dep in deps:
            node.dependencies.add(dep)
            self.nodes[dep].dependents.add(task.id)
        
        return True
    
    def add_tasks(self, task_configs: List[Dict[str, Any]]) -> tuple[bool, List[str]]:
        errors = []
        count = 0
        
        for config in task_configs:
            task = config.get("task")
            if not task:
                continue
            
            deps = config.get("dependencies")
            node_type = config.get("type")
            
            success = self.add_task(task, deps, node_type)
            if success:
                count += 1
            else:
                errors.append(f"Failed to add task: {task.id}")
        
        return len(errors) == 0, errors
    
    def detect_cycles(self) -> List[List[str]]:
        """
        第35阶段：循环依赖检测
        """
        cycles = []
        visited = set()
        recursion_stack = set()
        
        def dfs(node_id: str, path: List[str]) -> bool:
            if node_id in recursion_stack:
                cycle_start = path.index(node_id)
                cycle = path[cycle_start:] + [node_id]
                cycles.append(cycle)
                return True
            
            if node_id in visited:
                return False
            
            visited.add(node_id)
            recursion_stack.add(node_id)
            path.append(node_id)
            
            if node_id in self.nodes:
                for dependent in self.nodes[node_id].dependents:
                    dfs(dependent, path.copy())
            
            recursion_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id, [])
        
        return cycles
    
    def detect_dangling_nodes(self) -> List[str]:
        """
        第35阶段：悬空节点检测
        """
        dangling = []
        
        # 检查入度为0的节点是否有出边（除了初始节点）
        has_incoming = set()
        for node in self.nodes.values():
            has_incoming.update(node.dependents)
        
        # 孤立节点：没有入度也没有出度（除了第一个节点）
        node_ids = list(self.nodes.keys())
        if node_ids:
            start_node = node_ids[0]
            for node_id in node_ids[1:]:
                node = self.nodes[node_id]
                if (node_id not in has_incoming and 
                    len(node.dependents) == 0 and 
                    len(node.dependencies) > 0):
                    dangling.append(node_id)
        
        return dangling
    
    def validate_dag(self) -> tuple[bool, List[TopologicalIssue]]:
        """
        第35阶段：DAG合法性验证
        """
        self.issues = []
        
        if not self.nodes:
            issue = TopologicalIssue("empty_graph", "No tasks in graph")
            self.issues.append(issue)
            return False, self.issues
        
        # 检查循环
        cycles = self.detect_cycles()
        for cycle in cycles:
            self.issues.append(TopologicalIssue(
                "cycle",
                f"Cycle detected: {' -> '.join(cycle)}",
                cycle
            ))
        
        # 检查悬空节点
        dangling = self.detect_dangling_nodes()
        if dangling:
            self.issues.append(TopologicalIssue(
                "dangling_nodes",
                f"Dangling nodes: {dangling}",
                dangling
            ))
        
        return len(self.issues) == 0, self.issues
    
    def auto_mark_node_types(self) -> None:
        """
        第36阶段：串行/并行节点自动标记分类
        """
        execution_order = self.get_execution_order()
        
        for level in execution_order:
            if len(level) > 1:
                for node_id in level:
                    if node_id in self.nodes:
                        self.nodes[node_id].type = NodeType.PARALLEL
    
    def get_execution_order(self) -> List[List[str]]:
        """
        第33-34阶段：拓扑排序获取执行顺序
        """
        is_valid, errors = self.validate_dag()
        if not is_valid:
            raise ValueError("Invalid DAG: " + str([e.description for e in errors]))
        
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
    
    def validate_io_bindings(self) -> tuple[bool, List[TopologicalIssue]]:
        """
        第38阶段：节点输入输出前后绑定校验
        """
        issues = []
        
        for node_id, node in self.nodes.items():
            for dep_id in node.dependencies:
                if dep_id in self.nodes:
                    dep_node = self.nodes[dep_id]
                    if dep_node.status == TaskStatus.COMPLETED:
                        node.inputs.update(dep_node.outputs)
        
        return len(issues) == 0, issues
    
    def get_issue_summary(self) -> Dict[str, Any]:
        """
        获取问题摘要
        """
        issue_types = {}
        for issue in self.issues:
            issue_types[issue.type] = issue_types.get(issue.type, 0) + 1
        
        return {
            "total_issues": len(self.issues),
            "issue_types": issue_types,
            "has_cycle": any(i.type == "cycle" for i in self.issues),
            "has_dangling": any(i.type == "dangling_nodes" for i in self.issues),
            "is_valid": len(self.issues) == 0
        }
    
    def get_node(self, node_id: str) -> Optional[TaskNode]:
        return self.nodes.get(node_id)
    
    def get_all_nodes(self) -> List[TaskNode]:
        return list(self.nodes.values())
    
    def clear(self):
        self.nodes.clear()
        self.in_degree.clear()
        self.issues.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化
        """
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "issues": [i.to_dict() for i in self.issues],
            "summary": self.get_issue_summary()
        }


class SubtaskSplitter:
    """
    第32阶段：子任务智能拆分引擎
    """
    def __init__(self):
        pass
    
    def split_task_by_steps(
        self,
        task: Task,
        step_names: List[str]
    ) -> List[Task]:
        """
        按步骤拆分为子任务
        """
        subtasks = []
        
        for i, step_name in enumerate(step_names):
            subtask_quartet = task.quartet.__class__(
                target=f"{task.quartet.target} - Step {i+1}: {step_name}"
            )
            subtask = Task(
                task_id=f"{task.id}_step_{i+1}",
                quartet=subtask_quartet,
                context=task.context.copy()
            )
            subtasks.append(subtask)
        
        return subtasks
    
    def create_dependency_configs(
        self,
        subtasks: List[Task],
        sequential: bool = True
    ) -> List[Dict[str, Any]]:
        """
        创建依赖配置
        """
        configs = []
        
        for i, subtask in enumerate(subtasks):
            deps = []
            if sequential and i > 0:
                deps = [subtasks[i-1].id]
            
            configs.append({
                "task": subtask,
                "dependencies": deps
            })
        
        return configs
