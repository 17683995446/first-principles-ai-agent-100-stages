"""
第68阶段：任务重试机制与错误恢复策略
提供完整的任务重试、错误分类、退避策略和恢复机制
"""

import time
import uuid
import threading
from typing import Dict, Any, List, Optional, Callable, Set
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import random


class RetryStrategy(Enum):
    """重试策略"""
    IMMEDIATE = "immediate"  # 立即重试
    FIXED_DELAY = "fixed_delay"  # 固定延迟
    LINEAR_BACKOFF = "linear_backoff"  # 线性退避
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # 指数退避
    FIBONACCI_BACKOFF = "fibonacci_backoff"  # 斐波那契退避


class ErrorCategory(Enum):
    """错误分类"""
    TRANSIENT = "transient"  # 瞬时错误（网络、资源）
    LOGICAL = "logical"  # 逻辑错误（输入、数据）
    RESOURCE = "resource"  # 资源错误（内存、CPU）
    SYSTEM = "system"  # 系统错误（崩溃、超时）
    UNKNOWN = "unknown"  # 未知错误


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3  # 最大尝试次数
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay_seconds: float = 1.0  # 基础延迟
    max_delay_seconds: float = 60.0  # 最大延迟
    jitter: bool = True  # 是否添加抖动
    jitter_range: float = 0.3  # 抖动范围
    retryable_errors: Set[str] = field(default_factory=set)  # 可重试的错误
    fatal_errors: Set[str] = field(default_factory=set)  # 致命错误（不重试）
    
    def __post_init__(self):
        if not self.retryable_errors:
            self.retryable_errors = {
                "timeout", "connection_error", "network_error",
                "resource_unavailable", "temporary_failure"
            }
        if not self.fatal_errors:
            self.fatal_errors = {
                "validation_error", "illegal_argument", "unauthorized",
                "not_found", "permission_denied"
            }


@dataclass
class RetryAttempt:
    """重试尝试记录"""
    attempt_number: int
    timestamp: float
    error_message: str
    error_category: ErrorCategory
    delay_applied: float
    success: bool = False
    execution_time_ms: Optional[float] = None


@dataclass
class TaskRetryState:
    """任务重试状态"""
    task_id: str
    current_attempt: int = 0
    retry_history: List[RetryAttempt] = field(default_factory=list)
    next_retry_time: Optional[float] = None
    is_retrying: bool = False
    final_failure: bool = False
    
    def add_attempt(self, attempt: RetryAttempt):
        self.retry_history.append(attempt)
        self.current_attempt = attempt.attempt_number
    
    def should_retry(self, max_attempts: int) -> bool:
        return (
            not self.final_failure and
            self.current_attempt < max_attempts and
            not attempt.success for attempt in [self.retry_history[-1]] if self.retry_history
        )
    
    def mark_final_failure(self):
        self.final_failure = True
        self.is_retrying = False


