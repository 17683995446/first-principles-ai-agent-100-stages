"""
第71阶段：调度器性能优化
实现调度器的性能监控、算法优化、缓存和批量处理功能

核心原则：图难于其易，为大于其细。天下难事，必作于易；天下大事，必作于细。
"""

import time
import threading
import functools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from collections import defaultdict, deque
from enum import Enum


class PerformanceMetricType(Enum):
    """性能指标类型"""
    LATENCY = "latency"              # 延迟
    THROUGHPUT = "throughput"        # 吞吐量
    MEMORY = "memory"                # 内存使用
    CPU = "cpu"                      # CPU使用
    QUEUE_LENGTH = "queue_length"    # 队列长度
    CACHE_HIT = "cache_hit"          # 缓存命中
    CACHE_MISS = "cache_miss"        # 缓存未命中


@dataclass
class PerformanceMetric:
    """性能指标记录"""
    metric_type: PerformanceMetricType
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    task_id: Optional[str] = None


@dataclass
class PerformanceStats:
    """性能统计"""
    min_value: float = float('inf')
    max_value: float = float('-inf')
    avg_value: float = 0.0
    total_count: int = 0
    sum_value: float = 0.0
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0


class LatencyTracker:
    """延迟跟踪器"""
    
    def __init__(self, max_samples: int = 10000):
        self.max_samples = max_samples
        self.samples: List[Tuple[float, float]] = []  # (timestamp, value)
        self._lock = threading.RLock()
    
    def record(self, value: float):
        """记录延迟值"""
        with self._lock:
            timestamp = time.time()
            self.samples.append((timestamp, value))
            if len(self.samples) > self.max_samples:
                self.samples = self.samples[-self.max_samples:]
    
    def get_stats(self) -> PerformanceStats:
        """获取统计信息"""
        with self._lock:
            if not self.samples:
                return PerformanceStats()
            
            values = [v for _, v in self.samples]
            sorted_values = sorted(values)
            n = len(sorted_values)
            
            return PerformanceStats(
                min_value=min(values),
                max_value=max(values),
                avg_value=sum(values) / n,
                total_count=n,
                sum_value=sum(values),
                p50=sorted_values[int(n * 0.5)],
                p95=sorted_values[int(n * 0.95)] if n > 20 else sorted_values[-1],
                p99=sorted_values[int(n * 0.99)] if n > 100 else sorted_values[-1]
            )
    
    def get_recent_stats(self, window_seconds: float = 60.0) -> PerformanceStats:
        """获取最近时间窗口的统计"""
        with self._lock:
            now = time.time()
            recent_values = [
                v for ts, v in self.samples
                if now - ts <= window_seconds
            ]
            
            if not recent_values:
                return PerformanceStats()
            
            sorted_values = sorted(recent_values)
            n = len(sorted_values)
            
            return PerformanceStats(
                min_value=min(recent_values),
                max_value=max(recent_values),
                avg_value=sum(recent_values) / n,
                total_count=n,
                sum_value=sum(recent_values),
                p50=sorted_values[int(n * 0.5)],
                p95=sorted_values[int(n * 0.95)] if n > 20 else sorted_values[-1],
                p99=sorted_values[int(n * 0.99)] if n > 100 else sorted_values[-1]
            )


class ThroughputTracker:
    """吞吐量跟踪器"""
    
    def __init__(self, window_seconds: float = 60.0, bucket_size: float = 1.0):
        self.window_seconds = window_seconds
        self.bucket_size = bucket_size
        self.buckets: Dict[int, int] = defaultdict(int)
        self._lock = threading.RLock()
    
    def _get_bucket(self, timestamp: float) -> int:
        """获取时间桶"""
        return int(timestamp / self.bucket_size)
    
    def record(self, count: int = 1):
        """记录吞吐量"""
        with self._lock:
            bucket = self._get_bucket(time.time())
            self.buckets[bucket] += count
            self._cleanup_old_buckets()
    
    def _cleanup_old_buckets(self):
        """清理过期的时间桶"""
        now = time.time()
        min_bucket = self._get_bucket(now - self.window_seconds)
        old_buckets = [b for b in self.buckets if b < min_bucket]
        for b in old_buckets:
            del self.buckets[b]
    
    def get_throughput(self) -> float:
        """获取当前吞吐量（每秒）"""
        with self._lock:
            self._cleanup_old_buckets()
            total = sum(self.buckets.values())
            return total / self.window_seconds


