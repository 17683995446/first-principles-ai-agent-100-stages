"""
第66阶段：任务监控、指标收集与执行历史管理
提供完整的任务执行监控、指标统计和历史记录功能
"""

import time
import uuid
import threading
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime


class MonitorTaskStatus(Enum):
    """任务执行状态（监控专用）"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class TaskExecutionRecord:
    """任务执行记录"""
    task_id: str
    task_name: str
    status: MonitorTaskStatus
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    execution_time_ms: Optional[float] = None
    wait_time_ms: Optional[float] = None
    queue_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None
    priority: int = 1
    weight: int = 1
    task_type: str = "default"
    trace_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "execution_time_ms": self.execution_time_ms,
            "wait_time_ms": self.wait_time_ms,
            "queue_time_ms": self.queue_time_ms,
            "error_message": self.error_message,
            "result_summary": self.result_summary,
            "priority": self.priority,
            "weight": self.weight,
            "task_type": self.task_type,
            "trace_id": self.trace_id,
            "created_at": self.created_at
        }


@dataclass
class PerformanceMetrics:
    """性能指标统计"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    timeout_tasks: int = 0
    cancelled_tasks: int = 0
    avg_execution_time_ms: float = 0.0
    avg_wait_time_ms: float = 0.0
    avg_queue_time_ms: float = 0.0
    max_execution_time_ms: float = 0.0
    min_execution_time_ms: float = float('inf')
    throughput_tasks_per_second: float = 0.0
    success_rate: float = 0.0
    task_type_distribution: Dict[str, int] = field(default_factory=dict)
    priority_distribution: Dict[int, int] = field(default_factory=dict)
    hourly_execution_count: Dict[int, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "timeout_tasks": self.timeout_tasks,
            "cancelled_tasks": self.cancelled_tasks,
            "avg_execution_time_ms": self.avg_execution_time_ms,
            "avg_wait_time_ms": self.avg_wait_time_ms,
            "avg_queue_time_ms": self.avg_queue_time_ms,
            "max_execution_time_ms": self.max_execution_time_ms,
            "min_execution_time_ms": self.min_execution_time_ms if self.min_execution_time_ms != float('inf') else 0,
            "throughput_tasks_per_second": self.throughput_tasks_per_second,
            "success_rate": self.success_rate,
            "task_type_distribution": self.task_type_distribution,
            "priority_distribution": self.priority_distribution,
            "hourly_execution_count": self.hourly_execution_count
        }