class RetryManager:
    """重试管理器"""
    
    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        on_retry: Optional[Callable[[str, int, str], None]] = None,
        on_final_failure: Optional[Callable[[str, List[RetryAttempt]], None]] = None
    ):
        self.config = config or RetryConfig()
        self.on_retry = on_retry
        self.on_final_failure = on_final_failure
        
        self.retry_states: Dict[str, TaskRetryState] = {}
        self.pending_retries: Dict[str, threading.Timer] = {}
        self._lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            "total_retries": 0,
            "successful_retries": 0,
            "final_failures": 0,
            "retry_by_category": defaultdict(int)
        }
    
    def should_retry(
        self,
        task_id: str,
        error_message: str
    ) -> bool:
        """判断是否应该重试"""
        with self._lock:
            error_lower = error_message.lower()
            
            # 检查是否为致命错误
            for fatal in self.config.fatal_errors:
                if fatal in error_lower:
                    return False
            
            # 检查是否为可重试错误
            for retryable in self.config.retryable_errors:
                if retryable in error_lower:
                    return True
            
            # 默认认为其他错误可以重试
            return True
    
    def categorize_error(self, error_message: str) -> ErrorCategory:
        """分类错误"""
        error_lower = error_message.lower()
        
        transient_keywords = ["timeout", "connection", "network", "temporary", "unavailable"]
        for keyword in transient_keywords:
            if keyword in error_lower:
                return ErrorCategory.TRANSIENT
        
        logical_keywords = ["invalid", "illegal", "wrong", "malformed", "parse"]
        for keyword in logical_keywords:
            if keyword in error_lower:
                return ErrorCategory.LOGICAL
        
        resource_keywords = ["memory", "cpu", "disk", "resource", "overflow"]
        for keyword in resource_keywords:
            if keyword in error_lower:
                return ErrorCategory.RESOURCE
        
        system_keywords = ["crash", "fatal", "panic", "abort", "segmentation"]
        for keyword in system_keywords:
            if keyword in error_lower:
                return ErrorCategory.SYSTEM
        
        return ErrorCategory.UNKNOWN
    
    def calculate_delay(self, attempt_number: int) -> float:
        """计算重试延迟"""
        base_delay = self.config.base_delay_seconds
        max_delay = self.config.max_delay_seconds
        
        if self.config.strategy == RetryStrategy.IMMEDIATE:
            delay = 0
        elif self.config.strategy == RetryStrategy.FIXED_DELAY:
            delay = base_delay
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = base_delay * attempt_number
        elif self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = base_delay * (2 ** (attempt_number - 1))
        elif self.config.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            delay = self._fibonacci(attempt_number) * base_delay
        else:
            delay = base_delay
        
        # 限制最大延迟
        delay = min(delay, max_delay)
        
        # 添加抖动
        if self.config.jitter:
            jitter_amount = delay * self.config.jitter_range
            delay += random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay)
        
        return delay
    
    def _fibonacci(self, n: int) -> float:
        """计算斐波那契数"""
        if n <= 1:
            return 1.0
        a, b = 1.0, 1.0
        for _ in range(n - 1):
            a, b = b, a + b
        return b
    
    def schedule_retry(
        self,
        task_id: str,
        error_message: str,
        execution_time_ms: Optional[float] = None,
        executor: Optional[Callable[[], Any]] = None
    ) -> bool:
        """安排重试"""
        with self._lock:
            # 获取或创建重试状态
            if task_id not in self.retry_states:
                self.retry_states[task_id] = TaskRetryState(task_id=task_id)
            
            state = self.retry_states[task_id]
            state.current_attempt += 1
            
            # 分类错误
            error_category = self.categorize_error(error_message)
            
            # 计算延迟
            delay = self.calculate_delay(state.current_attempt)
            next_retry_time = time.time() + delay
            
            # 记录尝试
            attempt = RetryAttempt(
                attempt_number=state.current_attempt,
                timestamp=time.time(),
                error_message=error_message,
                error_category=error_category,
                delay_applied=delay
            )
            state.add_attempt(attempt)
            state.next_retry_time = next_retry_time
            
            # 更新统计
            self.stats["total_retries"] += 1
            self.stats["retry_by_category"][error_category.value] += 1
            
            # 回调
            if self.on_retry:
                self.on_retry(task_id, state.current_attempt, error_message)
            
            # 检查是否超过最大尝试次数
            if state.current_attempt >= self.config.max_attempts:
                state.mark_final_failure()
                self.stats["final_failures"] += 1
                
                if self.on_final_failure:
                    self.on_final_failure(task_id, state.retry_history)
                
                return False
            
            # 安排定时器
            timer = threading.Timer(
                delay,
                self._execute_retry,
                args=(task_id, executor)
            )
            self.pending_retries[task_id] = timer
            timer.start()
            
            return True
    
    def _execute_retry(self, task_id: str, executor: Optional[Callable[[], Any]]):
        """执行重试"""
        with self._lock:
            if task_id in self.retry_states:
                state = self.retry_states[task_id]
                state.is_retrying = True
            
            if task_id in self.pending_retries:
                del self.pending_retries[task_id]
    
    def cancel_retry(self, task_id: str) -> bool:
        """取消重试"""
        with self._lock:
            if task_id in self.pending_retries:
                self.pending_retries[task_id].cancel()
                del self.pending_retries[task_id]
                return True
            return False
    
    def mark_success(self, task_id: str):
        """标记任务成功"""
        with self._lock:
            if task_id in self.retry_states:
                state = self.retry_states[task_id]
                if state.retry_history:
                    state.retry_history[-1].success = True
                self.stats["successful_retries"] += 1
            
            self.cancel_retry(task_id)
    
    def get_retry_state(self, task_id: str) -> Optional[TaskRetryState]:
        """获取重试状态"""
        with self._lock:
            return self.retry_states.get(task_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                **self.stats,
                "pending_retries": len(self.pending_retries),
                "active_retry_states": len(self.retry_states)
            }
    
    def clear(self):
        """清空所有状态"""
        with self._lock:
            # 取消所有待处理的重试
            for timer in self.pending_retries.values():
                timer.cancel()
            self.pending_retries.clear()
            self.retry_states.clear()
            self.stats = {
                "total_retries": 0,
                "successful_retries": 0,
                "final_failures": 0,
                "retry_by_category": defaultdict(int)
            }


