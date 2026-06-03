"""
第74阶段：任务超时管理与死锁检测
实现任务超时控制、死锁检测与恢复机制

核心原则：图难于其易，为大于其细。天下难事，必作于易；天下大事，必作于细。
"""

import time
import threading
import functools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from enum import Enum
from collections import defaultdict
import queue


class TaskTimeoutStatus(Enum):
    """任务超时状态"""
    PENDING = "pending"
    RUNNING = "running"
    TIMEOUT = "timeout"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DeadlockStatus(Enum):
    """死锁状态"""
    SAFE = "safe"
    POTENTIAL = "potential"
    DEADLOCKED = "deadlocked"
    RESOLVING = "resolving"


@dataclass
class TaskTimeoutConfig:
    """超时配置"""
    default_timeout_seconds: float = 30.0
    enable_soft_timeout: bool = True
    soft_timeout_percentage: float = 0.8
    enable_hard_timeout: bool = True
    enable_timeout_callback: bool = True
    max_timeout_retries: int = 3
    cleanup_on_timeout: bool = True


@dataclass
class TaskTimeoutInfo:
    """任务超时信息"""
    task_id: str
    start_time: float
    timeout_seconds: float
    status: TaskTimeoutStatus
    thread_id: Optional[int] = None
    timeout_count: int = 0
    soft_timeout_triggered: bool = False
    hard_timeout_triggered: bool = False
    execution_callbacks: List[Callable] = field(default_factory=list)


class TaskTimeoutManager:
    """任务超时管理器"""

    def __init__(self, config: Optional[TaskTimeoutConfig] = None):
        self.config = config or TaskTimeoutConfig()
        self._tasks: Dict[str, TaskTimeoutInfo] = {}
        self._lock = threading.RLock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        self._timeout_queue: queue.Queue = queue.Queue()
        self._statistics = {
            "total_tasks": 0,
            "timeout_tasks": 0,
            "soft_timeouts": 0,
            "hard_timeouts": 0,
            "completed_tasks": 0
        }

    def start(self):
        """启动超时监控"""
        if self._running:
            return
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop(self):
        """停止超时监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)

    def register_task(
        self,
        task_id: str,
        timeout_seconds: Optional[float] = None,
        callbacks: Optional[List[Callable]] = None
    ):
        """注册任务"""
        with self._lock:
            timeout = timeout_seconds or self.config.default_timeout_seconds
            info = TaskTimeoutInfo(
                task_id=task_id,
                start_time=time.time(),
                timeout_seconds=timeout,
                status=TaskTimeoutStatus.RUNNING,
                thread_id=threading.get_ident(),
                execution_callbacks=callbacks or []
            )
            self._tasks[task_id] = info
            self._statistics["total_tasks"] += 1

    def unregister_task(self, task_id: str):
        """注销任务"""
        with self._lock:
            if task_id in self._tasks:
                info = self._tasks[task_id]
                if info.status == TaskTimeoutStatus.RUNNING:
                    info.status = TaskTimeoutStatus.COMPLETED
                    self._statistics["completed_tasks"] += 1
                del self._tasks[task_id]

    def mark_completed(self, task_id: str):
        """标记任务完成"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskTimeoutStatus.COMPLETED
                self._statistics["completed_tasks"] += 1

    def get_task_status(self, task_id: str) -> Optional[TaskTimeoutStatus]:
        """获取任务状态"""
        with self._lock:
            if task_id not in self._tasks:
                return None
            return self._tasks[task_id].status

    def is_task_timeout(self, task_id: str) -> bool:
        """检查任务是否超时"""
        with self._lock:
            if task_id not in self._tasks:
                return False
            info = self._tasks[task_id]
            if info.status != TaskTimeoutStatus.RUNNING:
                return False
            elapsed = time.time() - info.start_time
            return elapsed > info.timeout_seconds

    def get_timeout_duration(self, task_id: str) -> Optional[float]:
        """获取超时时长"""
        with self._lock:
            if task_id not in self._tasks:
                return None
            info = self._tasks[task_id]
            return time.time() - info.start_time - info.timeout_seconds

    def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                self._check_timeouts()
                time.sleep(0.5)
            except Exception:
                pass

    def _check_timeouts(self):
        """检查超时任务"""
        with self._lock:
            now = time.time()
            for task_id, info in self._tasks.items():
                if info.status != TaskTimeoutStatus.RUNNING:
                    continue

                elapsed = now - info.start_time
                timeout_threshold = info.timeout_seconds

                if self.config.enable_soft_timeout:
                    soft_threshold = timeout_threshold * self.config.soft_timeout_percentage
                    if elapsed >= soft_threshold and not info.soft_timeout_triggered:
                        info.soft_timeout_triggered = True
                        self._statistics["soft_timeouts"] += 1
                        self._trigger_callbacks(info, "soft_timeout")

                if self.config.enable_hard_timeout:
                    if elapsed >= timeout_threshold:
                        info.status = TaskTimeoutStatus.TIMEOUT
                        info.hard_timeout_triggered = True
                        self._statistics["timeout_tasks"] += 1
                        self._statistics["hard_timeouts"] += 1
                        self._timeout_queue.put(task_id)
                        self._trigger_callbacks(info, "hard_timeout")

    def _trigger_callbacks(self, info: TaskTimeoutInfo, event: str):
        """触发回调"""
        for callback in info.execution_callbacks:
            try:
                callback(info.task_id, event, info)
            except Exception:
                pass

    def get_timed_out_tasks(self) -> List[str]:
        """获取超时任务列表"""
        with self._lock:
            return [
                task_id for task_id, info in self._tasks.items()
                if info.status == TaskTimeoutStatus.TIMEOUT
            ]

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                **self._statistics,
                "active_tasks": sum(
                    1 for info in self._tasks.values()
                    if info.status == TaskTimeoutStatus.RUNNING
                ),
                "total_registered": len(self._tasks)
            }