class TaskExecutionHistory:
    """任务执行历史管理器"""
    
    def __init__(self, max_records: int = 10000):
        self.max_records = max_records
        self.records: Dict[str, TaskExecutionRecord] = {}
        self.records_list: List[TaskExecutionRecord] = []
        self._lock = threading.RLock()
        
        # 索引
        self.task_id_index: Dict[str, List[str]] = defaultdict(list)
        self.status_index: Dict[MonitorTaskStatus, List[str]] = defaultdict(list)
        self.type_index: Dict[str, List[str]] = defaultdict(list)
        self.time_index: List[Tuple[float, str]] = []
    
    def add_record(self, record: TaskExecutionRecord) -> str:
        """添加执行记录"""
        with self._lock:
            record_id = str(uuid.uuid4())
            self.records[record_id] = record
            self.records_list.append(record)
            
            # 更新索引
            self.task_id_index[record.task_id].append(record_id)
            self.status_index[record.status].append(record_id)
            self.type_index[record.task_type].append(record_id)
            self.time_index.append((record.created_at, record_id))
            
            # 限制记录数量
            self._trim_old_records()
            
            return record_id
    
    def get_record(self, record_id: str) -> Optional[TaskExecutionRecord]:
        """获取单个记录"""
        with self._lock:
            return self.records.get(record_id)
    
    def get_records_by_task_id(self, task_id: str) -> List[TaskExecutionRecord]:
        """获取指定任务的所有记录"""
        with self._lock:
            record_ids = self.task_id_index.get(task_id, [])
            return [self.records[rid] for rid in record_ids if rid in self.records]
    
    def get_records_by_status(self, status: MonitorTaskStatus) -> List[TaskExecutionRecord]:
        """获取指定状态的记录"""
        with self._lock:
            record_ids = self.status_index.get(status, [])
            return [self.records[rid] for rid in record_ids if rid in self.records]
    
    def get_records_by_time_range(self, start_time: float, end_time: float) -> List[TaskExecutionRecord]:
        """获取时间范围内的记录"""
        with self._lock:
            result = []
            for ts, rid in self.time_index:
                if start_time <= ts <= end_time:
                    if rid in self.records:
                        result.append(self.records[rid])
            return result
    
    def get_all_records(self) -> List[TaskExecutionRecord]:
        """获取所有记录（最新的在前）"""
        with self._lock:
            return list(reversed(self.records_list))
    
    def clear(self):
        """清空所有记录"""
        with self._lock:
            self.records.clear()
            self.records_list.clear()
            self.task_id_index.clear()
            self.status_index.clear()
            self.type_index.clear()
            self.time_index.clear()
    
    def _trim_old_records(self):
        """删除旧记录以保持最大数量限制"""
        if len(self.records_list) > self.max_records:
            # 删除最旧的记录
            num_to_remove = len(self.records_list) - self.max_records
            old_records = self.records_list[:num_to_remove]
            
            for record in old_records:
                # 清理索引
                rid = None
                for record_id, r in self.records.items():
                    if r is record:
                        rid = record_id
                        break
                
                if rid:
                    # 从task_id_index删除
                    for task_id, rids in list(self.task_id_index.items()):
                        if rid in rids:
                            rids.remove(rid)
                            if not rids:
                                del self.task_id_index[task_id]
                    
                    # 从status_index删除
                    for status, rids in list(self.status_index.items()):
                        if rid in rids:
                            rids.remove(rid)
                            if not rids:
                                del self.status_index[status]
                    
                    # 从type_index删除
                    for type_name, rids in list(self.type_index.items()):
                        if rid in rids:
                            rids.remove(rid)
                            if not rids:
                                del self.type_index[type_name]
                    
                    # 从time_index删除
                    self.time_index = [(ts, r) for ts, r in self.time_index if r != rid]
                    
                    # 删除记录
                    del self.records[rid]
            
            # 更新列表
            self.records_list = self.records_list[num_to_remove:]


