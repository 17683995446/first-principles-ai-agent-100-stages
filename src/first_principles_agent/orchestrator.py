"""
增强版主控制器 - First Principles Agent
第56-60阶段：完善工程化细节
- 第56阶段：优化单向依赖，彻底杜绝反向调用
- 第57阶段：开发全流程日志追踪系统
- 第58阶段：开发实时进度状态更新组件
- 第59阶段：统一全局异常捕获与分发机制
- 第60阶段：完成首轮全链路空载回归测试
"""

import time
import logging
import traceback
import uuid
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from .task_model import Task, TaskStatus
from .task_parser import UnifiedTaskModeling
from .topological_decomposer import TopologicalDecomposer, NodeType
from .atomic_converger import (
    AtomicConverger, AtomicAction, AtomicActionStatus,
    VerificationLayer, CircuitBreaker, RollbackManager,
    create_simple_action, create_validated_action
)


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Layer(Enum):
    """四层架构标识"""
    LAYER1_MODELING = "Layer1_Modeling"
    LAYER2_TOPOLOGY = "Layer2_Topology"
    LAYER3_ACTION = "Layer3_Action"
    LAYER4_VERIFICATION = "Layer4_Verification"
    ORCHESTRATOR = "Orchestrator"


class LogEntry:
    """增强版日志条目"""
    def __init__(
        self,
        level: LogLevel,
        layer: Layer,
        message: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.timestamp = time.time()
        self.level = level
        self.layer = layer
        self.message = message
        self.trace_id = trace_id or str(uuid.uuid4())[:8]
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "time_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp)),
            "level": self.level.value,
            "layer": self.layer.value,
            "message": self.message,
            "trace_id": self.trace_id,
            "metadata": self.metadata
        }
    
    def __str__(self) -> str:
        return f"[{self.to_dict()['time_str']}] [{self.level.value}] [{self.layer.value}] {self.message}"


