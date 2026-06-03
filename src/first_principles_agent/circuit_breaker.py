"""
第73阶段：任务熔断器与限流器
实现服务的熔断保护、流量控制和舱壁隔离

核心原则：图难于其易，为大于其细。天下难事，必作于易；天下大事，必作于细。
"""

import time
import threading
import functools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 熔断器关闭，正常工作
    OPEN = "open"         # 熔断器打开，快速失败
    HALF_OPEN = "half_open"  # 半开状态，尝试恢复


class RateLimitStrategy(Enum):
    """限流策略"""
    TOKEN_BUCKET = "token_bucket"      # 令牌桶
    SLIDING_WINDOW = "sliding_window"  # 滑动窗口
    FIXED_WINDOW = "fixed_window"      # 固定窗口


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5          # 失败次数阈值
    success_threshold: int = 3         # 成功次数阈值（半开恢复）
    timeout_seconds: float = 30.0      # 熔断超时时间
    half_open_max_calls: int = 3       # 半开状态最大尝试次数
    enable_slow_call_threshold: bool = False
    slow_call_threshold_seconds: float = 2.0
    slow_call_threshold_percentage: float = 50.0


@dataclass
class CircuitBreakerStats:
    """熔断器统计"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    average_duration_ms: float = 0.0
    state_changes: List[tuple] = field(default_factory=list)


class CircuitBreaker:
    """熔断器实现"""

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = threading.RLock()
        self._stats = CircuitBreakerStats()
        self._call_durations: List[float] = []
        self._state_change_history: List[tuple] = []

    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
            return self._state

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置"""
        if self._last_failure_time is None:
            return True
        return (time.time() - self._last_failure_time) >= self.config.timeout_seconds

    def _transition_to_half_open(self):
        """转换到半开状态"""
        old_state = self._state
        self._state = CircuitState.HALF_OPEN
        self._half_open_calls = 0
        self._state_change_history.append((time.time(), old_state, CircuitState.HALF_OPEN))
        print(f"熔断器 [{self.name}]: {old_state.value} -> half_open")

    def _transition_to_open(self):
        """转换到打开状态"""
        old_state = self._state
        self._state = CircuitState.OPEN
        self._failure_count = 0
        self._state_change_history.append((time.time(), old_state, CircuitState.OPEN))
        print(f"熔断器 [{self.name}]: {old_state.value} -> open")

    def _transition_to_closed(self):
        """转换到关闭状态"""
        old_state = self._state
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._state_change_history.append((time.time(), old_state, CircuitState.CLOSED))
        print(f"熔断器 [{self.name}]: {old_state.value} -> closed")

    def record_success(self, duration_ms: float = 0.0):
        """记录成功调用"""
        with self._lock:
            self._stats.successful_calls += 1
            self._stats.total_calls += 1
            if duration_ms > 0:
                self._call_durations.append(duration_ms)
                self._stats.average_duration_ms = sum(self._call_durations) / len(self._call_durations)

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                self._half_open_calls += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    def record_failure(self, duration_ms: float = 0.0):
        """记录失败调用"""
        with self._lock:
            self._stats.failed_calls += 1
            self._stats.total_calls += 1
            self._last_failure_time = time.time()

            if duration_ms > 0:
                self._call_durations.append(duration_ms)
                self._stats.average_duration_ms = sum(self._call_durations) / len(self._call_durations)

            if self._state == CircuitState.HALF_OPEN:
                self._transition_to_open()
            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to_open()

    def is_callable(self) -> bool:
        """检查是否允许调用"""
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            elif self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
            else:
                self._stats.rejected_calls += 1
                return False

    def get_stats(self) -> CircuitBreakerStats:
        """获取统计信息"""
        with self._lock:
            return CircuitBreakerStats(
                total_calls=self._stats.total_calls,
                successful_calls=self._stats.successful_calls,
                failed_calls=self._stats.failed_calls,
                rejected_calls=self._stats.rejected_calls,
                average_duration_ms=self._stats.average_duration_ms,
                state_changes=self._state_change_history[-10:]
            )

    def reset(self):
        """重置熔断器"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            self._stats = CircuitBreakerStats()


def circuit_breaker_decorator(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
):
    """熔断器装饰器"""
    breaker = CircuitBreaker(name, config)

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not breaker.is_callable():
                raise Exception(f"熔断器 [{name}] 已打开，拒绝调用")

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                breaker.record_success(duration_ms)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                breaker.record_failure(duration_ms)
                raise

        wrapper.circuit_breaker = breaker
        return wrapper

    return decorator


@dataclass
class RateLimitConfig:
    """限流器配置"""
    max_requests: int = 100              # 最大请求数
    time_window_seconds: float = 1.0     # 时间窗口
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    burst_size: Optional[int] = None     # 突发容量


class RateLimiter:
    """限流器"""

    def __init__(self, name: str, config: Optional[RateLimitConfig] = None):
        self.name = name
        self.config = config or RateLimitConfig()
        self._lock = threading.Lock()
        self._buckets: Dict[str, float] = {}  # 令牌桶
        self._request_counts: Dict[str, List[float]] = {}  # 滑动窗口
        self._total_requests = 0
        self._rejected_requests = 0

    def _get_or_create_bucket(self, key: str) -> float:
        """获取或创建令牌桶"""
        if key not in self._buckets:
            burst = self.config.burst_size or self.config.max_requests
            self._buckets[key] = burst
        return self._buckets[key]

    def _get_window_requests(self, key: str) -> List[float]:
        """获取窗口内的请求"""
        if key not in self._request_counts:
            self._request_counts[key] = []
        return self._request_counts[key]

    def _cleanup_window(self, requests: List[float], now: float):
        """清理过期的请求记录"""
        cutoff = now - self.config.time_window_seconds
        while requests and requests[0] < cutoff:
            requests.pop(0)

    def try_acquire(self, key: str = "default") -> bool:
        """
        尝试获取令牌

        Returns:
            True: 获取成功
            False: 被限流拒绝
        """
        with self._lock:
            now = time.time()

            if self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                return self._try_acquire_token_bucket(key, now)
            elif self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return self._try_acquire_sliding_window(key, now)
            elif self.config.strategy == RateLimitStrategy.FIXED_WINDOW:
                return self._try_acquire_fixed_window(key, now)

            return False

    def _try_acquire_token_bucket(self, key: str, now: float) -> bool:
        """令牌桶限流"""
        bucket = self._get_or_create_bucket(key)
        rate = self.config.max_requests / self.config.time_window_seconds

        bucket = min(bucket + rate * (now - self._buckets.get(f"{key}_last_refill", now)),
                     self.config.burst_size or self.config.max_requests)
        self._buckets[key] = bucket
        self._buckets[f"{key}_last_refill"] = now

        if bucket >= 1.0:
            self._buckets[key] -= 1.0
            self._total_requests += 1
            return True
        else:
            self._rejected_requests += 1
            return False

    def _try_acquire_sliding_window(self, key: str, now: float) -> bool:
        """滑动窗口限流"""
        requests = self._get_window_requests(key)
        self._cleanup_window(requests, now)

        if len(requests) < self.config.max_requests:
            requests.append(now)
            self._total_requests += 1
            return True
        else:
            self._rejected_requests += 1
            return False

    def _try_acquire_fixed_window(self, key: str, now: float) -> bool:
        """固定窗口限流"""
        requests = self._get_window_requests(key)
        self._cleanup_window(requests, now)

        if len(requests) < self.config.max_requests:
            requests.append(now)
            self._total_requests += 1
            return True
        else:
            self._rejected_requests += 1
            return False

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "name": self.name,
                "strategy": self.config.strategy.value,
                "max_requests": self.config.max_requests,
                "time_window_seconds": self.config.time_window_seconds,
                "total_requests": self._total_requests,
                "rejected_requests": self._rejected_requests,
                "rejection_rate": self._rejected_requests / self._total_requests if self._total_requests > 0 else 0
            }

    def reset(self):
        """重置限流器"""
        with self._lock:
            self._buckets.clear()
            self._request_counts.clear()
            self._total_requests = 0
            self._rejected_requests = 0


class Bulkhead:
    """舱壁隔离模式"""

    def __init__(self, max_concurrent_calls: int = 10, max_queue_size: int = 0):
        self.max_concurrent_calls = max_concurrent_calls
        self.max_queue_size = max_queue_size
        self._semaphore = threading.Semaphore(max_concurrent_calls)
        self._lock = threading.Lock()
        self._active_calls = 0
        self._queued_calls = 0
        self._rejected_calls = 0
        self._total_calls = 0

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """执行带舱壁保护的函数"""
        with self._lock:
            self._total_calls += 1

            if self._active_calls >= self.max_concurrent_calls:
                if self.max_queue_size > 0 and self._queued_calls < self.max_queue_size:
                    self._queued_calls += 1
                else:
                    self._rejected_calls += 1
                    raise Exception(f"舱壁已满，拒绝调用")
            else:
                self._active_calls += 1

        try:
            return func(*args, **kwargs)
        finally:
            with self._lock:
                if self._queued_calls > 0:
                    self._queued_calls -= 1
                else:
                    self._active_calls -= 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "max_concurrent_calls": self.max_concurrent_calls,
                "max_queue_size": self.max_queue_size,
                "active_calls": self._active_calls,
                "queued_calls": self._queued_calls,
                "rejected_calls": self._rejected_calls,
                "total_calls": self._total_calls
            }


class ResilienceManager:
    """弹性管理器 - 整合所有弹性机制"""

    def __init__(self, name: str = "Resilience"):
        self.name = name
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.bulkheads: Dict[str, Bulkhead] = {}
        self._lock = threading.RLock()

    def register_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """注册熔断器"""
        with self._lock:
            self.circuit_breakers[name] = CircuitBreaker(name, config)

    def register_rate_limiter(self, name: str, config: Optional[RateLimitConfig] = None):
        """注册限流器"""
        with self._lock:
            self.rate_limiters[name] = RateLimiter(name, config)

    def register_bulkhead(self, name: str, max_concurrent: int = 10, max_queue: int = 0):
        """注册舱壁"""
        with self._lock:
            self.bulkheads[name] = Bulkhead(max_concurrent, max_queue)

    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """获取熔断器"""
        return self.circuit_breakers.get(name)

    def get_rate_limiter(self, name: str) -> Optional[RateLimiter]:
        """获取限流器"""
        return self.rate_limiters.get(name)

    def get_bulkhead(self, name: str) -> Optional[Bulkhead]:
        """获取舱壁"""
        return self.bulkheads.get(name)

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有统计"""
        with self._lock:
            stats = {
                "circuit_breakers": {},
                "rate_limiters": {},
                "bulkheads": {}
            }

            for name, cb in self.circuit_breakers.items():
                cb_stats = cb.get_stats()
                stats["circuit_breakers"][name] = {
                    "state": cb.state.value,
                    "total_calls": cb_stats.total_calls,
                    "rejected_calls": cb_stats.rejected_calls
                }

            for name, rl in self.rate_limiters.items():
                stats["rate_limiters"][name] = rl.get_stats()

            for name, bh in self.bulkheads.items():
                stats["bulkheads"][name] = bh.get_stats()

            return stats


def create_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """创建熔断器"""
    return CircuitBreaker(name, config)


def create_rate_limiter(name: str, config: Optional[RateLimitConfig] = None) -> RateLimiter:
    """创建限流器"""
    return RateLimiter(name, config)


def create_bulkhead(max_concurrent: int = 10, max_queue: int = 0) -> Bulkhead:
    """创建舱壁"""
    return Bulkhead(max_concurrent, max_queue)


def create_resilience_manager(name: str = "Resilience") -> ResilienceManager:
    """创建弹性管理器"""
    return ResilienceManager(name)