@dataclass
class RecoveryCheckpoint:
    """恢复检查点"""
    task_id: str
    checkpoint_id: str
    timestamp: float
    state_data: Dict[str, Any]
    completed_steps: List[str]


class RecoveryManager:
    """恢复管理器 - 支持任务执行中途恢复"""
    
    def __init__(self, max_checkpoints_per_task: int = 10):
        self.max_checkpoints = max_checkpoints_per_task
        self.checkpoints: Dict[str, List[RecoveryCheckpoint]] = defaultdict(list)
        self._lock = threading.RLock()
    
    def save_checkpoint(
        self,
        task_id: str,
        state_data: Dict[str, Any],
        completed_steps: Optional[List[str]] = None
    ) -> str:
        """保存检查点"""
        with self._lock:
            checkpoint_id = str(uuid.uuid4())
            checkpoint = RecoveryCheckpoint(
                task_id=task_id,
                checkpoint_id=checkpoint_id,
                timestamp=time.time(),
                state_data=state_data,
                completed_steps=completed_steps or []
            )
            
            self.checkpoints[task_id].append(checkpoint)
            
            # 限制检查点数量
            if len(self.checkpoints[task_id]) > self.max_checkpoints:
                self.checkpoints[task_id].pop(0)
            
            return checkpoint_id
    
    def get_latest_checkpoint(self, task_id: str) -> Optional[RecoveryCheckpoint]:
        """获取最新的检查点"""
        with self._lock:
            checkpoints = self.checkpoints.get(task_id, [])
            return checkpoints[-1] if checkpoints else None
    
    def get_checkpoint(self, task_id: str, checkpoint_id: str) -> Optional[RecoveryCheckpoint]:
        """获取指定的检查点"""
        with self._lock:
            for checkpoint in self.checkpoints.get(task_id, []):
                if checkpoint.checkpoint_id == checkpoint_id:
                    return checkpoint
            return None
    
    def list_checkpoints(self, task_id: str) -> List[RecoveryCheckpoint]:
        """列出任务的所有检查点"""
        with self._lock:
            return list(self.checkpoints.get(task_id, []))
    
    def delete_checkpoints(self, task_id: str) -> int:
        """删除任务的所有检查点"""
        with self._lock:
            count = len(self.checkpoints.get(task_id, []))
            if task_id in self.checkpoints:
                del self.checkpoints[task_id]
            return count
    
    def clear(self):
        """清空所有检查点"""
        with self._lock:
            self.checkpoints.clear()


def create_retry_config(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    enable_jitter: bool = True
) -> RetryConfig:
    """创建重试配置的辅助函数"""
    return RetryConfig(
        max_attempts=max_attempts,
        strategy=strategy,
        base_delay_seconds=base_delay,
        max_delay_seconds=max_delay,
        jitter=enable_jitter
    )
