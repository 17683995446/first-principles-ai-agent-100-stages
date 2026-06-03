"""
第76阶段：系统监控与指标收集
提供完整的指标收集、聚合、报告和告警能力

核心原则：图难于其易，为大于其细。天下难事，必作于易；天下大事，必作于细。
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from collections import defaultdict, deque
import statistics


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"        # 计数器
    GAUGE = "gauge"            # 仪表（当前值）
    HISTOGRAM = "histogram"    # 直方图
    TIMER = "timer"            # 计时器


@dataclass
class MetricValue:
    """指标值"""
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Metric:
    """指标"""
    name: str
    type: MetricType
    description: str
    values: List[MetricValue] = field(default_factory=list)
    max_history: int = 1000

    def record(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """记录指标值"""
        mv = MetricValue(
            value=value,
            timestamp=time.time(),
            labels=labels or {}
        )
        self.values.append(mv)
        if len(self.values) > self.max_history:
            self.values = self.values[-self.max_history:]

    def get_snapshot(self, since: Optional[float] = None) -> List[MetricValue]:
        """获取指标快照"""
        if since is None:
            return list(self.values)
        return [mv for mv in self.values if mv.timestamp >= since]

    def get_statistics(self, since: Optional[float] = None) -> Dict[str, float]:
        """获取指标统计信息"""
        values = self.get_snapshot(since)
        if not values:
            return {}

        raw_values = [v.value for v in values]
        return {
            "count": len(raw_values),
            "min": min(raw_values),
            "max": max(raw_values),
            "mean": statistics.mean(raw_values),
            "median": statistics.median(raw_values) if len(raw_values) > 1 else raw_values[0],
            "p50": statistics.quantiles(raw_values, n=100)[49] if len(raw_values) >= 2 else raw_values[0],
            "p90": statistics.quantiles(raw_values, n=100)[89] if len(raw_values) >= 2 else raw_values[0],
            "p95": statistics.quantiles(raw_values, n=100)[94] if len(raw_values) >= 2 else raw_values[0],
            "p99": statistics.quantiles(raw_values, n=100)[98] if len(raw_values) >= 2 else raw_values[0]
        }


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric_name: str
    condition: Callable[[Metric], bool]
    message: str
    level: str = "warning"  # warning, error, critical
    cooldown_seconds: float = 60.0
    last_triggered: Optional[float] = None


class MetricsRegistry:
    """指标注册表"""

    def __init__(self, default_max_history: int = 1000):
        self.metrics: Dict[str, Metric] = {}
        self.default_max_history = default_max_history
        self._lock = threading.RLock()
        self._callbacks: List[Callable[[str, MetricValue], None]] = []

    def create_metric(
        self,
        name: str,
        type: MetricType,
        description: str,
        max_history: Optional[int] = None
    ) -> Metric:
        """创建并注册指标"""
        with self._lock:
            if name in self.metrics:
                return self.metrics[name]

            metric = Metric(
                name=name,
                type=type,
                description=description,
                max_history=max_history or self.default_max_history
            )
            self.metrics[name] = metric
            return metric

    def get_metric(self, name: str) -> Optional[Metric]:
        """获取指标"""
        return self.metrics.get(name)

    def increment(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """递增计数器"""
        with self._lock:
            if name not in self.metrics:
                self.create_metric(name, MetricType.COUNTER, f"Counter: {name}")
            metric = self.metrics[name]
            # 计数器：取最后一个值递增（如果有）
            if metric.values:
                current = metric.values[-1].value
                metric.record(current + value, labels)
            else:
                metric.record(value, labels)
            self._notify_callbacks(name, metric.values[-1])

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """设置仪表值"""
        with self._lock:
            if name not in self.metrics:
                self.create_metric(name, MetricType.GAUGE, f"Gauge: {name}")
            metric = self.metrics[name]
            metric.record(value, labels)
            self._notify_callbacks(name, metric.values[-1])

    def record_value(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """记录任意值"""
        with self._lock:
            if name not in self.metrics:
                self.create_metric(name, MetricType.HISTOGRAM, f"Histogram: {name}")
            metric = self.metrics[name]
            metric.record(value, labels)
            self._notify_callbacks(name, metric.values[-1])

    def timer(self, name: str, labels: Optional[Dict[str, str]] = None) -> "TimerContext":
        """创建计时器上下文"""
        return TimerContext(self, name, labels)

    def _notify_callbacks(self, name: str, value: MetricValue) -> None:
        """通知指标变化回调"""
        for callback in self._callbacks:
            try:
                callback(name, value)
            except Exception:
                pass

    def add_callback(self, callback: Callable[[str, MetricValue], None]) -> None:
        """添加指标变化回调"""
        self._callbacks.append(callback)

    def get_all_metrics(self) -> Dict[str, Metric]:
        """获取所有指标"""
        with self._lock:
            return dict(self.metrics)

    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """获取所有指标的统计信息"""
        with self._lock:
            stats = {}
            for name, metric in self.metrics.items():
                stats[name] = metric.get_statistics()
            return stats


class TimerContext:
    """计时器上下文"""

    def __init__(self, registry: MetricsRegistry, name: str, labels: Optional[Dict[str, str]] = None):
        self.registry = registry
        self.name = name
        self.labels = labels or {}
        self.start_time: Optional[float] = None

    def __enter__(self) -> "TimerContext":
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.start_time is not None:
            elapsed = (time.time() - self.start_time) * 1000  # 毫秒
            self.registry.record_value(self.name, elapsed, self.labels)


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.rules: List[AlertRule] = []
        self.alerts: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def add_rule(self, rule: AlertRule) -> None:
        """添加告警规则"""
        with self._lock:
            self.rules.append(rule)

    def check_rules(self, registry: MetricsRegistry) -> List[Dict[str, Any]]:
        """检查告警规则"""
        with self._lock:
            triggered = []
            now = time.time()

            for rule in self.rules:
                metric = registry.get_metric(rule.metric_name)
                if not metric:
                    continue

                if rule.last_triggered:
                    if now - rule.last_triggered < rule.cooldown_seconds:
                        continue

                if rule.condition(metric):
                    alert = {
                        "rule_name": rule.name,
                        "metric_name": rule.metric_name,
                        "level": rule.level,
                        "message": rule.message,
                        "timestamp": now
                    }
                    self.alerts.append(alert)
                    triggered.append(alert)
                    rule.last_triggered = now

            return triggered

    def get_recent_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近的告警"""
        with self._lock:
            return list(self.alerts[-limit:])


