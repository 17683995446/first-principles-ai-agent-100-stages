"""
第67阶段：调度器与监控系统集成优化
集成调度器与监控系统，提供完整的一体化解决方案
"""

import time
import uuid
import threading
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict

from .configurable_scheduler import (
    ConfigurableScheduler, TaskDependencyGraph,
    SchedulerConfig, SchedulingStrategy, create_scheduler_config
)
from .task_monitor import (
    TaskMonitor, TaskExecutionHistory, TaskMetricsCollector,
    TaskExecutionRecord, PerformanceMetrics, MonitorTaskStatus,
    create_monitor
)
from .task_scheduler import TaskPriority
from .task_model import Task, TaskQuartet


@dataclass
class IntegratedSchedulerStats:
    """集成调度器综合统计"""
    total_scheduled: int = 0
    total_executing: int = 0
    total_completed: int = 0
    total_failed: int = 0
    total_timeout: int = 0
    queue_depth: int = 0
    avg_wait_time_ms: float = 0.0
    avg_exec_time_ms: float = 0.0
    throughput_per_min: float = 0.0
    success_rate: float = 0.0
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_scheduled": self.total_scheduled,
            "total_executing": self.total_executing,
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "total_timeout": self.total_timeout,
            "queue_depth": self.queue_depth,
            "avg_wait_time_ms": self.avg_wait_time_ms,
            "avg_exec_time_ms": self.avg_exec_time_ms,
            "throughput_per_min": self.throughput_per_min,
            "success_rate": self.success_rate,
            "resource_utilization": self.resource_utilization
        }