class TaskMetricsCollector:
    """指标收集器"""
    
    def __init__(self, history: Optional[TaskExecutionHistory] = None):
        self.history = history or TaskExecutionHistory()
        self.current_metrics = PerformanceMetrics()
        self._lock = threading.RLock()
        
        # 统计窗口
        self.start_time = time.time()
        self.window_start = time.time()
        self.window_tasks = 0
    
    def record_task_start(self, task_id: str, task_name: str, priority: int = 1, 
                          weight: int = 1, task_type: str = "default", 
                          trace_id: Optional[str] = None) -> TaskExecutionRecord:
        """记录任务开始"""
        with self._lock:
            record = TaskExecutionRecord(
                task_id=task_id,
                task_name=task_name,
                status=MonitorTaskStatus.RUNNING,
                start_time=time.time(),
                priority=priority,
                weight=weight,
                task_type=task_type,
                trace_id=trace_id
            )
            self.current_metrics.total_tasks += 1
            self.current_metrics.task_type_distribution[task_type] = \
                self.current_metrics.task_type_distribution.get(task_type, 0) + 1
            self.current_metrics.priority_distribution[priority] = \
                self.current_metrics.priority_distribution.get(priority, 0) + 1
            
            self.history.add_record(record)
            return record
    
    def record_task_complete(self, task_id: str, execution_time_ms: float, 
                             result_summary: Optional[Dict[str, Any]] = None,
                             wait_time_ms: Optional[float] = None,
                             queue_time_ms: Optional[float] = None) -> bool:
        """记录任务完成"""
        with self._lock:
            # 更新统计
            self.current_metrics.completed_tasks += 1
            self._update_execution_time_stats(execution_time_ms)
            
            if wait_time_ms is not None:
                self._update_wait_time_stats(wait_time_ms)
            
            if queue_time_ms is not None:
                self._update_queue_time_stats(queue_time_ms)
            
            self.window_tasks += 1
            self._update_throughput()
            self._update_success_rate()
            
            # 更新记录状态
            records = self.history.get_records_by_task_id(task_id)
            if records:
                record = records[-1]
                record.status = MonitorTaskStatus.COMPLETED
                record.end_time = time.time()
                record.execution_time_ms = execution_time_ms
                record.wait_time_ms = wait_time_ms
                record.queue_time_ms = queue_time_ms
                record.result_summary = result_summary
            
            return True
    
    def record_task_failed(self, task_id: str, error_message: str, 
                           execution_time_ms: Optional[float] = None) -> bool:
        """记录任务失败"""
        with self._lock:
            self.current_metrics.failed_tasks += 1
            self._update_success_rate()
            
            # 更新记录状态
            records = self.history.get_records_by_task_id(task_id)
            if records:
                record = records[-1]
                record.status = MonitorTaskStatus.FAILED
                record.end_time = time.time()
                record.execution_time_ms = execution_time_ms
                record.error_message = error_message
            
            return True
    
    def record_task_timeout(self, task_id: str, wait_time_ms: Optional[float] = None) -> bool:
        """记录任务超时"""
        with self._lock:
            self.current_metrics.timeout_tasks += 1
            self._update_success_rate()
            
            # 更新记录状态
            records = self.history.get_records_by_task_id(task_id)
            if records:
                record = records[-1]
                record.status = MonitorTaskStatus.TIMEOUT
                record.end_time = time.time()
                record.wait_time_ms = wait_time_ms
            
            return True
    
    def record_task_cancelled(self, task_id: str) -> bool:
        """记录任务取消"""
        with self._lock:
            self.current_metrics.cancelled_tasks += 1
            
            # 更新记录状态
            records = self.history.get_records_by_task_id(task_id)
            if records:
                record = records[-1]
                record.status = MonitorTaskStatus.CANCELLED
                record.end_time = time.time()
            
            return True
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """获取当前指标"""
        with self._lock:
            return self.current_metrics
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        with self._lock:
            return self.current_metrics.to_dict()
    
    def reset(self):
        """重置指标"""
        with self._lock:
            self.current_metrics = PerformanceMetrics()
            self.start_time = time.time()
            self.window_start = time.time()
            self.window_tasks = 0
            self.history.clear()
    
    def _update_execution_time_stats(self, execution_time_ms: float):
        """更新执行时间统计"""
        total = self.current_metrics.completed_tasks
        if total <= 0:
            self.current_metrics.avg_execution_time_ms = execution_time_ms
            self.current_metrics.max_execution_time_ms = execution_time_ms
            self.current_metrics.min_execution_time_ms = execution_time_ms
            return
        
        current_avg = self.current_metrics.avg_execution_time_ms
        new_avg = (current_avg * (total - 1) + execution_time_ms) / total
        self.current_metrics.avg_execution_time_ms = new_avg
        
        if execution_time_ms > self.current_metrics.max_execution_time_ms:
            self.current_metrics.max_execution_time_ms = execution_time_ms
        
        if execution_time_ms < self.current_metrics.min_execution_time_ms:
            self.current_metrics.min_execution_time_ms = execution_time_ms
    
    def _update_wait_time_stats(self, wait_time_ms: float):
        """更新等待时间统计"""
        total = self.current_metrics.completed_tasks
        if total <= 0:
            self.current_metrics.avg_wait_time_ms = wait_time_ms
            return
        
        current_avg = self.current_metrics.avg_wait_time_ms
        new_avg = (current_avg * (total - 1) + wait_time_ms) / total
        self.current_metrics.avg_wait_time_ms = new_avg
    
    def _update_queue_time_stats(self, queue_time_ms: float):
        """更新队列时间统计"""
        total = self.current_metrics.completed_tasks
        if total <= 0:
            self.current_metrics.avg_queue_time_ms = queue_time_ms
            return
        
        current_avg = self.current_metrics.avg_queue_time_ms
        new_avg = (current_avg * (total - 1) + queue_time_ms) / total
        self.current_metrics.avg_queue_time_ms = new_avg
    
    def _update_throughput(self):
        """更新吞吐量"""
        elapsed = time.time() - self.window_start
        if elapsed > 0:
            self.current_metrics.throughput_tasks_per_second = self.window_tasks / elapsed
    
    def _update_success_rate(self):
        """更新成功率"""
        total = self.current_metrics.total_tasks
        completed = self.current_metrics.completed_tasks
        if total > 0:
            self.current_metrics.success_rate = completed / total