@dataclass
class ResourceLock:
    """资源锁"""
    resource_id: str
    holder_task_id: str
    acquired_time: float
    lock_type: str = "exclusive"
    is_held: bool = True


class DeadlockDetector:
    """死锁检测器"""

    def __init__(self):
        self._locks: Dict[str, ResourceLock] = {}
        self._task_locks: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.RLock()
        self._wait_graph: Dict[str, Set[str]] = defaultdict(set)
        self._detection_enabled = True
        self._status = DeadlockStatus.SAFE
        self._last_detection_time: Optional[float] = None
        self._statistics = {
            "total_acquires": 0,
            "total_releases": 0,
            "deadlocks_detected": 0,
            "deadlocks_resolved": 0,
            "potential_deadlocks": 0
        }

    def acquire_lock(
        self,
        resource_id: str,
        task_id: str,
        timeout_seconds: float = 10.0
    ) -> bool:
        """尝试获取锁"""
        with self._lock:
            self._statistics["total_acquires"] += 1

            if resource_id not in self._locks:
                self._locks[resource_id] = ResourceLock(
                    resource_id=resource_id,
                    holder_task_id=task_id,
                    acquired_time=time.time()
                )
                self._task_locks[task_id].add(resource_id)
                return True

            existing_lock = self._locks[resource_id]
            if not existing_lock.is_held or existing_lock.holder_task_id == task_id:
                return True

            self._wait_graph[task_id].add(existing_lock.holder_task_id)

            start_time = time.time()
            while (time.time() - start_time) < timeout_seconds:
                if not self._locks[resource_id].is_held:
                    break
                time.sleep(0.1)
            else:
                self._statistics["potential_deadlocks"] += 1
                self._check_and_handle_deadlock()
                return False

            self._locks[resource_id] = ResourceLock(
                resource_id=resource_id,
                holder_task_id=task_id,
                acquired_time=time.time()
            )
            self._task_locks[task_id].add(resource_id)
            if task_id in self._wait_graph:
                self._wait_graph[task_id].discard(existing_lock.holder_task_id)
            return True

    def release_lock(self, resource_id: str, task_id: str) -> bool:
        """释放锁"""
        with self._lock:
            if resource_id not in self._locks:
                return False

            lock = self._locks[resource_id]
            if lock.holder_task_id != task_id:
                return False

            lock.is_held = False
            self._task_locks[task_id].discard(resource_id)
            self._statistics["total_releases"] += 1
            return True

    def release_all_locks(self, task_id: str) -> int:
        """释放任务持有的所有锁"""
        with self._lock:
            released = 0
            for resource_id in list(self._task_locks[task_id]):
                if self.release_lock(resource_id, task_id):
                    released += 1
            return released

    def _check_and_handle_deadlock(self):
        """检测和处理死锁"""
        if not self._detection_enabled:
            return

        deadlock = self._detect_deadlock()
        if deadlock:
            self._status = DeadlockStatus.DEADLOCKED
            self._statistics["deadlocks_detected"] += 1
            self._resolve_deadlock(deadlock)

    def _detect_deadlock(self) -> Optional[List[str]]:
        """检测死锁（使用等待图）"""
        visited = set()
        rec_stack = set()

        def dfs(task_id: str, path: List[str]) -> Optional[List[str]]:
            visited.add(task_id)
            rec_stack.add(task_id)
            path.append(task_id)

            for waiting_for in self._wait_graph.get(task_id, set()):
                if waiting_for not in visited:
                    result = dfs(waiting_for, path[:])
                    if result:
                        return result
                elif waiting_for in rec_stack:
                    cycle_start = path.index(waiting_for)
                    return path[cycle_start:]

            rec_stack.remove(task_id)
            return None

        for task_id in self._wait_graph:
            if task_id not in visited:
                cycle = dfs(task_id, [])
                if cycle:
                    return cycle

        return None

    def _resolve_deadlock(self, deadlock_cycle: List[str]):
        """解决死锁"""
        self._status = DeadlockStatus.RESOLVING

        victim_task = deadlock_cycle[-1]
        print(f"死锁检测: 发现循环 {deadlock_cycle}")
        print(f"死锁解决: 选择任务 {victim_task} 作为牺牲者")

        self.release_all_locks(victim_task)

        self._status = DeadlockStatus.SAFE
        self._statistics["deadlocks_resolved"] += 1

    def get_task_locks(self, task_id: str) -> Set[str]:
        """获取任务持有的锁"""
        with self._lock:
            return self._task_locks.get(task_id, set()).copy()

    def get_resource_lock(self, resource_id: str) -> Optional[ResourceLock]:
        """获取资源锁信息"""
        with self._lock:
            return self._locks.get(resource_id)

    def get_waiting_tasks(self, task_id: str) -> Set[str]:
        """获取任务等待的锁持有者"""
        with self._lock:
            return self._wait_graph.get(task_id, set()).copy()

    def get_status(self) -> DeadlockStatus:
        """获取当前状态"""
        return self._status

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                **self._statistics,
                "current_status": self._status.value,
                "total_locks": len(self._locks),
                "total_tasks_with_locks": len(self._task_locks),
                "last_detection_time": self._last_detection_time
            }

    def reset(self):
        """重置检测器"""
        with self._lock:
            self._locks.clear()
            self._task_locks.clear()
            self._wait_graph.clear()
            self._status = DeadlockStatus.SAFE
            self._statistics = {
                "total_acquires": 0,
                "total_releases": 0,
                "deadlocks_detected": 0,
                "deadlocks_resolved": 0,
                "potential_deadlocks": 0
            }


