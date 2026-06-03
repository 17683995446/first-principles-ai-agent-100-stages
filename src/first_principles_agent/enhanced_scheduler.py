"""
第64阶段：资源管理与调度策略增强
增强的任务调度器，支持资源配额、加权调度、超时控制
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from .task_scheduler import (
    TaskQueue, TaskScheduler, QueuedTask, TaskPriority, TaskQueueStatus
)
from .task_model import Task


class ResourceType(Enum):
    """资源类型枚举"""
    CPU = "cpu"
    MEMORY = "memory"
    IO = "io"
    NETWORK = "network"


@dataclass
class ResourceQuota:
    """资源配额"""
    cpu: float = 1.0  # CPU核数
    memory_mb: int = 512  # 内存MB
    io_weight: int = 1  # IO权重
    network_mbps: int = 100  # 网络带宽Mbps


@dataclass
class ResourceUsage:
    """资源使用情况"""
    cpu_used: float = 0.0
    memory_mb_used: int = 0
    io_used: int = 0
    network_mbps_used: int = 0


@dataclass
class TaskConfig:
    """任务配置，增强的任务元数据"""
    resource_quota: ResourceQuota = field(default_factory=ResourceQuota)
    timeout_seconds: Optional[float] = None  # 超时时间，None表示无限制
    weight: int = 1  # 调度权重，越高越容易被调度
    task_type: str = "default"  # 任务类型，用于执行器匹配


class WeightedTaskQueue(TaskQueue):
    """
    加权任务队列，支持加权公平调度
    """
    
    def __init__(
        self,
        max_concurrent: int = 3,
        enable_priority: bool = True,
        resource_quota: Optional[ResourceQuota] = None
    ):
        super().__init__(max_concurrent, enable_priority)
        
        # 资源管理
        self.total_resources = resource_quota or ResourceQuota()
        self.used_resources = ResourceUsage()
        
        # 加权调度相关
        self.task_weights: Dict[str, int] = {}  # task_id -> weight
        self.type_stats: Dict[str, Dict[str, Any]] = {}  # 按任务类型统计
        
    def enqueue(
        self,
        task: Task,
        priority: TaskPriority = TaskPriority.NORMAL,
        task_config: Optional[TaskConfig] = None
    ) -> str:
        """
        入队任务，支持任务配置
        
        Args:
            task: 任务对象
            priority: 优先级
            task_config: 任务配置（资源、超时、权重等）
            
        Returns:
            任务ID
        """
        config = task_config or TaskConfig()
        
        # 存储任务权重
        self.task_weights[task.id] = config.weight
        
        # 统计任务类型
        task_type = config.task_type
        if task_type not in self.type_stats:
            self.type_stats[task_type] = {"count": 0, "total_weight": 0}
        self.type_stats[task_type]["count"] += 1
        self.type_stats[task_type]["total_weight"] += config.weight
        
        # 调用父类入队
        return super().enqueue(task, priority)
    
    def dequeue(self) -> Optional[QueuedTask]:
        """
        加权公平调度出队
        
        Returns:
            可执行的任务
        """
        with self._lock:
            if not self.pending_queue:
                return None
            
            if len(self.running_tasks) >= self.max_concurrent:
                return None
            
            # 加权选择
            selected_index = self._weighted_select()
            if selected_index is None:
                return None
            
            queued_task = self.pending_queue.pop(selected_index)
            queued_task.start_time = time.time()
            self.running_tasks[queued_task.task.id] = queued_task
            self._update_stats()
            
            return queued_task
    
    def _weighted_select(self) -> Optional[int]:
        """
        加权选择算法
        
        Returns:
            选中任务的索引
        """
        if not self.pending_queue:
            return None
        
        # 如果启用了优先级，先按优先级分组
        if self.enable_priority:
            # 找到最高优先级的任务组
            max_priority = max(t.priority.value for t in self.pending_queue)
            high_priority_indices = [
                i for i, t in enumerate(self.pending_queue) 
                if t.priority.value == max_priority
            ]
            
            # 在最高优先级组内进行加权选择
            candidates = [(i, self.pending_queue[i]) for i in high_priority_indices]
        else:
            # 没有优先级，使用所有任务
            candidates = [(i, t) for i, t in enumerate(self.pending_queue)]
        
        # 计算候选任务的总权重
        total_weight = sum(
            self.task_weights.get(task.task.id, 1)
            for _, task in candidates
        )
        
        if total_weight <= 0:
            return candidates[0][0] if candidates else None
        
        # 随机选择（模拟加权概率）
        import random
        pick = random.uniform(0, total_weight)
        
        current = 0
        for idx, task in candidates:
            weight = self.task_weights.get(task.task.id, 1)
            current += weight
            if current >= pick:
                return idx
        
        return candidates[0][0] if candidates else None
    
    def get_extended_stats(self) -> Dict[str, Any]:
        """获取扩展统计信息"""
        stats = self.get_stats()
        stats.update({
            "used_resources": {
                "cpu": self.used_resources.cpu_used,
                "memory_mb": self.used_resources.memory_mb_used,
                "io": self.used_resources.io_used,
                "network_mbps": self.used_resources.network_mbps_used
            },
            "total_resources": {
                "cpu": self.total_resources.cpu,
                "memory_mb": self.total_resources.memory_mb,
                "io_weight": self.total_resources.io_weight,
                "network_mbps": self.total_resources.network_mbps
            },
            "type_stats": self.type_stats.copy()
        })
        return stats
    
    def clear(self):
        """清空队列，包括增强数据"""
        super().clear()
        self.task_weights.clear()
        self.type_stats.clear()


class EnhancedTaskScheduler(TaskScheduler):
    """
    增强型任务调度器
    支持资源管理、超时控制、加权调度
    """
    
    def __init__(
        self,
        task_queue: Optional[WeightedTaskQueue] = None,
        max_concurrent: int = 3,
        resource_quota: Optional[ResourceQuota] = None,
        on_task_complete: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        on_task_error: Optional[Callable[[str, str], None]] = None,
        on_task_timeout: Optional[Callable[[str], None]] = None
    ):
        queue = task_queue or WeightedTaskQueue(
            max_concurrent=max_concurrent,
            resource_quota=resource_quota
        )
        super().__init__(
            task_queue=queue,
            max_concurrent=max_concurrent,
            on_task_complete=on_task_complete,
            on_task_error=on_task_error
        )
        
        self.on_task_timeout = on_task_timeout
        self.task_configs: Dict[str, TaskConfig] = {}  # task_id -> config
        self.task_timers: Dict[str, Optional[threading.Timer]] = {}  # 超时计时器
        
        # 超时监控线程
        self._timeout_thread: Optional[threading.Thread] = None
    
    def submit_task(
        self,
        task: Task,
        priority: TaskPriority = TaskPriority.NORMAL,
        task_config: Optional[TaskConfig] = None
    ) -> str:
        """
        提交任务，支持增强配置
        
        Args:
            task: 任务对象
            priority: 优先级
            task_config: 任务配置
            
        Returns:
            任务ID
        """
        config = task_config or TaskConfig()
        self.task_configs[task.id] = config
        
        # 调用队列的增强入队
        return self.queue.enqueue(task, priority, config)
    
    def start(self):
        """启动调度器，包括超时监控"""
        super().start()
        
        # 启动超时监控线程
        with self._lock:
            if self._timeout_thread is None or not self._timeout_thread.is_alive():
                self._timeout_thread = threading.Thread(
                    target=self._timeout_monitor_loop,
                    daemon=True
                )
                self._timeout_thread.start()
    
    def _execute_task(self, queued_task: QueuedTask):
        """执行任务，支持超时控制"""
        task_id = queued_task.task.id
        config = self.task_configs.get(task_id, TaskConfig())
        
        # 设置超时计时器
        timer = None
        if config.timeout_seconds is not None:
            timer = threading.Timer(
                config.timeout_seconds,
                self._handle_task_timeout,
                args=[task_id]
            )
            self.task_timers[task_id] = timer
            timer.start()
        
        try:
            # 调用父类执行逻辑
            super()._execute_task(queued_task)
        finally:
            # 清理计时器
            timer = self.task_timers.pop(task_id, None)
            if timer:
                timer.cancel()
    
    def _handle_task_timeout(self, task_id: str):
        """处理任务超时"""
        with self._lock:
            if task_id in self.queue.running_tasks:
                # 标记任务失败
                self.queue.complete_task(
                    task_id,
                    error=f"Task timed out after {self.task_configs.get(task_id, TaskConfig()).timeout_seconds} seconds"
                )
                
                if self.on_task_timeout:
                    self.on_task_timeout(task_id)
                if self.on_task_error:
                    self.on_task_error(
                        task_id,
                        f"Task timed out after {self.task_configs.get(task_id, TaskConfig()).timeout_seconds} seconds"
                    )
    
    def _timeout_monitor_loop(self):
        """超时监控主循环"""
        while self._running:
            time.sleep(0.5)
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """获取增强统计信息"""
        if hasattr(self.queue, 'get_extended_stats'):
            return self.queue.get_extended_stats()
        return self.get_stats()


def create_task_config(
    cpu: float = 1.0,
    memory_mb: int = 512,
    timeout_seconds: Optional[float] = None,
    weight: int = 1,
    task_type: str = "default"
) -> TaskConfig:
    """
    辅助函数：创建任务配置
    
    Args:
        cpu: CPU核数需求
        memory_mb: 内存需求MB
        timeout_seconds: 超时时间
        weight: 调度权重
        task_type: 任务类型
        
    Returns:
        TaskConfig对象
    """
    return TaskConfig(
        resource_quota=ResourceQuota(
            cpu=cpu,
            memory_mb=memory_mb
        ),
        timeout_seconds=timeout_seconds,
        weight=weight,
        task_type=task_type
    )
