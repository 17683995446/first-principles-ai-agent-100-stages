"""
第69阶段：任务优先级动态调整
实现任务优先级的动态调整策略，包括老化、自适应、学习等机制
"""

import time
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from .task_scheduler import TaskPriority
from .task_monitor import MonitorTaskStatus


class PriorityAdjustmentStrategy(Enum):
    """优先级调整策略"""
    AGING = "aging"                  # 老化策略
    ADAPTIVE = "adaptive"            # 自适应策略
    LEARNING = "learning"            # 学习策略
    DEADLINE_DRIVEN = "deadline"     # 截止日期驱动策略


@dataclass
class TaskPriorityConfig:
    """任务优先级配置"""
    min_priority: int = 1
    max_priority: int = 10
    aging_factor: float = 0.1         # 老化因子
    max_age_bonus: float = 5.0       # 最大老化奖励
    adaptive_threshold: float = 0.5  # 自适应阈值
    adjustment_step: float = 0.5     # 调整步长
    check_interval: float = 1.0      # 检查间隔（秒）
    enable_auto_adjust: bool = True  # 启用自动调整


@dataclass
class TaskPriorityState:
    """任务优先级状态"""
    task_id: str
    original_priority: float
    current_priority: float
    queue_entry_time: float = field(default_factory=time.time)
    last_adjustment_time: float = field(default_factory=time.time)
    retry_count: int = 0
    success_rate: float = 1.0
    avg_execution_time: float = 0.0
    deadline: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    priority_history: List[tuple] = field(default_factory=list)
    
    def get_queue_age_seconds(self) -> float:
        """获取队列中等待时间"""
        return time.time() - self.queue_entry_time
    
    def record_priority_change(self, old_priority: float, new_priority: float, reason: str):
        """记录优先级变化"""
        self.priority_history.append((time.time(), old_priority, new_priority, reason))


class PriorityAdjustmentRule:
    """优先级调整规则"""
    
    def __init__(self, name: str, condition: Callable, adjustment: Callable):
        self.name = name
        self.condition = condition  # 条件判断函数
        self.adjustment = adjustment  # 调整函数


