
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
import json
import time


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ConstraintType(Enum):
    """约束类型枚举"""
    MAX_STEPS = "max_steps"
    MAX_ITEMS = "max_items"
    TIME_LIMIT = "time_limit"
    MEMORY_LIMIT = "memory_limit"
    NETWORK_RESTRICTED = "network_restricted"
    FILE_RESTRICTED = "file_restricted"
    CUSTOM = "custom"


class PreconditionType(Enum):
    """前置条件类型"""
    FILE_EXISTS = "file_exists"
    DIRECTORY_EXISTS = "directory_exists"
    VARIABLE_SET = "variable_set"
    API_AVAILABLE = "api_available"
    CUSTOM = "custom"


class ValidationError:
    """验证错误详情"""
    def __init__(self, field: str, message: str, severity: str = "error"):
        self.field = field
        self.message = message
        self.severity = severity
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity
        }


class Constraint:
    """约束条件"""
    def __init__(
        self,
        constraint_type: ConstraintType,
        value: Any,
        description: str = "",
        enabled: bool = True
    ):
        self.type = constraint_type
        self.value = value
        self.description = description
        self.enabled = enabled
    
    def is_satisfied(self, context: Dict[str, Any]) -> bool:
        """检查约束是否满足"""
        if not self.enabled:
            return True
        
        try:
            if self.type == ConstraintType.MAX_STEPS:
                return context.get("step_count", 0) <= self.value
            elif self.type == ConstraintType.MAX_ITEMS:
                return len(context.get("items", [])) <= self.value
            elif self.type == ConstraintType.TIME_LIMIT:
                return context.get("elapsed_time", 0) <= self.value
            elif self.type == ConstraintType.MEMORY_LIMIT:
                return context.get("memory_usage", 0) <= self.value
            elif self.type == ConstraintType.NETWORK_RESTRICTED:
                return not context.get("network_access", False)
            elif self.type == ConstraintType.FILE_RESTRICTED:
                return context.get("file_access_allowed", True)
            return True
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "value": self.value,
            "description": self.description,
            "enabled": self.enabled
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Constraint':
        """从字典创建"""
        return Constraint(
            constraint_type=ConstraintType(data.get("type", "max_steps")),
            value=data.get("value"),
            description=data.get("description", ""),
            enabled=data.get("enabled", True)
        )


class Precondition:
    """前置条件"""
    def __init__(
        self,
        check_func: Callable[[Dict[str, Any]], bool],
        precondition_type: PreconditionType = PreconditionType.CUSTOM,
        description: str = "",
        required: bool = True
    ):
        self.check_func = check_func
        self.type = precondition_type
        self.description = description
        self.required = required
    
    def is_satisfied(self, context: Dict[str, Any]) -> bool:
        """检查前置条件是否满足"""
        try:
            return self.check_func(context)
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "description": self.description,
            "required": self.required
        }


class EndRule:
    """终止规则"""
    def __init__(
        self,
        end_func: Callable[[Dict[str, Any]], bool],
        description: str = "",
        timeout_seconds: Optional[float] = None
    ):
        self.end_func = end_func
        self.description = description
        self.timeout_seconds = timeout_seconds
        self.start_time = None
    
    def start_timer(self):
        """开始计时"""
        self.start_time = time.time()
    
    def check_timeout(self) -> bool:
        """检查是否超时"""
        if self.timeout_seconds is None:
            return False
        if self.start_time is None:
            return False
        return (time.time() - self.start_time) > self.timeout_seconds
    
    def is_ended(self, context: Dict[str, Any]) -> bool:
        """检查是否终止"""
        if self.check_timeout():
            return True
        try:
            return self.end_func(context)
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "description": self.description,
            "timeout_seconds": self.timeout_seconds
        }


