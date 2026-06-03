"""
原子动作收敛层（第3层）+ 分段校验收敛层（第4层）
第41-50阶段实现
"""

import time
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
from .task_model import Task, TaskStatus


class AtomicActionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ActionGranularity(Enum):
    FINE = "fine"       # 细粒度
    MEDIUM = "medium"   # 中等粒度
    COARSE = "coarse"  # 粗粒度


class ActionInputSchema:
    """第41阶段：输入模式验证"""
    def __init__(self, required_keys: Optional[List[str]] = None, 
                 optional_keys: Optional[List[str]] = None):
        self.required_keys = required_keys or []
        self.optional_keys = optional_keys or []
    
    def validate(self, context: Dict[str, Any]) -> tuple[bool, List[str]]:
        missing = [k for k in self.required_keys if k not in context]
        return len(missing) == 0, missing
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "required_keys": self.required_keys,
            "optional_keys": self.optional_keys
        }


class ActionOutputSchema:
    """第41阶段：输出模式验证"""
    def __init__(self, expected_keys: Optional[List[str]] = None):
        self.expected_keys = expected_keys or []
    
    def validate(self, output: Any) -> tuple[bool, List[str]]:
        if not isinstance(output, dict):
            return False, ["Output is not a dictionary"]
        
        missing = [k for k in self.expected_keys if k not in output]
        return len(missing) == 0, missing
    
    def to_dict(self) -> Dict[str, Any]:
        return {"expected_keys": self.expected_keys}


class AtomicAction:
    """
    第41阶段：原子动作标准存储结构
    遵循三大公理：单一职责、不可再分、可直接执行
    """
    def __init__(
        self,
        action_id: str,
        description: str,
        execute_func: Callable[[Dict[str, Any]], Any],
        input_schema: Optional[ActionInputSchema] = None,
        output_schema: Optional[ActionOutputSchema] = None,
        max_retries: int = 0,
        timeout_seconds: Optional[float] = None,
        granularity: Optional[ActionGranularity] = None
    ):
        self.id = action_id
        self.description = description
        self.execute_func = execute_func
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.granularity = granularity or ActionGranularity.MEDIUM
        self.status = AtomicActionStatus.PENDING
        self.output = None
        self.error = None
        self.retry_count = 0
        self.execution_time_ms = 0
        self.context = {}
    
    def can_retry(self) -> bool:
        """第48阶段：重试判断"""
        return self.retry_count < self.max_retries
    
    def validate_input(self, context: Dict[str, Any]) -> tuple[bool, List[str]]:
        """第43阶段：输入验证"""
        if not self.input_schema:
            return True, []
        return self.input_schema.validate(context)
    
    def validate_output(self, output: Any) -> tuple[bool, List[str]]:
        """第43阶段：输出验证"""
        if not self.output_schema:
            return True, []
        return self.output_schema.validate(output)
    
    def execute(self, context: Dict[str, Any]) -> Any:
        """执行原子动作"""
        start_time = time.time()
        self.status = AtomicActionStatus.RUNNING
        self.context = context.copy()
        
        try:
            # 输入验证
            valid, missing = self.validate_input(context)
            if not valid:
                raise ValueError(f"Missing input keys: {missing}")
            
            # 执行
            self.output = self.execute_func(context)
            
            # 输出验证
            valid, missing = self.validate_output(self.output)
            if not valid:
                raise ValueError(f"Missing output keys: {missing}")
            
            self.status = AtomicActionStatus.COMPLETED
            self.execution_time_ms = (time.time() - start_time) * 1000
            return self.output
            
        except Exception as e:
            self.status = AtomicActionStatus.FAILED
            self.error = str(e)
            self.execution_time_ms = (time.time() - start_time) * 1000
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "granularity": self.granularity.value,
            "status": self.status.value,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error
        }