class MonitoringReporter:
    """监控报告生成器"""

    def __init__(self, registry: MetricsRegistry, alert_manager: AlertManager):
        self.registry = registry
        self.alert_manager = alert_manager

    def generate_report(self, since: Optional[float] = None) -> Dict[str, Any]:
        """生成监控报告"""
        return {
            "timestamp": time.time(),
            "metrics": self.registry.get_statistics(),
            "recent_alerts": self.alert_manager.get_recent_alerts(limit=50)
        }

    def get_metric_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """获取单个指标的摘要"""
        metric = self.registry.get_metric(name)
        if not metric:
            return None

        return {
            "name": metric.name,
            "type": metric.type.value,
            "description": metric.description,
            "statistics": metric.get_statistics(),
            "latest_values": [v.value for v in metric.get_snapshot()[-10:]]
        }


class MonitoringManager:
    """监控管理器 - 整合所有监控功能"""

    def __init__(self):
        self.registry = MetricsRegistry()
        self.alert_manager = AlertManager()
        self.reporter = MonitoringReporter(self.registry, self.alert_manager)
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """启动监控"""
        self._running = True

    def stop(self) -> None:
        """停止监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)

    def increment(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """递增计数"""
        self.registry.increment(name, value, labels)

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """设置仪表值"""
        self.registry.set_gauge(name, value, labels)

    def record_value(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """记录值"""
        self.registry.record_value(name, value, labels)

    def timer(self, name: str, labels: Optional[Dict[str, str]] = None) -> TimerContext:
        """创建计时器"""
        return self.registry.timer(name, labels)

    def check_alerts(self) -> List[Dict[str, Any]]:
        """检查告警"""
        return self.alert_manager.check_rules(self.registry)

    def get_report(self) -> Dict[str, Any]:
        """获取监控报告"""
        return self.reporter.generate_report()

    def get_metric(self, name: str) -> Optional[Metric]:
        """获取指标"""
        return self.registry.get_metric(name)


def create_monitoring_manager() -> MonitoringManager:
    """创建监控管理器"""
    return MonitoringManager()


def create_alert_rule(
    name: str,
    metric_name: str,
    condition: Callable[[Metric], bool],
    message: str,
    level: str = "warning",
    cooldown_seconds: float = 60.0
) -> AlertRule:
    """创建告警规则"""
    return AlertRule(
        name=name,
        metric_name=metric_name,
        condition=condition,
        message=message,
        level=level,
        cooldown_seconds=cooldown_seconds
    )