class DynamicPriorityManager:
    """动态优先级管理器"""
    
    def __init__(self, config: Optional[TaskPriorityConfig] = None):
        self.config = config or TaskPriorityConfig()
        self.task_states: Dict[str, TaskPriorityState] = {}
        self.rules: List[PriorityAdjustmentRule] = []
        self._lock = threading.RLock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        self._statistics = defaultdict(int)
        
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """设置默认调整规则"""
        # 规则1：老化提升优先级
        def aging_condition(state: TaskPriorityState) -> bool:
            age = state.get_queue_age_seconds()
            return age > 10.0  # 超过10秒开始老化
        
        def aging_adjustment(state: TaskPriorityState) -> float:
            age = state.get_queue_age_seconds()
            bonus = min(age * self.config.aging_factor, self.config.max_age_bonus)
            return state.current_priority + bonus
        
        self.rules.append(PriorityAdjustmentRule(
            "aging", aging_condition, aging_adjustment
        ))
        
        # 规则2：重试次数增加优先级
        def retry_condition(state: TaskPriorityState) -> bool:
            return state.retry_count > 0
        
        def retry_adjustment(state: TaskPriorityState) -> float:
            bonus = min(state.retry_count * 0.5, 3.0)
            return state.current_priority + bonus
        
        self.rules.append(PriorityAdjustmentRule(
            "retry_bonus", retry_condition, retry_adjustment
        ))
        
        # 规则3：截止日期驱动
        def deadline_condition(state: TaskPriorityState) -> bool:
            if state.deadline is None:
                return False
            time_left = state.deadline - time.time()
            return time_left < 300.0  # 5分钟内
        
        def deadline_adjustment(state: TaskPriorityState) -> float:
            time_left = state.deadline - time.time()
            urgency = max(0.0, (300.0 - time_left) / 300.0)  # 0-1
            bonus = urgency * 5.0  # 最大提升5
            return state.current_priority + bonus
        
        self.rules.append(PriorityAdjustmentRule(
            "deadline_driven", deadline_condition, deadline_adjustment
        ))
        
        # 规则4：失败率高的任务降权
        def failure_condition(state: TaskPriorityState) -> bool:
            return state.success_rate < 0.7
        
        def failure_adjustment(state: TaskPriorityState) -> float:
            penalty = (1.0 - state.success_rate) * 2.0
            return state.current_priority - penalty
        
        self.rules.append(PriorityAdjustmentRule(
            "failure_penalty", failure_condition, failure_adjustment
        ))
    
    def register_task(self, task_id: str, priority: float, 
                     deadline: Optional[float] = None,
                     tags: Optional[List[str]] = None):
        """注册任务"""
        with self._lock:
            state = TaskPriorityState(
                task_id=task_id,
                original_priority=priority,
                current_priority=priority,
                deadline=deadline,
                tags=tags or []
            )
            self.task_states[task_id] = state
            return state
    
    def update_task_state(self, task_id: str, 
                         success: bool, 
                         execution_time: Optional[float] = None):
        """更新任务状态"""
        with self._lock:
            if task_id not in self.task_states:
                return
            
            state = self.task_states[task_id]
            
            if not success:
                state.retry_count += 1
            
            # 更新成功率
            total = len(state.priority_history) + 1
            state.success_rate = (state.success_rate * (total - 1) + 
                                 (1.0 if success else 0.0)) / total
            
            # 更新平均执行时间
            if execution_time:
                count = total
                state.avg_execution_time = (
                    state.avg_execution_time * (count - 1) + execution_time
                ) / count
    
    def calculate_adjusted_priority(self, task_id: str) -> float:
        """计算调整后的优先级"""
        with self._lock:
            if task_id not in self.task_states:
                return 1.0
            
            state = self.task_states[task_id]
            old_priority = state.current_priority
            new_priority = old_priority
            
            # 应用所有规则
            for rule in self.rules:
                if rule.condition(state):
                    new_priority = rule.adjustment(state)
            
            # 限制范围
            new_priority = max(self.config.min_priority, 
                              min(self.config.max_priority, new_priority))
            
            # 记录变化
            if abs(new_priority - old_priority) > 0.01:
                state.record_priority_change(old_priority, new_priority, 
                                            "multiple_rules")
                state.current_priority = new_priority
                state.last_adjustment_time = time.time()
                self._statistics["adjustments"] += 1
            
            return new_priority
    
    def get_task_priority(self, task_id: str) -> float:
        """获取任务当前优先级"""
        with self._lock:
            if task_id in self.task_states:
                return self.task_states[task_id].current_priority
            return 1.0
    
    def add_custom_rule(self, name: str, 
                       condition: Callable[[TaskPriorityState], bool],
                       adjustment: Callable[[TaskPriorityState], float]):
        """添加自定义规则"""
        with self._lock:
            rule = PriorityAdjustmentRule(name, condition, adjustment)
            self.rules.append(rule)
    
    def start_monitor(self):
        """启动监控线程"""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitor(self):
        """停止监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
    
    def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                if self.config.enable_auto_adjust:
                    for task_id in list(self.task_states.keys()):
                        self.calculate_adjusted_priority(task_id)
                
                self._statistics["cycles"] += 1
                time.sleep(self.config.check_interval)
            except Exception as e:
                print(f"监控异常: {e}")
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        with self._lock:
            return {
                "tracked_tasks": len(self.task_states),
                "adjustments": self._statistics.get("adjustments", 0),
                "cycles": self._statistics.get("cycles", 0),
                "avg_priority": sum(s.current_priority for s in self.task_states.values()) 
                               / len(self.task_states) if self.task_states else 0.0
            }
    
    def clear_tasks(self):
        """清除所有任务状态"""
        with self._lock:
            self.task_states.clear()


class PriorityAwareScheduler:
    """优先级感知调度器 - 集成调度器与动态优先级"""
    
    def __init__(self, scheduler_config=None, priority_config=None):
        from first_principles_agent.integrated_scheduler import IntegratedTaskScheduler
        self.scheduler = IntegratedTaskScheduler(
            scheduler_config=scheduler_config
        )
        self.priority_manager = DynamicPriorityManager(
            config=priority_config
        )
        self._lock = threading.RLock()
    
    def submit_task(self, task, priority, task_config=None, 
                   task_type="default", weight=1, deadline=None, tags=None):
        """提交任务，支持优先级和截止日期"""
        with self._lock:
            # 注册到优先级管理器
            task_id = getattr(task, 'task_id', str(id(task)))
            
            self.priority_manager.register_task(
                task_id=task_id,
                priority=priority,
                deadline=deadline,
                tags=tags
            )
            
            # 获取动态优先级并提交
            dynamic_priority = self.priority_manager.get_task_priority(task_id)
            
            return self.scheduler.submit_task(
                task,
                dynamic_priority,
                task_config,
                task_type,
                weight
            )
    
    def update_task_priority(self, task_id: str):
        """更新任务优先级"""
        with self._lock:
            return self.priority_manager.calculate_adjusted_priority(task_id)
    
    def get_statistics(self):
        """获取统计信息"""
        priority_stats = self.priority_manager.get_statistics()
        scheduler_stats = self.scheduler.get_stats().to_dict()
        return {
            "priority": priority_stats,
            "scheduler": scheduler_stats
        }
    
    def start(self):
        """启动"""
        self.priority_manager.start_monitor()
        self.scheduler.start()
    
    def stop(self):
        """停止"""
        self.priority_manager.stop_monitor()
        self.scheduler.stop()


def create_priority_config(
    min_priority: int = 1,
    max_priority: int = 10,
    aging_factor: float = 0.1,
    enable_auto_adjust: bool = True
) -> TaskPriorityConfig:
    """创建优先级配置的工厂函数"""
    return TaskPriorityConfig(
        min_priority=min_priority,
        max_priority=max_priority,
        aging_factor=aging_factor,
        enable_auto_adjust=enable_auto_adjust
    )