class ActionValidator:
    """
    第43阶段：三大原子判定条件自动校验
    """
    def __init__(self):
        self.validation_results = []
    
    def is_atomic(self, action: AtomicAction) -> tuple[bool, List[str]]:
        """
        判断动作是否满足原子性三条标准
        1. 单一职责：只有一个主要目标
        2. 不可再分：不能有意义地拆分
        3. 可直接执行：不需要进一步规划
        """
        issues = []
        
        # 检查1：描述是否包含连词（表示多个动作）
        action_words = ["并", "且", "然后", "再", "和", "与", "同时", "and", "AND", ",", "，"]
        multi_action_indicators = sum(1 for word in action_words if word in action.description)
        if multi_action_indicators >= 1:
            issues.append(f"可能违反单一职责：包含{multi_action_indicators}个连词/分隔符")
        
        # 检查2：是否包含"规划"、"分析"等模糊词
        vague_words = ["处理", "完成", "执行"]
        if any(word in action.description for word in vague_words):
            if not action.input_schema and not action.output_schema:
                issues.append("缺少输入输出约束，可能粒度过粗")
        
        return len(issues) == 0, issues
    
    def validate_batch(self, actions: List[AtomicAction]) -> Dict[str, Any]:
        """批量验证"""
        results = []
        atomic_count = 0
        
        for action in actions:
            is_atomic, issues = self.is_atomic(action)
            results.append({
                "action_id": action.id,
                "is_atomic": is_atomic,
                "issues": issues
            })
            if is_atomic:
                atomic_count += 1
        
        return {
            "total": len(actions),
            "atomic_count": atomic_count,
            "non_atomic_count": len(actions) - atomic_count,
            "results": results
        }


class ActionSplitter:
    """
    第42阶段：复合动作自动拆分工具
    """
    def __init__(self):
        self.split_patterns = [
            (r"[和与且]", self._split_by_conjunction),
            (r"[,，]", self._split_by_comma),
            (r"[然后再]", self._split_by_sequence)
        ]
    
    def split_if_needed(self, action: AtomicAction) -> List[AtomicAction]:
        """
        检查并拆分复合动作
        """
        # 如果已经是原子动作，直接返回
        is_atomic, _ = ActionValidator().is_atomic(action)
        if is_atomic:
            return [action]
        
        # 尝试拆分
        parts = self._split_description(action.description)
        
        if len(parts) <= 1:
            return [action]
        
        # 生成子动作
        subtasks = []
        for i, part in enumerate(parts):
            sub_action = AtomicAction(
                action_id=f"{action.id}_sub_{i+1}",
                description=part.strip(),
                execute_func=action.execute_func,
                granularity=ActionGranularity.FINE
            )
            subtasks.append(sub_action)
        
        return subtasks
    
    def _split_description(self, description: str) -> List[str]:
        """按模式拆分描述"""
        import re
        for pattern, _ in self.split_patterns:
            if re.search(pattern, description):
                parts = re.split(pattern, description)
                if len(parts) > 1:
                    return [p.strip() for p in parts if p.strip()]
        return [description]
    
    def _split_by_conjunction(self, text: str) -> List[str]:
        return text.replace("和", "|").replace("与", "|").replace("且", "|").split("|")
    
    def _split_by_comma(self, text: str) -> List[str]:
        return [s.strip() for s in text.replace("，", ",").split(",") if s.strip()]
    
    def _split_by_sequence(self, text: str) -> List[str]:
        return text.replace("然后", "|").replace("再", "|").split("|")