class TimeoutDeadlockManager:
    """超时与死锁统一管理器"""

    def __init__(
        self,
        timeout_config: Optional[TaskTimeoutConfig] = None
    ):
        self.timeout_manager = TaskTimeoutManager(timeout_config)
        self.deadlock_detector = DeadlockDetector()
        self._lock = threading.RLock()

    def start(self):
        """启动管理器"""
        self.timeout_manager.start()

    def stop(self):
        """停止管理器"""
        self.timeout_manager.stop()

    def register_task(
        self,
        task_id: str,
        timeout_seconds: Optional[float] = None,
        callbacks: Optional[List[Callable]] = None
    ):
        """注册任务"""
        self.timeout_manager.register_task(task_id, timeout_seconds, callbacks)

    def acquire_resource(
        self,
        task_id: str,
        resource_id: str,
        timeout_seconds: float = 10.0
    ) -> bool:
        """获取资源"""
        return self.deadlock_detector.acquire_lock(resource_id, task_id, timeout_seconds)

    def release_resource(self, task_id: str, resource_id: str) -> bool:
        """释放资源"""
        return self.deadlock_detector.release_lock(resource_id, task_id)

    def complete_task(self, task_id: str):
        """完成任务"""
        self.deadlock_detector.release_all_locks(task_id)
        self.timeout_manager.unregister_task(task_id)

    def get_all_statistics(self) -> Dict[str, Any]:
        """获取所有统计"""
        with self._lock:
            return {
                "timeout": self.timeout_manager.get_statistics(),
                "deadlock": self.deadlock_detector.get_statistics()
            }


def create_timeout_manager(config: Optional[TaskTimeoutConfig] = None) -> TaskTimeoutManager:
    """创建超时管理器"""
    return TaskTimeoutManager(config)


def create_deadlock_detector() -> DeadlockDetector:
    """创建死锁检测器"""
    return DeadlockDetector()


def create_timeout_deadlock_manager(config: Optional[TaskTimeoutConfig] = None) -> TimeoutDeadlockManager:
    """创建统一管理器"""
    return TimeoutDeadlockManager(config)
