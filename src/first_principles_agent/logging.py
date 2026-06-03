"""
第77阶段：日志记录与追踪系统
提供结构化日志、多级别记录、上下文追踪等功能

核心原则：图难于其易，为大于其细。天下难事，必作于易；天下大事，必作于细。
"""

import time
import threading
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from enum import Enum
from collections import deque


class LogLevel(Enum):
    """日志级别"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@dataclass
class LogRecord:
    """日志记录"""
    timestamp: float
    level: LogLevel
    message: str
    logger_name: str
    trace_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)

    def format(self, include_timestamp: bool = True) -> str:
        """格式化日志记录"""
        parts = []
        if include_timestamp:
            formatted_time = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.localtime(self.timestamp)
            )
            parts.append(f"[{formatted_time}]")

        parts.append(f"[{self.level.name}]")
        parts.append(f"[{self.logger_name}]")

        if self.trace_id:
            parts.append(f"[trace={self.trace_id}]")

        if self.context:
            context_str = " ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"[{context_str}]")

        parts.append(self.message)

        return " ".join(parts)


@dataclass
class LogContext:
    """日志上下文"""
    trace_id: str
    context: Dict[str, Any] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def set(self, key: str, value: Any) -> "LogContext":
        """设置上下文字段"""
        with self._lock:
            self.context[key] = value
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文字段"""
        with self._lock:
            return self.context.get(key, default)

    def remove(self, key: str) -> "LogContext":
        """移除上下文字段"""
        with self._lock:
            self.context.pop(key, None)
        return self

    def update(self, **kwargs) -> "LogContext":
        """批量更新上下文"""
        with self._lock:
            self.context.update(kwargs)
        return self

    def clear(self) -> "LogContext":
        """清空上下文"""
        with self._lock:
            self.context.clear()
        return self


class LogHandler:
    """日志处理器基类"""

    def __init__(self, level: LogLevel = LogLevel.INFO):
        self.level = level
        self._lock = threading.Lock()

    def handle(self, record: LogRecord) -> None:
        """处理日志记录"""
        if record.level.value >= self.level.value:
            with self._lock:
                self._handle(record)

    def _handle(self, record: LogRecord) -> None:
        """实际处理逻辑（子类实现）"""
        pass

    def flush(self) -> None:
        """刷新缓冲区"""
        pass

    def close(self) -> None:
        """关闭处理器"""
        pass


class ConsoleHandler(LogHandler):
    """控制台日志处理器"""

    def __init__(self, level: LogLevel = LogLevel.INFO):
        super().__init__(level)

    def _handle(self, record: LogRecord) -> None:
        print(record.format())


class MemoryHandler(LogHandler):
    """内存日志处理器"""

    def __init__(
        self,
        level: LogLevel = LogLevel.INFO,
        max_records: int = 1000
    ):
        super().__init__(level)
        self.max_records = max_records
        self.records: deque = deque(maxlen=max_records)

    def _handle(self, record: LogRecord) -> None:
        self.records.append(record)

    def get_records(self, since: Optional[float] = None) -> List[LogRecord]:
        """获取记录"""
        if since is None:
            return list(self.records)
        return [r for r in self.records if r.timestamp >= since]

    def clear(self) -> None:
        """清空记录"""
        self.records.clear()


class CallbackHandler(LogHandler):
    """回调日志处理器"""

    def __init__(
        self,
        callback: Callable[[LogRecord], None],
        level: LogLevel = LogLevel.INFO
    ):
        super().__init__(level)
        self.callback = callback

    def _handle(self, record: LogRecord) -> None:
        self.callback(record)


