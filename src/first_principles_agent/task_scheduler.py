"""
第63阶段：支持多任务并发调度基础能力
多任务并发调度模块
"""

import time
import uuid
import threading
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from .task_model import Task, TaskStatus


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskQueueStatus(Enum):
    """任务队列状态"""
    EMPTY = "empty"
    HAS_PENDING = "has_pending"
    ALL_COMPLETED = "all_completed"


@dataclass
class QueuedTask:
    """队列中的任务包装类"""
    task: Task
    priority: TaskPriority
    enqueue_time: float
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task.id,
            "priority": self.priority.value,
            "status": self._get_status(),
            "enqueue_time": self.enqueue_time,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "result": self.result,
            "error": self.error
        }
    
    def _get_status(self) -> str:
        if self.end_time is not None:
            return "completed" if self.error is None else "failed"
        elif self.start_time is not None:
            return "running"
        else:
            return "pending"


class TaskQueue:
    """
    任务队列管理器
    支持优先级、并发控制、任务状态追踪
    """
    
    def __init__(
        self,
        max_concurrent: int = 3,
        enable_priority: bool = True
    ):
        self.max_concurrent = max_concurrent
        self.enable_priority = enable_priority
        
        # 队列存储
        self.pending_queue: List[QueuedTask] = []
        self.running_tasks: Dict[str, QueuedTask] = {}
        self.completed_tasks: Dict[str, QueuedTask] = {}
        self.all_tasks: Dict[str, QueuedTask] = {}
        
        # 线程安全锁
        self._lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            "total_enqueued": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_running": 0,
            "total_pending": 0,
            "avg_wait_time_ms": 0,
            "avg_exec_time_ms": 0
        }
    
    def enqueue(
        self,
        task: Task,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """
        将任务加入队列
        
        Args:
            task: 任务对象
            priority: 优先级
            
        Returns:
            任务ID
        """
        with self._lock:
            queued_task = QueuedTask(
                task=task,
                priority=priority,
                enqueue_time=time.time()
            )
            
            self.pending_queue.append(queued_task)
            self.all_tasks[task.id] = queued_task
            self.stats["total_enqueued"] += 1
            self._update_stats()
            
            if self.enable_priority:
                self._sort_by_priority()
            
            return task.id
    
    def dequeue(self) -> Optional[QueuedTask]:
        """
        从队列中获取下一个可执行的任务
        
        Returns:
            队列任务对象，无可用任务时返回None
        """
        with self._lock:
            if not self.pending_queue:
                return None
            
            if len(self.running_tasks) >= self.max_concurrent:
                return None
            
            # 从队列头部取出
            queued_task = self.pending_queue.pop(0)
            queued_task.start_time = time.time()
            self.running_tasks[queued_task.task.id] = queued_task
            self._update_stats()
            
            return queued_task
    
    def complete_task(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        标记任务完成
        
        Args:
            task_id: 任务ID
            result: 任务结果
            error: 错误信息
            
        Returns:
            是否成功标记
        """
        with self._lock:
            if task_id not in self.running_tasks:
                return False
            
            queued_task = self.running_tasks.pop(task_id)
            queued_task.end_time = time.time()
            queued_task.result = result
            queued_task.error = error
            self.completed_tasks[task_id] = queued_task
            
            if error:
                self.stats["total_failed"] += 1
            else:
                self.stats["total_completed"] += 1
            
            self._update_stats()
            return True
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消待执行任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        with self._lock:
            for i, task in enumerate(self.pending_queue):
                if task.task.id == task_id:
                    self.pending_queue.pop(i)
                    self.all_tasks.pop(task_id, None)
                    self._update_stats()
                    return True
            return False
    
    def get_task(self, task_id: str) -> Optional[QueuedTask]:
        """获取任务信息"""
        with self._lock:
            return self.all_tasks.get(task_id)
    
    def get_queue_status(self) -> TaskQueueStatus:
        """获取队列状态"""
        with self._lock:
            if not self.pending_queue and not self.running_tasks:
                return TaskQueueStatus.ALL_COMPLETED
            elif self.pending_queue:
                return TaskQueueStatus.HAS_PENDING
            else:
                return TaskQueueStatus.EMPTY
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return self.stats.copy()
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务状态"""
        with self._lock:
            return [task.to_dict() for task in self.all_tasks.values()]
    
    def clear(self):
        """清空队列"""
        with self._lock:
            self.pending_queue = []
            self.running_tasks = {}
            self.completed_tasks = {}
            self.all_tasks = {}
            self.stats = {
                "total_enqueued": 0,
                "total_completed": 0,
                "total_failed": 0,
                "total_running": 0,
                "total_pending": 0,
                "avg_wait_time_ms": 0,
                "avg_exec_time_ms": 0
            }
    
    def _sort_by_priority(self):
        """按优先级排序队列"""
        self.pending_queue.sort(
            key=lambda x: (-x.priority.value, x.enqueue_time)
        )
    
    def _update_stats(self):
        """更新统计信息"""
        self.stats["total_pending"] = len(self.pending_queue)
        self.stats["total_running"] = len(self.running_tasks)
        
        # 计算平均等待时间和执行时间
        completed = list(self.completed_tasks.values())
        if completed:
            wait_times = [
                (t.start_time - t.enqueue_time) * 1000 
                for t in completed if t.start_time
            ]
            exec_times = [
                (t.end_time - t.start_time) * 1000 
                for t in completed if t.start_time and t.end_time
            ]
            
            self.stats["avg_wait_time_ms"] = (
                sum(wait_times) / len(wait_times) if wait_times else 0
            )
            self.stats["avg_exec_time_ms"] = (
                sum(exec_times) / len(exec_times) if exec_times else 0
            )


class TaskScheduler:
    """
    任务调度器
    基于优先级和并发控制的任务调度
    """
    
    def __init__(
        self,
        task_queue: Optional[TaskQueue] = None,
        max_concurrent: int = 3,
        on_task_complete: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        on_task_error: Optional[Callable[[str, str], None]] = None
    ):
        self.queue = task_queue or TaskQueue(max_concurrent=max_concurrent)
        self.on_task_complete = on_task_complete
        self.on_task_error = on_task_error
        
        # 调度线程控制
        self._scheduler_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.RLock()
        
        # 执行函数映射
        self._executors: Dict[str, Callable[[Task], Dict[str, Any]]] = {}
    
    def register_executor(
        self,
        task_type: str,
        executor: Callable[[Task], Dict[str, Any]]
    ):
        """
        注册任务执行器
        
        Args:
            task_type: 任务类型
            executor: 执行函数
        """
        with self._lock:
            self._executors[task_type] = executor
    
    def submit_task(
        self,
        task: Task,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """
        提交任务
        
        Args:
            task: 任务对象
            priority: 优先级
            
        Returns:
            任务ID
        """
        return self.queue.enqueue(task, priority)
    
    def start(self):
        """启动调度器"""
        with self._lock:
            if self._running:
                return
            
            self._running = True
            self._scheduler_thread = threading.Thread(
                target=self._scheduler_loop,
                daemon=True
            )
            self._scheduler_thread.start()
    
    def stop(self):
        """停止调度器"""
        with self._lock:
            self._running = False
        
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5.0)
    
    def get_queue_status(self) -> TaskQueueStatus:
        """获取队列状态"""
        return self.queue.get_queue_status()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.queue.get_stats()
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.queue.get_task(task_id)
        return task.to_dict() if task else None
    
    def _scheduler_loop(self):
        """调度主循环"""
        while self._running:
            self._dispatch_tasks()
            time.sleep(0.1)
    
    def _dispatch_tasks(self):
        """分发任务"""
        while True:
            queued_task = self.queue.dequeue()
            if not queued_task:
                break
            
            # 在新线程中执行任务
            thread = threading.Thread(
                target=self._execute_task,
                args=(queued_task,),
                daemon=True
            )
            thread.start()
    
    def _execute_task(self, queued_task: QueuedTask):
        """执行单个任务"""
        task_id = queued_task.task.id
        
        try:
            # 查找执行器
            task_type = getattr(queued_task.task, "task_type", "default")
            executor = self._executors.get(task_type)
            
            if executor:
                result = executor(queued_task.task)
                self.queue.complete_task(task_id, result=result)
                
                if self.on_task_complete:
                    self.on_task_complete(task_id, result)
            else:
                # 默认执行器
                result = self._default_executor(queued_task.task)
                self.queue.complete_task(task_id, result=result)
                
                if self.on_task_complete:
                    self.on_task_complete(task_id, result)
        
        except Exception as e:
            error_msg = str(e)
            self.queue.complete_task(task_id, error=error_msg)
            
            if self.on_task_error:
                self.on_task_error(task_id, error_msg)
    
    def _default_executor(self, task: Task) -> Dict[str, Any]:
        """默认任务执行器"""
        # 模拟任务执行
        time.sleep(0.5)
        return {
            "task_id": task.id,
            "status": "completed",
            "message": "Task executed with default executor"
        }