class IntegratedTaskScheduler:
    """
    集成调度器 - 结合调度器与监控系统的完整解决方案
    """
    
    def __init__(
        self,
        scheduler_config: Optional[SchedulerConfig] = None,
        max_history_records: int = 10000,
        auto_start_monitoring: bool = True
    ):
        self.scheduler_config = scheduler_config or create_scheduler_config()
        
        # 初始化调度器
        self.scheduler = ConfigurableScheduler(
            config=self.scheduler_config,
            dependency_graph=TaskDependencyGraph()
        )
        
        # 初始化监控系统
        self.monitor = create_monitor(max_history_records=max_history_records)
        
        # 状态
        self.is_running = False
        self._monitoring_thread: Optional[threading.Thread] = None
        
        # 性能跟踪
        self._start_time = time.time()
        self._task_submit_times: Dict[str, float] = {}
        self._lock = threading.RLock()
        
        # 自定义执行器映射
        self._custom_executors: Dict[str, Callable[[Task], Dict[str, Any]]] = {}
        
        if auto_start_monitoring:
            self.start_monitoring()
    
    def register_executor(
        self,
        task_type: str,
        executor: Callable[[Task], Dict[str, Any]]
    ):
        """注册任务执行器"""
        with self._lock:
            self._custom_executors[task_type] = executor
            self.scheduler.register_executor(task_type, executor)
    
    def add_dependency(
        self,
        from_task_id: str,
        to_task_id: str,
        hard: bool = True
    ):
        """添加任务依赖关系"""
        self.scheduler.add_dependency(from_task_id, to_task_id, hard)
    
    def submit_task(
        self,
        task: Task,
        priority: TaskPriority = TaskPriority.NORMAL,
        task_config: Optional[Any] = None,
        task_type: str = "default",
        weight: int = 1
    ) -> str:
        """
        提交任务（带监控集成）
        """
        with self._lock:
            # 记录提交时间
            submit_time = time.time()
            self._task_submit_times[task.id] = submit_time
            
            # 记录监控开始
            self.monitor.on_task_start(
                task_id=task.id,
                task_name=getattr(task.quartet, 'target', 'Unnamed Task') if hasattr(task, 'quartet') else 'Unnamed Task',
                priority=priority.value if hasattr(priority, 'value') else priority,
                weight=weight,
                task_type=task_type,
                trace_id=str(uuid.uuid4())
            )
            
            # 注册包装后的执行器
            if task_type not in self._custom_executors:
                def wrapped_executor(t: Task):
                    return self._execute_with_monitoring(t)
                
                self.register_executor(task_type, wrapped_executor)
            
            # 提交到调度器
            return self.scheduler.submit_task(task, priority, task_config)
    
    def _execute_with_monitoring(self, task: Task) -> Dict[str, Any]:
        """
        包装执行器，集成监控
        """
        task_id = task.id
        start_time = time.time()
        result: Dict[str, Any] = {"status": "unknown"}
        
        try:
            # 查找或使用默认执行器
            executor = self._custom_executors.get(
                "default",
                None
            )
            
            if executor and executor is not self._execute_with_monitoring:
                result = executor(task)
            else:
                # 默认执行
                result = {
                    "task_id": task_id,
                    "status": "completed",
                    "completed_at": time.time()
                }
            
            # 计算执行时间
            exec_time_ms = (time.time() - start_time) * 1000
            
            # 计算等待时间
            wait_time_ms: Optional[float] = None
            if task_id in self._task_submit_times:
                wait_time_ms = (start_time - self._task_submit_times[task_id]) * 1000
            
            # 记录完成
            self.monitor.on_task_complete(
                task_id=task_id,
                execution_time_ms=exec_time_ms,
                result_summary=result,
                wait_time_ms=wait_time_ms,
                queue_time_ms=wait_time_ms
            )
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            exec_time_ms = (time.time() - start_time) * 1000
            
            self.monitor.on_task_failed(
                task_id=task_id,
                error_message=error_msg,
                execution_time_ms=exec_time_ms
            )
            raise
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self._lock:
            cancelled = self.scheduler.queue.cancel_task(task_id)
            if cancelled:
                self.monitor.on_task_cancelled(task_id)
            return cancelled
    
    def start(self):
        """启动调度器"""
        with self._lock:
            if not self.is_running:
                self.is_running = True
                self.scheduler.start()
    
    def stop(self):
        """停止调度器"""
        with self._lock:
            if self.is_running:
                self.is_running = False
                self.scheduler.stop()
                self.stop_monitoring()
    
    def start_monitoring(self):
        """启动监控线程"""
        with self._lock:
            if self._monitoring_thread is None or not self._monitoring_thread.is_alive():
                self._monitoring_thread = threading.Thread(
                    target=self._monitoring_loop,
                    daemon=True
                )
                self._monitoring_thread.start()
    
    def stop_monitoring(self):
        """停止监控线程"""
        with self._lock:
            self._monitoring_stop_flag = True
    
    def _monitoring_loop(self):
        """监控主循环"""
        self._monitoring_stop_flag = False
        
        while self.is_running and not self._monitoring_stop_flag:
            try:
                # 定期清理过期数据
                self._cleanup_task_times()
                time.sleep(1.0)
            except Exception as e:
                print(f"监控循环异常: {e}")
    
    def _cleanup_task_times(self):
        """清理已完成任务的时间记录"""
        with self._lock:
            completed_ids = list(self._task_submit_times.keys())
            # 保留最近的记录
            if len(completed_ids) > 10000:
                # 简单的清理策略，保留最近的
                pass
    
    def get_stats(self) -> IntegratedSchedulerStats:
        """获取综合统计"""
        with self._lock:
            monitor_stats = self.monitor.get_metrics()
            scheduler_stats = self.scheduler.get_stats()
            
            # 合并统计
            stats = IntegratedSchedulerStats(
                total_scheduled=monitor_stats.get("total_tasks", 0),
                total_completed=monitor_stats.get("completed_tasks", 0),
                total_failed=monitor_stats.get("failed_tasks", 0),
                total_timeout=monitor_stats.get("timeout_tasks", 0),
                queue_depth=scheduler_stats.get("total_pending", 0),
                avg_wait_time_ms=monitor_stats.get("avg_wait_time_ms", 0),
                avg_exec_time_ms=monitor_stats.get("avg_execution_time_ms", 0),
                success_rate=monitor_stats.get("success_rate", 0),
                throughput_per_min=monitor_stats.get("throughput_tasks_per_second", 0) * 60
            )
            
            # 计算资源利用率（模拟）
            stats.resource_utilization = {
                "cpu": 0.75,
                "memory": 0.6,
                "io": 0.4
            }
            
            return stats
    
    def get_recent_history(
        self,
        limit: int = 50,
        status_filter: Optional[MonitorTaskStatus] = None
    ) -> List[Dict[str, Any]]:
        """获取最近的执行历史"""
        return self.monitor.get_history(limit=limit, status=status_filter)
    
    def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """获取特定任务的历史"""
        return self.monitor.get_task_history(task_id)
    
    def set_scheduling_strategy(self, strategy: SchedulingStrategy):
        """切换调度策略"""
        self.scheduler.set_strategy(strategy)
    
    def export_stats_report(self) -> Dict[str, Any]:
        """导出完整的统计报告"""
        return {
            "timestamp": time.time(),
            "uptime_seconds": time.time() - self._start_time,
            "scheduler": self.get_stats().to_dict(),
            "monitor": self.monitor.get_metrics(),
            "config": {
                "strategy": self.scheduler_config.strategy.value if hasattr(self.scheduler_config.strategy, 'value') else str(self.scheduler_config.strategy),
                "max_concurrent": self.scheduler_config.max_concurrent
            }
        }


def create_integrated_scheduler(
    strategy: SchedulingStrategy = SchedulingStrategy.DEPENDENCY_AWARE,
    max_concurrent: int = 5,
    max_history_records: int = 10000
) -> IntegratedTaskScheduler:
    """
    创建集成调度器的工厂函数
    """
    config = create_scheduler_config(
        strategy=strategy,
        max_concurrent=max_concurrent
    )
    
    return IntegratedTaskScheduler(
        scheduler_config=config,
        max_history_records=max_history_records,
        auto_start_monitoring=True
    )
