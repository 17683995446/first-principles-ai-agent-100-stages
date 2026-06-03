"""
第65阶段：任务依赖关系与可配置调度策略
支持任务依赖管理、多种调度策略、策略配置
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable, Set
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
from .enhanced_scheduler import (
    WeightedTaskQueue, EnhancedTaskScheduler, TaskConfig, ResourceQuota
)
from .task_scheduler import QueuedTask, TaskPriority, TaskQueueStatus
from .task_model import Task


class SchedulingStrategy(Enum):
    """调度策略枚举"""
    FIFO = "fifo"  # 先进先出
    PRIORITY_WEIGHTED = "priority_weighted"  # 优先级+权重
    DEPENDENCY_AWARE = "dependency_aware"  # 依赖感知
    SHORTEST_JOB_FIRST = "shortest_job_first"  # 最短作业优先
    ROUND_ROBIN = "round_robin"  # 轮询


@dataclass
class DependencyEdge:
    """依赖关系边"""
    from_task_id: str  # 前置任务
    to_task_id: str  # 后置任务
    hard: bool = True  # 是否为硬依赖（必须完成才能开始）


@dataclass
class TaskDependencyGraph:
    """任务依赖图"""
    tasks: Set[str] = field(default_factory=set)
    dependencies: List[DependencyEdge] = field(default_factory=list)
    
    # 快速查找结构
    _task_deps: Dict[str, Set[str]] = field(default_factory=dict)  # task -> 前置任务集合
    _task_dependents: Dict[str, Set[str]] = field(default_factory=dict)  # task -> 后置任务集合
    
    def add_dependency(self, from_task: str, to_task: str, hard: bool = True):
        """添加依赖关系"""
        edge = DependencyEdge(from_task, to_task, hard)
        self.dependencies.append(edge)
        self.tasks.add(from_task)
        self.tasks.add(to_task)
        
        # 更新快速查找结构
        if to_task not in self._task_deps:
            self._task_deps[to_task] = set()
        self._task_deps[to_task].add(from_task)
        
        if from_task not in self._task_dependents:
            self._task_dependents[from_task] = set()
        self._task_dependents[from_task].add(to_task)
    
    def get_dependencies(self, task_id: str) -> Set[str]:
        """获取任务的前置依赖"""
        return self._task_deps.get(task_id, set())
    
    def get_dependents(self, task_id: str) -> Set[str]:
        """获取依赖该任务的后置任务"""
        return self._task_dependents.get(task_id, set())
    
    def has_unmet_dependencies(self, task_id: str, completed_tasks: Set[str]) -> bool:
        """检查任务是否有未满足的依赖"""
        dependencies = self.get_dependencies(task_id)
        # 只检查硬依赖
        hard_deps = set()
        for dep in dependencies:
            # 查找依赖边以确认是否为硬依赖
            for edge in self.dependencies:
                if edge.from_task_id == dep and edge.to_task_id == task_id:
                    if edge.hard:
                        hard_deps.add(dep)
                    break
        return not hard_deps.issubset(completed_tasks)
    
    def is_cyclic(self) -> bool:
        """检查是否有循环依赖"""
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            if node not in visited:
                visited.add(node)
                rec_stack.add(node)
                
                for dependent in self.get_dependents(node):
                    if dependent not in visited and has_cycle(dependent):
                        return True
                    elif dependent in rec_stack:
                        return True
                        
            if node in rec_stack:
                rec_stack.remove(node)
            return False
        
        for task in self.tasks:
            if has_cycle(task):
                return True
        return False


@dataclass
class SchedulerConfig:
    """调度器配置"""
    strategy: SchedulingStrategy = SchedulingStrategy.DEPENDENCY_AWARE
    max_concurrent: int = 3
    enable_priority: bool = True
    enable_weight: bool = True
    enable_dependency: bool = True
    default_weight: int = 1
    round_robin_quantum: float = 1.0  # 轮询时间片（秒）
    enable_resource_constraint: bool = True
    resource_quota: ResourceQuota = field(default_factory=ResourceQuota)


class DependencyAwareQueue(WeightedTaskQueue):
    """
    依赖感知的任务队列
    """
    
    def __init__(
        self,
        config: Optional[SchedulerConfig] = None,
        dependency_graph: Optional[TaskDependencyGraph] = None
    ):
        self.config = config or SchedulerConfig()
        super().__init__(
            max_concurrent=self.config.max_concurrent,
            enable_priority=self.config.enable_priority,
            resource_quota=self.config.resource_quota
        )
        
        self.dependency_graph = dependency_graph or TaskDependencyGraph()
        self.completed_task_ids: Set[str] = set()
        
        # 轮询相关
        self._round_robin_index: int = 0
        self._task_estimates: Dict[str, float] = {}  # task_id -> 预估执行时间
        
    def add_dependency(self, from_task: str, to_task: str, hard: bool = True):
        """添加任务依赖"""
        self.dependency_graph.add_dependency(from_task, to_task, hard)
    
    def set_task_estimate(self, task_id: str, estimate_seconds: float):
        """设置任务预估执行时间（用于最短作业优先）"""
        self._task_estimates[task_id] = estimate_seconds
    
    def enqueue(
        self,
        task: Task,
        priority: TaskPriority = TaskPriority.NORMAL,
        task_config: Optional[TaskConfig] = None
    ) -> str:
        """入队任务，添加到依赖图"""
        self.dependency_graph.tasks.add(task.id)
        return super().enqueue(task, priority, task_config)
    
    def complete_task(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> bool:
        """完成任务，更新依赖状态"""
        success = super().complete_task(task_id, result, error)
        if success:
            self.completed_task_ids.add(task_id)
        return success
    
    def dequeue(self) -> Optional[QueuedTask]:
        """根据策略选择任务"""
        with self._lock:
            if not self.pending_queue:
                return None
            
            if len(self.running_tasks) >= self.max_concurrent:
                return None
            
            # 根据策略选择
            selected_index = self._select_by_strategy()
            if selected_index is None:
                return None
            
            queued_task = self.pending_queue.pop(selected_index)
            queued_task.start_time = time.time()
            self.running_tasks[queued_task.task.id] = queued_task
            self._update_stats()
            
            return queued_task
    
    def _select_by_strategy(self) -> Optional[int]:
        """根据调度策略选择任务"""
        strategy = self.config.strategy
        
        if strategy == SchedulingStrategy.FIFO:
            return self._select_fifo()
        elif strategy == SchedulingStrategy.PRIORITY_WEIGHTED:
            return self._weighted_select()
        elif strategy == SchedulingStrategy.DEPENDENCY_AWARE:
            return self._select_dependency_aware()
        elif strategy == SchedulingStrategy.SHORTEST_JOB_FIRST:
            return self._select_shortest_job()
        elif strategy == SchedulingStrategy.ROUND_ROBIN:
            return self._select_round_robin()
        else:
            return self._weighted_select()
    
    def _select_fifo(self) -> Optional[int]:
        """先进先出选择"""
        if not self.pending_queue:
            return None
        
        # 检查依赖
        for i, task in enumerate(self.pending_queue):
            if not self._has_unmet_deps(task.task.id):
                return i
        return None
    
    def _select_dependency_aware(self) -> Optional[int]:
        """依赖感知选择（先检查依赖，再按优先级+权重）"""
        if not self.pending_queue:
            return None
        
        # 筛选出依赖已满足的任务
        available_tasks = []
        for i, task in enumerate(self.pending_queue):
            if not self._has_unmet_deps(task.task.id):
                available_tasks.append((i, task))
        
        if not available_tasks:
            return None
        
        # 在可用任务中按优先级+权重选择
        if self.config.enable_priority:
            # 按优先级分组
            priority_groups = defaultdict(list)
            for i, task in available_tasks:
                priority_groups[task.priority.value].append((i, task))
            
            # 取最高优先级组
            if priority_groups:
                max_priority = max(priority_groups.keys())
                candidates = priority_groups[max_priority]
            else:
                candidates = available_tasks
        else:
            candidates = available_tasks
        
        # 使用权重选择
        if self.config.enable_weight and len(candidates) > 1:
            total_weight = sum(
                self.task_weights.get(task.task.id, self.config.default_weight)
                for _, task in candidates
            )
            
            if total_weight > 0:
                import random
                pick = random.uniform(0, total_weight)
                current = 0
                for idx, task in candidates:
                    weight = self.task_weights.get(task.task.id, self.config.default_weight)
                    current += weight
                    if current >= pick:
                        return idx
        
        # 否则返回第一个
        return candidates[0][0] if candidates else None
    
    def _select_shortest_job(self) -> Optional[int]:
        """最短作业优先选择"""
        if not self.pending_queue:
            return None
        
        # 筛选可用任务
        available = [
            (i, task) for i, task in enumerate(self.pending_queue)
            if not self._has_unmet_deps(task.task.id)
        ]
        
        if not available:
            return None
        
        # 按预估时间排序
        available.sort(
            key=lambda x: self._task_estimates.get(x[1].task.id, float('inf'))
        )
        
        return available[0][0]
    
    def _select_round_robin(self) -> Optional[int]:
        """轮询选择"""
        if not self.pending_queue:
            return None
        
        # 筛选可用任务
        available = [
            (i, task) for i, task in enumerate(self.pending_queue)
            if not self._has_unmet_deps(task.task.id)
        ]
        
        if not available:
            return None
        
        # 轮询选择
        selected_index = self._round_robin_index % len(available)
        self._round_robin_index += 1
        
        return available[selected_index][0]
    
    def _has_unmet_deps(self, task_id: str) -> bool:
        """检查任务是否有未满足的依赖"""
        if not self.config.enable_dependency:
            return False
        return self.dependency_graph.has_unmet_dependencies(task_id, self.completed_task_ids)
    
    def clear(self):
        """清空"""
        super().clear()
        self.completed_task_ids.clear()
        self._task_estimates.clear()
        self._round_robin_index = 0
        self.dependency_graph = TaskDependencyGraph()


class ConfigurableScheduler(EnhancedTaskScheduler):
    """
    可配置的增强调度器
    """
    
    def __init__(
        self,
        config: Optional[SchedulerConfig] = None,
        dependency_graph: Optional[TaskDependencyGraph] = None,
        on_task_complete: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        on_task_error: Optional[Callable[[str, str], None]] = None,
        on_task_timeout: Optional[Callable[[str], None]] = None
    ):
        self.config = config or SchedulerConfig()
        
        queue = DependencyAwareQueue(
            config=self.config,
            dependency_graph=dependency_graph
        )
        
        super().__init__(
            task_queue=queue,
            max_concurrent=self.config.max_concurrent,
            resource_quota=self.config.resource_quota,
            on_task_complete=on_task_complete,
            on_task_error=on_task_error,
            on_task_timeout=on_task_timeout
        )
    
    def add_dependency(self, from_task: str, to_task: str, hard: bool = True):
        """添加任务依赖"""
        if hasattr(self.queue, 'add_dependency'):
            self.queue.add_dependency(from_task, to_task, hard)
    
    def set_task_estimate(self, task_id: str, estimate_seconds: float):
        """设置任务预估执行时间"""
        if hasattr(self.queue, 'set_task_estimate'):
            self.queue.set_task_estimate(task_id, estimate_seconds)
    
    def set_strategy(self, strategy: SchedulingStrategy):
        """切换调度策略"""
        self.config.strategy = strategy
        if hasattr(self.queue, 'config'):
            self.queue.config.strategy = strategy
    
    def get_config(self) -> SchedulerConfig:
        """获取当前配置"""
        return self.config


def create_scheduler_config(
    strategy: SchedulingStrategy = SchedulingStrategy.DEPENDENCY_AWARE,
    max_concurrent: int = 3,
    enable_priority: bool = True,
    enable_weight: bool = True,
    enable_dependency: bool = True,
    cpu: float = 4.0,
    memory_mb: int = 2048
) -> SchedulerConfig:
    """创建调度器配置"""
    return SchedulerConfig(
        strategy=strategy,
        max_concurrent=max_concurrent,
        enable_priority=enable_priority,
        enable_weight=enable_weight,
        enable_dependency=enable_dependency,
        resource_quota=ResourceQuota(cpu=cpu, memory_mb=memory_mb)
    )