class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: Optional[float] = None):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[Any, Tuple[Any, float]] = {}  # key -> (value, timestamp)
        self.order: deque = deque()
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: Any) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            value, timestamp = self.cache[key]
            
            if self.ttl_seconds and (time.time() - timestamp) > self.ttl_seconds:
                del self.cache[key]
                self.misses += 1
                return None
            
            self.hits += 1
            self.order.remove(key)
            self.order.append(key)
            return value
    
    def put(self, key: Any, value: Any):
        """设置缓存值"""
        with self._lock:
            if key in self.cache:
                self.order.remove(key)
            elif len(self.cache) >= self.max_size:
                oldest_key = self.order.popleft()
                del self.cache[oldest_key]
            
            self.cache[key] = (value, time.time())
            self.order.append(key)
    
    def get_hit_rate(self) -> float:
        """获取缓存命中率"""
        with self._lock:
            total = self.hits + self.misses
            return self.hits / total if total > 0 else 0.0
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self.cache.clear()
            self.order.clear()
            self.hits = 0
            self.misses = 0


class BatchProcessor:
    """批量处理器"""
    
    def __init__(
        self,
        process_func: Callable[[List[Any]], List[Any]],
        batch_size: int = 100,
        flush_interval_seconds: float = 1.0
    ):
        self.process_func = process_func
        self.batch_size = batch_size
        self.flush_interval_seconds = flush_interval_seconds
        self.queue: deque = deque()
        self.results: Dict[int, Any] = {}
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._counter = 0
    
    def start(self):
        """启动批量处理器"""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()
    
    def stop(self):
        """停止批量处理器"""
        with self._lock:
            self._running = False
            self._condition.notify_all()
        if self._thread:
            self._thread.join()
    
    def submit(self, item: Any) -> Any:
        """提交单个项目"""
        with self._lock:
            item_id = self._counter
            self._counter += 1
            self.queue.append((item_id, item))
            
            if len(self.queue) >= self.batch_size:
                self._condition.notify_all()
            
            while item_id not in self.results:
                self._condition.wait()
            
            result = self.results.pop(item_id)
            return result
    
    def submit_batch(self, items: List[Any]) -> List[Any]:
        """提交批量项目"""
        results = []
        for item in items:
            results.append(self.submit(item))
        return results
    
    def _worker(self):
        """工作线程"""
        while True:
            with self._lock:
                while self._running and len(self.queue) < self.batch_size:
                    self._condition.wait(self.flush_interval_seconds)
                
                if not self._running and not self.queue:
                    return
                
                batch = []
                while self.queue and len(batch) < self.batch_size:
                    batch.append(self.queue.popleft())
                
                if not batch:
                    continue
            
            item_ids = [item_id for item_id, _ in batch]
            items = [item for _, item in batch]
            
            processed = self.process_func(items)
            
            with self._lock:
                for item_id, result in zip(item_ids, processed):
                    self.results[item_id] = result
                self._condition.notify_all()