class AtomicConverger:
    """
    第44阶段：原子动作收敛层核心
    子任务下沉转为原子队列
    """
    def __init__(self):
        self.action_queue: List[AtomicAction] = []
        self.completed_actions: List[AtomicAction] = []
        self.failed_actions: List[AtomicAction] = []
        self.validator = ActionValidator()
        self.splitter = ActionSplitter()
    
    def add_action(self, action: AtomicAction) -> bool:
        """添加原子动作"""
        self.action_queue.append(action)
        return True
    
    def add_actions(self, actions: List[AtomicAction]) -> tuple[int, List[str]]:
        """批量添加动作"""
        count = 0
        errors = []
        for action in actions:
            try:
                if self.add_action(action):
                    count += 1
            except Exception as e:
                errors.append(f"{action.id}: {str(e)}")
        return count, errors
    
    def decompose_task(self, task: Task) -> List[AtomicAction]:
        """
        第44阶段：子任务下沉转为原子队列
        """
        # 这里应该根据task生成对应的动作队列
        # 目前直接返回队列中的动作
        return self.action_queue.copy()
    
    def purify_queue(self) -> tuple[List[AtomicAction], List[str]]:
        """
        第45阶段：队列净化
        识别并整改非原子动作
        """
        purified = []
        warnings = []
        
        for action in self.action_queue:
            is_atomic, issues = self.validator.is_atomic(action)
            
            if is_atomic:
                purified.append(action)
            else:
                # 尝试拆分
                sub_actions = self.splitter.split_if_needed(action)
                if len(sub_actions) > 1:
                    purified.extend(sub_actions)
                    warnings.append(f"{action.id} 被拆分为 {len(sub_actions)} 个原子动作")
                else:
                    purified.append(action)
                    warnings.append(f"{action.id} 仍为非原子动作: {', '.join(issues)}")
        
        self.action_queue = purified
        return purified, warnings
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.action_queue)
        completed = len([a for a in self.action_queue if a.status == AtomicActionStatus.COMPLETED])
        failed = len([a for a in self.action_queue if a.status == AtomicActionStatus.FAILED])
        pending = len([a for a in self.action_queue if a.status == AtomicActionStatus.PENDING])
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "completion_rate": completed / total if total > 0 else 0
        }
    
    def clear(self):
        """清空队列"""
        self.action_queue = []
        self.completed_actions = []
        self.failed_actions = []


# ==================== 第46-50阶段：分段校验收敛层 ====================

class VerificationType(Enum):
    PRECONDITION = "precondition"
    POSTCONDITION = "postcondition"
    CONSTRAINT = "constraint"
    END_CONDITION = "end_condition"


class VerificationResult(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class VerificationReport:
    """第47阶段：执行结果合规性比对校验"""
    def __init__(
        self,
        verification_type: VerificationType,
        result: VerificationResult,
        message: str = "",
        details: Optional[Dict[str, Any]] = None
    ):
        self.type = verification_type
        self.result = result
        self.message = message
        self.details = details or {}
        self.timestamp = time.time()
    
    def is_success(self) -> bool:
        return self.result == VerificationResult.PASSED
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "result": self.result.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }


class CircuitBreaker:
    """
    第48阶段：熔断触发判定机制、阈值体系
    """
    def __init__(
        self,
        failure_threshold: int = 3,
        timeout_seconds: float = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        self.failure_count = 0
        self.success_count = 0
        self.state = "closed"  # closed, open, half_open
        self.last_failure_time = None
    
    def record_success(self):
        """记录成功"""
        self.success_count += 1
        self.failure_count = 0
        
        if self.state == "half_open" and self.success_count >= self.success_threshold:
            self.state = "closed"
            self.success_count = 0
    
    def record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.success_count = 0
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
    
    def should_allow_request(self) -> bool:
        """是否允许请求"""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = "half_open"
                return True
            return False
        
        return True  # half_open
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count
        }


class RollbackManager:
    """
    第49阶段：任务回滚、局部重规划调用接口
    """
    def __init__(self):
        self.execution_history: List[Dict[str, Any]] = []
        self.checkpoints: Dict[str, Any] = {}
    
    def create_checkpoint(self, name: str, state: Dict[str, Any]):
        """创建检查点"""
        self.checkpoints[name] = {
            "state": state.copy(),
            "timestamp": time.time()
        }
    
    def rollback_to_checkpoint(self, name: str) -> Optional[Dict[str, Any]]:
        """回滚到检查点"""
        if name in self.checkpoints:
            checkpoint = self.checkpoints[name]
            self.execution_history.append({
                "action": "rollback",
                "checkpoint": name,
                "timestamp": time.time()
            })
            return checkpoint["state"]
        return None
    
    def record_action(self, action_id: str, output: Any):
        """记录动作"""
        self.execution_history.append({
            "action": action_id,
            "output": output,
            "timestamp": time.time()
        })
    
    def get_last_successful_state(self) -> Optional[Dict[str, Any]]:
        """获取最后一次成功状态"""
        for record in reversed(self.execution_history):
            if record.get("success"):
                return record.get("state")
        return None