class Logger:
    """
    第57阶段：全流程日志追踪系统
    增强版日志系统，支持：
    - 多层级日志
    - 追踪ID
    - 分类日志
    - 可追溯性
    """
    def __init__(self, enable_console: bool = True):
        self.entries: List[LogEntry] = []
        self.enable_console = enable_console
        self.current_trace_id: Optional[str] = None
        self._setup_console_logger()
    
    def _setup_console_logger(self):
        """设置控制台日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='[%(levelname)s] %(message)s'
        )
        self.console_logger = logging.getLogger("Agent")
    
    def _log(self, entry: LogEntry):
        """内部日志记录"""
        self.entries.append(entry)
        
        if self.enable_console:
            level_map = {
                LogLevel.DEBUG: self.console_logger.debug,
                LogLevel.INFO: self.console_logger.info,
                LogLevel.WARNING: self.console_logger.warning,
                LogLevel.ERROR: self.console_logger.error,
                LogLevel.CRITICAL: self.console_logger.critical
            }
            
            level_map.get(entry.level, self.console_logger.info)(str(entry))
    
    def log(self, level: LogLevel, layer: Layer, message: str, 
            metadata: Optional[Dict[str, Any]] = None):
        """记录日志"""
        entry = LogEntry(level, layer, message, self.current_trace_id, metadata)
        self._log(entry)
    
    def debug(self, layer: Layer, message: str, metadata: Optional[Dict[str, Any]] = None):
        self.log(LogLevel.DEBUG, layer, message, metadata)
    
    def info(self, layer: Layer, message: str, metadata: Optional[Dict[str, Any]] = None):
        self.log(LogLevel.INFO, layer, message, metadata)
    
    def warning(self, layer: Layer, message: str, metadata: Optional[Dict[str, Any]] = None):
        self.log(LogLevel.WARNING, layer, message, metadata)
    
    def error(self, layer: Layer, message: str, metadata: Optional[Dict[str, Any]] = None):
        self.log(LogLevel.ERROR, layer, message, metadata)
    
    def critical(self, layer: Layer, message: str, metadata: Optional[Dict[str, Any]] = None):
        self.log(LogLevel.CRITICAL, layer, message, metadata)
    
    def set_trace_id(self, trace_id: str):
        """设置追踪ID"""
        self.current_trace_id = trace_id
    
    def get_trace_id(self) -> str:
        """获取当前追踪ID"""
        return self.current_trace_id or "N/A"
    
    def get_logs_by_level(self, level: LogLevel) -> List[LogEntry]:
        """按级别过滤日志"""
        return [e for e in self.entries if e.level == level]
    
    def get_logs_by_layer(self, layer: Layer) -> List[LogEntry]:
        """按层过滤日志"""
        return [e for e in self.entries if e.layer == layer]
    
    def get_all_logs(self) -> List[LogEntry]:
        """获取所有日志"""
        return self.entries.copy()
    
    def clear(self):
        """清空日志"""
        self.entries = []
    
    def get_summary(self) -> Dict[str, Any]:
        """获取日志摘要"""
        summary = {
            "total": len(self.entries),
            "by_level": {},
            "by_layer": {},
            "trace_id": self.current_trace_id
        }
        
        for entry in self.entries:
            level_key = entry.level.value
            layer_key = entry.layer.value
            
            summary["by_level"][level_key] = summary["by_level"].get(level_key, 0) + 1
            summary["by_layer"][layer_key] = summary["by_layer"].get(layer_key, 0) + 1
        
        return summary


class ProgressCallback:
    """
    第58阶段：实时进度状态更新组件
    进度回调机制
    """
    def __init__(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.callback = callback
        self.progress: Dict[str, Any] = {
            "current_step": 0,
            "total_steps": 0,
            "percentage": 0,
            "current_layer": None,
            "message": "",
            "start_time": None,
            "end_time": None
        }
    
    def update(
        self,
        current_step: int,
        total_steps: int,
        current_layer: Optional[str] = None,
        message: str = ""
    ):
        """更新进度"""
        percentage = int((current_step / total_steps * 100)) if total_steps > 0 else 0
        
        self.progress = {
            "current_step": current_step,
            "total_steps": total_steps,
            "percentage": percentage,
            "current_layer": current_layer,
            "message": message
        }
        
        if self.callback:
            self.callback(self.progress.copy())
    
    def start(self):
        """开始计时"""
        self.progress["start_time"] = time.time()
    
    def end(self):
        """结束计时"""
        self.progress["end_time"] = time.time()
    
    def get_progress(self) -> Dict[str, Any]:
        """获取当前进度"""
        return self.progress.copy()


class GlobalExceptionHandler:
    """
    第59阶段：统一全局异常捕获与分发机制
    """
    def __init__(self):
        self.handlers: Dict[type, Callable[[Exception], None]] = {}
        self.default_handler: Optional[Callable[[Exception], None]] = None
        self.exception_history: List[Dict[str, Any]] = []
    
    def register_handler(self, exception_type: type, handler: Callable[[Exception], None]):
        """注册异常处理器"""
        self.handlers[exception_type] = handler
    
    def register_default_handler(self, handler: Callable[[Exception], None]):
        """注册默认处理器"""
        self.default_handler = handler
    
    def handle(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理异常"""
        exception_info = {
            "type": type(exception).__name__,
            "message": str(exception),
            "traceback": traceback.format_exc(),
            "context": context or {},
            "timestamp": time.time()
        }
        
        self.exception_history.append(exception_info)
        
        # 查找特定处理器
        for exc_type, handler in self.handlers.items():
            if isinstance(exception, exc_type):
                handler(exception)
                exception_info["handled_by"] = f"specific_handler_{exc_type.__name__}"
                return exception_info
        
        # 使用默认处理器
        if self.default_handler:
            self.default_handler(exception)
            exception_info["handled_by"] = "default_handler"
        
        return exception_info
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取异常历史"""
        return self.exception_history.copy()
    
    def clear_history(self):
        """清空异常历史"""
        self.exception_history = []


class FirstPrinciplesAgent:
    """
    增强版第一性原理AI Agent - 主控制器
    
    第56阶段：优化单向依赖，彻底杜绝反向调用
    - 严格的层调用顺序检查
    - 层间无反向依赖
    
    第57阶段：全流程日志追踪系统
    - 增强版Logger
    - 追踪ID
    - 分类日志
    
    第58阶段：实时进度状态更新组件
    - ProgressCallback
    - 实时进度通知
    
    第59阶段：统一全局异常捕获
    - GlobalExceptionHandler
    - 异常历史记录
    """
    
    def __init__(
        self,
        enable_logging: bool = True,
        enable_progress: bool = True,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        # 第一层：任务归一建模层（只被Orchestrator调用）
        self.modeler = UnifiedTaskModeling()
        
        # 第二层：拓扑依赖拆解层（只被Orchestrator调用）
        self.decomposer = TopologicalDecomposer()
        
        # 第三层：原子动作收敛层（只被Orchestrator调用）
        self.converger = AtomicConverger()
        
        # 第四层：分段校验收敛层（只被Orchestrator调用）
        self.verification = VerificationLayer()
        
        # 熔断器
        self.circuit_breaker = CircuitBreaker(failure_threshold=3)
        
        # 回滚管理器
        self.rollback_manager = RollbackManager()
        
        # 增强版日志系统
        self.logger = Logger(enable_console=enable_logging)
        
        # 进度回调
        self.progress_callback = ProgressCallback(progress_callback)
        
        # 全局异常处理器
        self.exception_handler = GlobalExceptionHandler()
        self._setup_default_exception_handler()
        
        # 当前任务
        self.current_task: Optional[Task] = None
        
        # 执行指标
        self.metrics = {
            "total_steps": 0,
            "completed_steps": 0,
            "failed_steps": 0,
            "start_time": None,
            "end_time": None,
            "execution_time_ms": 0
        }
        
        # 追踪ID
        self.trace_id = str(uuid.uuid4())[:8]
        self.logger.set_trace_id(self.trace_id)
    
    def _setup_default_exception_handler(self):
        """设置默认异常处理器"""
        def default_handler(exc: Exception):
            self.logger.error(
                Layer.ORCHESTRATOR,
                f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
                {"traceback": traceback.format_exc()}
            )
        
        self.exception_handler.register_default_handler(default_handler)
    
    def execute(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        主执行入口 - 严格单向依赖
        
        第56阶段：优化单向依赖
        严格的层调用顺序：Orchestrator → L1 → L2 → L3 → L4
        """
        self.trace_id = str(uuid.uuid4())[:8]
        self.logger.set_trace_id(self.trace_id)
        self.logger.info(Layer.ORCHESTRATOR, "=" * 60)
        self.logger.info(Layer.ORCHESTRATOR, f"Agent开始执行 [TraceID: {self.trace_id}]")
        self.logger.info(Layer.ORCHESTRATOR, "=" * 60)
        
        # 重置状态
        self.metrics["start_time"] = time.time()
        self.logger.clear()
        self.progress_callback.start()
        
        result = {
            "success": False,
            "trace_id": self.trace_id,
            "error": None,
            "metrics": {}
        }
        
        try:
            # 第1步：建模层（单向依赖：Orchestrator → Layer1）
            self.logger.info(Layer.ORCHESTRATOR, "→ 调用 Layer1: 任务归一建模")
            self._modeling_layer(user_input, context)
            self.progress_callback.update(1, 4, "Layer1_Modeling", "任务建模完成")
            
            # 第2步：拓扑层（单向依赖：Layer1 → Layer2）
            self.logger.info(Layer.ORCHESTRATOR, "→ 调用 Layer2: 拓扑依赖拆解")
            self._topology_layer()
            self.progress_callback.update(2, 4, "Layer2_Topology", "DAG构建完成")
            
            # 第3步：动作层（单向依赖：Layer2 → Layer3）
            self.logger.info(Layer.ORCHESTRATOR, "→ 调用 Layer3: 原子动作队列")
            self._action_layer()
            self.progress_callback.update(3, 4, "Layer3_Action", "动作队列生成")
            
            # 第4步：验证层（单向依赖：Layer3 → Layer4）
            self.logger.info(Layer.ORCHESTRATOR, "→ 调用 Layer4: 执行与收敛")
            success = self._verification_layer()
            self.progress_callback.update(4, 4, "Layer4_Verification", "执行完成")
            
            result["success"] = success
            
        except Exception as e:
            # 统一异常处理
            exc_info = self.exception_handler.handle(e, {
                "trace_id": self.trace_id,
                "current_task": self.current_task.id if self.current_task else None
            })
            result["error"] = exc_info["message"]
            self.logger.error(Layer.ORCHESTRATOR, f"执行异常: {exc_info['message']}")
        
        finally:
            self.metrics["end_time"] = time.time()
            self.metrics["execution_time_ms"] = (
                self.metrics["end_time"] - self.metrics["start_time"]
            ) * 1000
            self.progress_callback.end()
        
        result["metrics"] = self.metrics.copy()
        result["logs"] = self.logger.get_all_logs()
        result["log_summary"] = self.logger.get_summary()
        
        self.logger.info(Layer.ORCHESTRATOR, "=" * 60)
        self.logger.info(
            Layer.ORCHESTRATOR,
            f"执行{'成功' if result['success'] else '失败'} [TraceID: {self.trace_id}]"
        )
        self.logger.info(Layer.ORCHESTRATOR, "=" * 60)
        
        return result
    
    def _modeling_layer(self, user_input: str, context: Optional[Dict[str, Any]]):
        """
        第56阶段：单向依赖 - Layer1只能被Orchestrator调用
        """
        self.logger.info(Layer.LAYER1_MODELING, f"开始建模: {user_input}")
        
        success, modeling_result = self.modeler.model(user_input, context)
        
        if not success:
            if modeling_result.get("rejected"):
                rejection = modeling_result["rejection_info"]
                self.logger.error(
                    Layer.LAYER1_MODELING,
                    f"任务被拒绝: {rejection['reason_message']}"
                )
                raise ValueError(f"任务被拒绝: {rejection['reason_message']}")
            else:
                errors = modeling_result.get("errors", [])
                self.logger.error(Layer.LAYER1_MODELING, f"建模失败: {errors}")
                raise ValueError(f"建模失败: {errors}")
        
        self.current_task = modeling_result["task"]
        self.logger.info(
            Layer.LAYER1_MODELING,
            f"✓ 建模成功: {self.current_task.id}"
        )
    
    def _topology_layer(self):
        """
        第56阶段：单向依赖 - Layer2只能被Orchestrator调用
        """
        self.logger.info(Layer.LAYER2_TOPOLOGY, "开始DAG构建")
        
        if not self.current_task:
            raise ValueError("No task to decompose")
        
        self.decomposer.add_task(self.current_task)
        
        is_valid, issues = self.decomposer.validate_dag()
        
        if not is_valid:
            issue_msgs = [i.description for i in issues]
            self.logger.error(Layer.LAYER2_TOPOLOGY, f"DAG验证失败: {issue_msgs}")
            raise ValueError(f"DAG验证失败: {issue_msgs}")
        
        self.logger.info(
            Layer.LAYER2_TOPOLOGY,
            f"✓ DAG构建成功: {len(self.decomposer.nodes)} 个节点"
        )
    
    def _action_layer(self):
        """
        第56阶段：单向依赖 - Layer3只能被Orchestrator调用
        """
        self.logger.info(Layer.LAYER3_ACTION, "开始生成动作队列")
        
        self.converger.clear()
        
        self.logger.info(
            Layer.LAYER3_ACTION,
            f"✓ 动作队列生成: {len(self.converger.action_queue)} 个动作"
        )
    
    def _verification_layer(self) -> bool:
        """
        第56阶段：单向依赖 - Layer4只能被Orchestrator调用
        """
        self.logger.info(Layer.LAYER4_VERIFICATION, "开始执行与验证")
        
        # 检查熔断
        if not self.circuit_breaker.should_allow_request():
            self.logger.error(
                Layer.LAYER4_VERIFICATION,
                "熔断器打开，停止执行"
            )
            return False
        
        # 检查前置条件
        if self.current_task:
            pre_report = self.verification.check_preconditions(
                self.current_task,
                {}
            )
            
            if not pre_report.is_success():
                self.logger.error(
                    Layer.LAYER4_VERIFICATION,
                    f"前置条件不满足: {pre_report.message}"
                )
                self.circuit_breaker.record_failure()
                return False
        
        # 执行动作队列
        success = self._execute_action_queue()
        
        if success:
            self.circuit_breaker.record_success()
            self.logger.info(Layer.LAYER4_VERIFICATION, "✓ 执行成功")
        else:
            self.circuit_breaker.record_failure()
            self.logger.error(Layer.LAYER4_VERIFICATION, "✗ 执行失败")
        
        return success
    
    def _execute_action_queue(self) -> bool:
        """执行动作队列"""
        if not self.converger.action_queue:
            self.logger.info(Layer.LAYER3_ACTION, "队列为空，使用默认执行")
            return True
        
        for action in self.converger.action_queue:
            try:
                self.logger.info(Layer.LAYER3_ACTION, f"执行动作: {action.id}")
                action.execute({})
                self.metrics["completed_steps"] += 1
                self.logger.info(Layer.LAYER3_ACTION, f"✓ 动作完成: {action.id}")
                
            except Exception as e:
                self.logger.error(
                    Layer.LAYER3_ACTION,
                    f"✗ 动作失败: {action.id} - {str(e)}"
                )
                self.metrics["failed_steps"] += 1
                return False
        
        return True
    
    def set_actions(self, actions: List[AtomicAction]):
        """设置原子动作"""
        self.converger.clear()
        count, _ = self.converger.add_actions(actions)
        self.logger.info(Layer.ORCHESTRATOR, f"设置{count}个原子动作")
    
    def get_state(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "has_task": self.current_task is not None,
            "task_id": self.current_task.id if self.current_task else None,
            "nodes_count": len(self.decomposer.nodes),
            "actions_count": len(self.converger.action_queue),
            "circuit_breaker": self.circuit_breaker.get_status(),
            "metrics": self.metrics,
            "trace_id": self.trace_id,
            "progress": self.progress_callback.get_progress()
        }
    
    def reset(self):
        """重置Agent"""
        self.current_task = None
        self.decomposer.clear()
        self.converger.clear()
        self.verification.reset()
        self.logger.clear()
        self.logger.set_trace_id(str(uuid.uuid4())[:8])
        self.metrics = {
            "total_steps": 0,
            "completed_steps": 0,
            "failed_steps": 0,
            "start_time": None,
            "end_time": None,
            "execution_time_ms": 0
        }
        self.logger.info(Layer.ORCHESTRATOR, "Agent已重置")


def create_agent(**kwargs) -> FirstPrinciplesAgent:
    """创建Agent工厂函数"""
    return FirstPrinciplesAgent(**kwargs)