def measure_latency(func: Callable):
    """性能装饰器：测量函数执行延迟"""
    tracker = LatencyTracker()
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            latency = (time.time() - start_time) * 1000  # 毫秒
            tracker.record(latency)
    
    wrapper.tracker = tracker
    return wrapper


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.latency_trackers: Dict[str, LatencyTracker] = {}
        self.throughput_trackers: Dict[str, ThroughputTracker] = {}
        self.caches: Dict[str, LRUCache] = {}
        self.metrics: List[PerformanceMetric] = []
        self._lock = threading.RLock()
    
    def get_latency_tracker(self, name: str) -> LatencyTracker:
        """获取或创建延迟跟踪器"""
        with self._lock:
            if name not in self.latency_trackers:
                self.latency_trackers[name] = LatencyTracker()
            return self.latency_trackers[name]
    
    def get_throughput_tracker(self, name: str) -> ThroughputTracker:
        """获取或创建吞吐量跟踪器"""
        with self._lock:
            if name not in self.throughput_trackers:
                self.throughput_trackers[name] = ThroughputTracker()
            return self.throughput_trackers[name]
    
    def get_cache(self, name: str, max_size: int = 1000) -> LRUCache:
        """获取或创建缓存"""
        with self._lock:
            if name not in self.caches:
                self.caches[name] = LRUCache(max_size=max_size)
            return self.caches[name]
    
    def record_metric(self, metric: PerformanceMetric):
        """记录性能指标"""
        with self._lock:
            self.metrics.append(metric)
            if len(self.metrics) > 10000:
                self.metrics = self.metrics[-10000:]
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有统计信息"""
        with self._lock:
            stats = {
                "latency": {},
                "throughput": {},
                "cache": {}
            }
            
            for name, tracker in self.latency_trackers.items():
                stats["latency"][name] = tracker.get_stats()
            
            for name, tracker in self.throughput_trackers.items():
                stats["throughput"][name] = tracker.get_throughput()
            
            for name, cache in self.caches.items():
                stats["cache"][name] = {
                    "size": len(cache.cache),
                    "max_size": cache.max_size,
                    "hits": cache.hits,
                    "misses": cache.misses,
                    "hit_rate": cache.get_hit_rate()
                }
            
            return stats


class OptimizedScheduler:
    """性能优化的调度器"""
    
    def __init__(self, monitor: Optional[PerformanceMonitor] = None):
        self.monitor = monitor or PerformanceMonitor()
        self.node_cache = self.monitor.get_cache("node_selection", max_size=500)
        self.latency_tracker = self.monitor.get_latency_tracker("scheduling")
        self.throughput_tracker = self.monitor.get_throughput_tracker("tasks")
        self._lock = threading.RLock()
    
    @measure_latency
    def optimized_select_node(self, requirement, nodes):
        """优化的节点选择算法"""
        cache_key = (
            frozenset((n.node_id, n.get_overall_load()) for n in nodes),
            requirement.cpu_cores,
            requirement.memory_gb
        )
        
        cached = self.node_cache.get(cache_key)
        if cached:
            return cached
        
        eligible = [n for n in nodes if requirement.can_allocate_on(n)]
        if not eligible:
            return None
        
        result = min(eligible, key=lambda n: n.get_overall_load())
        self.node_cache.put(cache_key, result)
        return result
    
    def submit_task_optimized(self, requirement, nodes):
        """优化的任务提交"""
        start = time.time()
        node = self.optimized_select_node(requirement, nodes)
        latency = (time.time() - start) * 1000
        self.latency_tracker.record(latency)
        self.throughput_tracker.record()
        return node
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return self.monitor.get_all_stats()


def create_performance_monitor() -> PerformanceMonitor:
    """创建性能监控器的便捷函数"""
    return PerformanceMonitor()


def create_lru_cache(max_size: int = 1000, ttl_seconds: Optional[float] = None) -> LRUCache:
    """创建LRU缓存的便捷函数"""
    return LRUCache(max_size=max_size, ttl_seconds=ttl_seconds)


def create_batch_processor(
    process_func: Callable,
    batch_size: int = 100,
    flush_interval: float = 1.0
) -> BatchProcessor:
    """创建批量处理器的便捷函数"""
    return BatchProcessor(
        process_func=process_func,
        batch_size=batch_size,
        flush_interval_seconds=flush_interval
    )