class VerificationLayer:
    """
    第46-50阶段：分段校验收敛层核心
    """
    def __init__(self):
        self.reports: List[VerificationReport] = []
        self.circuit_breaker = CircuitBreaker()
        self.rollback_manager = RollbackManager()
    
    def check_preconditions(self, task: Task, context: Dict[str, Any]) -> VerificationReport:
        """第46阶段：预校验"""
        # 检查前置条件
        satisfied = task.quartet.check_preconditions(context)
        
        if satisfied:
            return VerificationReport(
                VerificationType.PRECONDITION,
                VerificationResult.PASSED,
                "All preconditions satisfied"
            )
        else:
            return VerificationReport(
                VerificationType.PRECONDITION,
                VerificationResult.FAILED,
                "Some preconditions not satisfied"
            )
    
    def check_postconditions(self, action: AtomicAction, context: Dict[str, Any]) -> VerificationReport:
        """第47阶段：执行结果校验"""
        if action.status == AtomicActionStatus.COMPLETED:
            return VerificationReport(
                VerificationType.POSTCONDITION,
                VerificationResult.PASSED,
                "Action completed successfully"
            )
        else:
            return VerificationReport(
                VerificationType.POSTCONDITION,
                VerificationResult.FAILED,
                f"Action failed: {action.error}"
            )
    
    def check_constraints(self, task: Task, context: Dict[str, Any]) -> VerificationReport:
        """约束检查"""
        satisfied, violated = task.quartet.check_constraints(context)
        
        if satisfied:
            return VerificationReport(
                VerificationType.CONSTRAINT,
                VerificationResult.PASSED,
                "All constraints satisfied"
            )
        else:
            return VerificationReport(
                VerificationType.CONSTRAINT,
                VerificationResult.FAILED,
                f"Constraints violated"
            )
    
    def check_end_condition(self, task: Task, context: Dict[str, Any]) -> VerificationReport:
        """终止条件检查"""
        ended = task.quartet.check_end_condition(context)
        
        if ended:
            return VerificationReport(
                VerificationType.END_CONDITION,
                VerificationResult.PASSED,
                "End condition met - task should terminate"
            )
        else:
            return VerificationReport(
                VerificationType.END_CONDITION,
                VerificationResult.WARNING,
                "End condition not met - continue execution"
            )
    
    def get_reports(self) -> List[VerificationReport]:
        return self.reports.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        passed = len([r for r in self.reports if r.result == VerificationResult.PASSED])
        failed = len([r for r in self.reports if r.result == VerificationResult.FAILED])
        return {
            "total": len(self.reports),
            "passed": passed,
            "failed": failed
        }
    
    def reset(self):
        self.reports = []


# ==================== 工厂函数 ====================

def create_simple_action(
    action_id: str,
    description: str,
    execute_func: Callable[[Dict[str, Any]], Any]
) -> AtomicAction:
    """创建简单原子动作"""
    return AtomicAction(
        action_id=action_id,
        description=description,
        execute_func=execute_func
    )


def create_validated_action(
    action_id: str,
    description: str,
    execute_func: Callable[[Dict[str, Any]], Any],
    required_inputs: Optional[List[str]] = None,
    expected_outputs: Optional[List[str]] = None
) -> AtomicAction:
    """创建带验证的原子动作"""
    return AtomicAction(
        action_id=action_id,
        description=description,
        execute_func=execute_func,
        input_schema=ActionInputSchema(required_keys=required_inputs) if required_inputs else None,
        output_schema=ActionOutputSchema(expected_keys=expected_outputs) if expected_outputs else None
    )


def create_default_verification_layer() -> VerificationLayer:
    """创建默认验证层"""
    return VerificationLayer()