class Logger:
    """日志记录器"""

    def __init__(
        self,
        name: str,
        handlers: Optional[List[LogHandler]] = None
    ):
        self.name = name
        self.handlers: List[LogHandler] = handlers or []
        self.level: LogLevel = LogLevel.DEBUG
        self._lock = threading.Lock()
        self._contexts: Dict[str, LogContext] = {}

    def add_handler(self, handler: LogHandler) -> "Logger":
        """添加处理器"""
        with self._lock:
            self.handlers.append(handler)
        return self

    def remove_handler(self, handler: LogHandler) -> "Logger":
        """移除处理器"""
        with self._lock:
            if handler in self.handlers:
                self.handlers.remove(handler)
        return self

    def set_level(self, level: LogLevel) -> "Logger":
        """设置日志级别"""
        with self._lock:
            self.level = level
        return self

    def create_context(self, trace_id: Optional[str] = None) -> LogContext:
        """创建追踪上下文"""
        trace_id = trace_id or str(uuid.uuid4())
        context = LogContext(trace_id=trace_id)
        thread_id = threading.get_ident()
        with self._lock:
            self._contexts[thread_id] = context
        return context

    def get_context(self) -> Optional[LogContext]:
        """获取当前线程的上下文"""
        thread_id = threading.get_ident()
        with self._lock:
            return self._contexts.get(thread_id)

    def clear_context(self) -> None:
        """清除当前线程的上下文"""
        thread_id = threading.get_ident()
        with self._lock:
            self._contexts.pop(thread_id, None)

    def _log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **extra
    ) -> None:
        """内部日志方法"""
        if level.value < self.level.value:
            return

        trace_id = None
        merged_context = context or {}

        # 获取当前上下文
        current_context = self.get_context()
        if current_context:
            trace_id = current_context.trace_id
            merged_context.update(current_context.context)

        record = LogRecord(
            timestamp=time.time(),
            level=level,
            message=message,
            logger_name=self.name,
            trace_id=trace_id,
            context=merged_context,
            extra=extra
        )

        with self._lock:
            for handler in self.handlers:
                handler.handle(record)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None, **extra) -> None:
        """调试日志"""
        self._log(LogLevel.DEBUG, message, context, **extra)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None, **extra) -> None:
        """信息日志"""
        self._log(LogLevel.INFO, message, context, **extra)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None, **extra) -> None:
        """警告日志"""
        self._log(LogLevel.WARNING, message, context, **extra)

    def error(self, message: str, context: Optional[Dict[str, Any]] = None, **extra) -> None:
        """错误日志"""
        self._log(LogLevel.ERROR, message, context, **extra)

    def critical(self, message: str, context: Optional[Dict[str, Any]] = None, **extra) -> None:
        """严重错误日志"""
        self._log(LogLevel.CRITICAL, message, context, **extra)

    def flush(self) -> None:
        """刷新所有处理器"""
        with self._lock:
            for handler in self.handlers:
                handler.flush()

    def close(self) -> None:
        """关闭所有处理器"""
        with self._lock:
            for handler in self.handlers:
                handler.close()


class LogManager:
    """日志管理器"""

    def __init__(self):
        self.loggers: Dict[str, Logger] = {}
        self._lock = threading.Lock()
        self.default_handlers: List[LogHandler] = []

    def get_logger(self, name: str) -> Logger:
        """获取或创建日志记录器"""
        with self._lock:
            if name not in self.loggers:
                logger = Logger(name)
                # 添加默认处理器
                for handler in self.default_handlers:
                    logger.add_handler(handler)
                self.loggers[name] = logger
            return self.loggers[name]

    def add_default_handler(self, handler: LogHandler) -> None:
        """添加默认处理器"""
        with self._lock:
            self.default_handlers.append(handler)
            # 应用到现有日志记录器
            for logger in self.loggers.values():
                logger.add_handler(handler)

    def set_root_level(self, level: LogLevel) -> None:
        """设置根日志级别"""
        with self._lock:
            for logger in self.loggers.values():
                logger.set_level(level)

    def flush_all(self) -> None:
        """刷新所有日志记录器"""
        with self._lock:
            for logger in self.loggers.values():
                logger.flush()

    def close_all(self) -> None:
        """关闭所有日志记录器"""
        with self._lock:
            for logger in self.loggers.values():
                logger.close()


# 全局日志管理器
_log_manager = LogManager()


def get_logger(name: str) -> Logger:
    """获取日志记录器"""
    return _log_manager.get_logger(name)


def add_default_handler(handler: LogHandler) -> None:
    """添加默认处理器"""
    _log_manager.add_default_handler(handler)


def set_root_level(level: LogLevel) -> None:
    """设置根日志级别"""
    _log_manager.set_root_level(level)


def create_context(trace_id: Optional[str] = None) -> LogContext:
    """创建追踪上下文（使用默认日志记录器）"""
    return get_logger("default").create_context(trace_id)


def get_context() -> Optional[LogContext]:
    """获取当前上下文（使用默认日志记录器）"""
    return get_logger("default").get_context()


def debug(message: str, context: Optional[Dict[str, Any]] = None, **extra) -> None:
    """调试日志（使用默认日志记录器）"""
    get_logger("default").debug(message, context, **extra)


def info(message: str, context: Optional[Dict[str, Any]] = None, **extra) -> None:
    """信息日志（使用默认日志记录器）"""
    get_logger("default").info(message, context, **extra)


def warning(message: str, context: Optional[Dict[str, Any]] = None, **extra) -> None:
    """警告日志（使用默认日志记录器）"""
    get_logger("default").warning(message, context, **extra)


def error(message: str, context: Optional[Dict[str, Any]] = None, **extra) -> None:
    """错误日志（使用默认日志记录器）"""
    get_logger("default").error(message, context, **extra)


def critical(message: str, context: Optional[Dict[str, Any]] = None, **extra) -> None:
    """严重错误日志（使用默认日志记录器）"""
    get_logger("default").critical(message, context, **extra)