class TaskQuartet:
    """
    任务四元组
    - Target: 唯一、明确、可验证的目标
    - Preconditions: 前置条件列表
    - Constraints: 约束条件列表
    - EndRule: 终止规则
    """
    def __init__(
        self,
        target: str,
        preconditions: Optional[List[Precondition]] = None,
        constraints: Optional[List[Constraint]] = None,
        end_rule: Optional[EndRule] = None
    ):
        self.target = target
        self.preconditions = preconditions or []
        self.constraints = constraints or []
        self.end_rule = end_rule
        self.metadata = {}
    
    def validate(self) -> tuple:
        """验证四元组完整性"""
        errors = []
        warnings = []
        
        # 验证 Target
        if not self.target or len(self.target.strip()) < 2:
            errors.append(ValidationError("target", "Target must be at least 2 characters"))
        
        # 检查 Target 是否模糊
        vague_indicators = ["随便", "等等", "看看", "弄一下", "搞一下"]
        if any(indicator in self.target for indicator in vague_indicators):
            warnings.append(ValidationError(
                "target",
                "Target may be vague",
                severity="warning"
            ))
        
        # 验证 EndRule
        if self.end_rule is None:
            warnings.append(ValidationError(
                "end_rule",
                "No end rule defined, task may never complete",
                severity="warning"
            ))
        
        return len(errors) == 0, errors, warnings
    
    def check_preconditions(self, context: Dict[str, Any]) -> tuple:
        """检查前置条件"""
        failed = []
        for pc in self.preconditions:
            if not pc.is_satisfied(context):
                failed.append(pc)
        
        return len(failed) == 0, failed
    
    def check_constraints(self, context: Dict[str, Any]) -> tuple:
        """检查约束条件"""
        violated = []
        for c in self.constraints:
            if not c.is_satisfied(context):
                violated.append(c)
        
        return len(violated) == 0, violated
    
    def check_end_condition(self, context: Dict[str, Any]) -> bool:
        """检查终止条件"""
        if self.end_rule is None:
            return False
        return self.end_rule.is_ended(context)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "target": self.target,
            "preconditions": [pc.to_dict() for pc in self.preconditions],
            "constraints": [c.to_dict() for c in self.constraints],
            "end_rule": self.end_rule.to_dict() if self.end_rule else None,
            "metadata": self.metadata
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TaskQuartet':
        """从字典创建"""
        quartet = TaskQuartet(
            target=data.get("target", ""),
            preconditions=[],
            constraints=[Constraint.from_dict(c) for c in data.get("constraints", [])]
        )
        quartet.metadata = data.get("metadata", {})
        return quartet
    
    def to_json(self) -> str:
        """序列化为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @staticmethod
    def from_json(json_str: str) -> 'TaskQuartet':
        """从JSON反序列化"""
        return TaskQuartet.from_dict(json.loads(json_str))


class Task:
    """
    任务
    - id: 唯一标识
    - quartet: 任务四元组
    - context: 执行上下文
    - status: 任务状态
    """
    def __init__(
        self,
        task_id: str,
        quartet: TaskQuartet,
        context: Optional[Dict[str, Any]] = None,
        parent_task_id: Optional[str] = None
    ):
        self.id = task_id
        self.quartet = quartet
        self.status = TaskStatus.PENDING
        self.context = context or {}
        self.output = None
        self.parent_task_id = parent_task_id
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
        self.metadata = {}
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate(self) -> tuple:
        """验证任务合法性"""
        is_valid, errors, warnings = self.quartet.validate()
        self.validation_errors = errors
        self.validation_warnings = warnings
        return is_valid, errors, warnings
    
    def is_legal(self) -> bool:
        """检查任务是否合法"""
        is_valid, _, _ = self.validate()
        return is_valid
    
    def mark_in_progress(self):
        """标记为进行中"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = time.time()
    
    def mark_completed(self, output_val: Any = None):
        """标记为完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = time.time()
        if output_val is not None:
            self.output = output_val
    
    def mark_failed(self, error_msg: str = ""):
        """标记为失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = time.time()
        if error_msg:
            self.metadata["error_message"] = error_msg
    
    def mark_blocked(self, reason: str = ""):
        """标记为阻塞"""
        self.status = TaskStatus.BLOCKED
        if reason:
            self.metadata["block_reason"] = reason
    
    def update_context(self, updates: Dict[str, Any]):
        """更新上下文"""
        self.context.update(updates)
    
    def increment_step(self):
        """增加步骤计数"""
        self.context["step_count"] = self.context.get("step_count", 0) + 1
    
    def get_execution_time(self) -> Optional[float]:
        """获取执行时间（秒）"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "quartet": self.quartet.to_dict(),
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "context": self.context,
            "output": self.output,
            "parent_task_id": self.parent_task_id,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
            "validation_errors": [e.to_dict() for e in self.validation_errors],
            "validation_warnings": [w.to_dict() for w in self.validation_warnings]
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Task':
        """从字典创建"""
        quartet = TaskQuartet.from_dict(data.get("quartet", {}))
        task = Task(
            task_id=data.get("id", ""),
            quartet=quartet,
            context=data.get("context", {}),
            parent_task_id=data.get("parent_task_id")
        )
        task.status = TaskStatus(data.get("status", "pending"))
        task.output = data.get("output")
        task.metadata = data.get("metadata", {})
        return task
    
    def to_json(self) -> str:
        """序列化为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @staticmethod
    def from_json(json_str: str) -> 'Task':
        """从JSON反序列化"""
        return Task.from_dict(json.loads(json_str))
    
    def __repr__(self) -> str:
        return f"Task(id='{self.id}', status={self.status.value}, target='{self.quartet.target[:30]}...')"


def create_simple_task(
    task_id: str,
    target: str,
    end_condition_func: Callable[[Dict[str, Any]], bool] = None,
    context: Optional[Dict[str, Any]] = None
) -> Task:
    """
    创建简单任务的工厂函数
    
    Args:
        task_id: 任务ID
        target: 目标描述
        end_condition_func: 终止条件函数
        context: 初始上下文
    
    Returns:
        Task: 创建的任务实例
    """
    end_rule = None
    if end_condition_func:
        end_rule = EndRule(end_condition_func)
    
    quartet = TaskQuartet(
        target=target,
        end_rule=end_rule
    )
    
    return Task(
        task_id=task_id,
        quartet=quartet,
        context=context
    )


def validate_task_legality(task: Task) -> tuple:
    """
    验证任务合法性的辅助函数
    
    Returns:
        tuple: (是否合法, 错误列表, 警告列表)
    """
    is_valid, errors, warnings = task.validate()
    
    # 额外的合法性检查
    if not task.quartet.target:
        errors.append(ValidationError("quartet.target", "Target cannot be empty"))
    
    return len([e for e in errors if e.severity == "error"]) == 0, errors, warnings


# ==================== 便捷的预置约束工厂函数 ====================

def max_steps_constraint(max_steps: int, description: str = "") -> Constraint:
    """创建最大步骤数约束"""
    return Constraint(
        constraint_type=ConstraintType.MAX_STEPS,
        value=max_steps,
        description=description or f"Maximum {max_steps} steps"
    )


def time_limit_constraint(seconds: float, description: str = "") -> Constraint:
    """创建时间限制约束"""
    return Constraint(
        constraint_type=ConstraintType.TIME_LIMIT,
        value=seconds,
        description=description or f"Time limit: {seconds}s"
    )


def no_network_constraint(description: str = "") -> Constraint:
    """创建禁止网络访问约束"""
    return Constraint(
        constraint_type=ConstraintType.NETWORK_RESTRICTED,
        value=True,
        description=description or "Network access restricted"
    )