class TaskMonitor:
    """任务监控器 - 集成历史记录和指标收集"""
    
    def __init__(self, max_history_records: int = 10000):
        self.history = TaskExecutionHistory(max_records=max_history_records)
        self.metrics = TaskMetricsCollector(self.history)
        self._lock = threading.RLock()
        
        # 回调函数
        self._on_status_change: Optional[Callable[[TaskExecutionRecord], None]] = None
        self._on_metric_update: Optional[Callable[[PerformanceMetrics], None]] = None
    
    def register_status_change_callback(self, callback: Callable[[TaskExecutionRecord], None]):
        """注册状态变化回调"""
        self._on_status_change = callback
    
    def register_metric_update_callback(self, callback: Callable[[PerformanceMetrics], None]):
        """注册指标更新回调"""
        self._on_metric_update = callback
    
    def on_task_start(self, task_id: str, task_name: str, priority: int = 1,
                      weight: int = 1, task_type: str = "default",
                      trace_id: Optional[str] = None) -> TaskExecutionRecord:
        """任务开始时调用"""
        record = self.metrics.record_task_start(
            task_id, task_name, priority, weight, task_type, trace_id
        )
        if self._on_status_change:
            self._on_status_change(record)
        if self._on_metric_update:
            self._on_metric_update(self.metrics.current_metrics)
        return record
    
    def on_task_complete(self, task_id: str, execution_time_ms: float,
                         result_summary: Optional[Dict[str, Any]] = None,
                         wait_time_ms: Optional[float] = None,
                         queue_time_ms: Optional[float] = None) -> bool:
        """任务完成时调用"""
        result = self.metrics.record_task_complete(
            task_id, execution_time_ms, result_summary, wait_time_ms, queue_time_ms
        )
        records = self.history.get_records_by_task_id(task_id)
        if records and self._on_status_change:
            self._on_status_change(records[-1])
        if self._on_metric_update:
            self._on_metric_update(self.metrics.current_metrics)
        return result
    
    def on_task_failed(self, task_id: str, error_message: str,
                       execution_time_ms: Optional[float] = None) -> bool:
        """任务失败时调用"""
        result = self.metrics.record_task_failed(task_id, error_message, execution_time_ms)
        records = self.history.get_records_by_task_id(task_id)
        if records and self._on_status_change:
            self._on_status_change(records[-1])
        if self._on_metric_update:
            self._on_metric_update(self.metrics.current_metrics)
        return result
    
    def on_task_timeout(self, task_id: str, wait_time_ms: Optional[float] = None) -> bool:
        """任务超时时调用"""
        result = self.metrics.record_task_timeout(task_id, wait_time_ms)
        records = self.history.get_records_by_task_id(task_id)
        if records and self._on_status_change:
            self._on_status_change(records[-1])
        if self._on_metric_update:
            self._on_metric_update(self.metrics.current_metrics)
        return result
    
    def on_task_cancelled(self, task_id: str) -> bool:
        """任务取消时调用"""
        result = self.metrics.record_task_cancelled(task_id)
        records = self.history.get_records_by_task_id(task_id)
        if records and self._on_status_change:
            self._on_status_change(records[-1])
        if self._on_metric_update:
            self._on_metric_update(self.metrics.current_metrics)
        return result
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        return self.metrics.get_metrics_summary()
    
    def get_history(self, limit: Optional[int] = None, 
                    status: Optional[MonitorTaskStatus] = None) -> List[Dict[str, Any]]:
        """获取历史记录"""
        if status:
            records = self.history.get_records_by_status(status)
        else:
            records = self.history.get_all_records()
        
        if limit:
            records = records[:limit]
        
        return [r.to_dict() for r in records]
    
    def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """获取指定任务的历史"""
        records = self.history.get_records_by_task_id(task_id)
        return [r.to_dict() for r in records]
    
    def clear(self):
        """清空所有数据"""
        self.metrics.reset()


def create_monitor(max_history_records: int = 10000) -> TaskMonitor:
    """创建任务监控器的工厂函数"""
    return TaskMonitor(max_history_records=max_history_records)
