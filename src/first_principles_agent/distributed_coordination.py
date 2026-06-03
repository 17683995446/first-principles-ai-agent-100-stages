"""
第75阶段：分布式协调与基础共识
实现节点管理、心跳检测、分布式锁、配置中心等基础分布式功能

核心原则：图难于其易，为大于其细。天下难事，必作于易；天下大事，必作于细。
"""

import time
import threading
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from enum import Enum
from collections import defaultdict
import queue


class NodeStatus(Enum):
    """节点状态"""
    JOINING = "joining"
    ACTIVE = "active"
    SUSPICIOUS = "suspicious"
    UNHEALTHY = "unhealthy"
    LEFT = "left"
    LEADER = "leader"


class ConsensusStatus(Enum):
    """共识状态"""
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


@dataclass
class NodeInfo:
    """节点信息"""
    node_id: str
    address: str
    port: int
    status: NodeStatus
    last_heartbeat: float
    join_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_leader: bool = False


@dataclass
class DistributedLockConfig:
    """分布式锁配置"""
    lock_timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 0.1
    heartbeat_interval_seconds: float = 5.0


@dataclass
class ConfigEntry:
    """配置条目"""
    key: str
    value: str
    version: int
    created_time: float
    modified_time: float
    created_by: str


class HeartbeatManager:
    """心跳管理器"""

    def __init__(self, node_id: str, heartbeat_interval: float = 5.0, timeout_threshold: float = 15.0):
        self.node_id = node_id
        self.heartbeat_interval = heartbeat_interval
        self.timeout_threshold = timeout_threshold
        self._nodes: Dict[str, NodeInfo] = {}
        self._lock = threading.RLock()
        self._heartbeat_callbacks: List[Callable[[str, NodeStatus], None]] = []
        self._running = False
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._check_thread: Optional[threading.Thread] = None

    def register_node(self, node_id: str, address: str, port: int, metadata: Optional[Dict] = None) -> NodeInfo:
        """注册节点"""
        with self._lock:
            node = NodeInfo(
                node_id=node_id,
                address=address,
                port=port,
                status=NodeStatus.JOINING,
                last_heartbeat=time.time(),
                join_time=time.time(),
                metadata=metadata or {}
            )
            self._nodes[node_id] = node
            return node

    def unregister_node(self, node_id: str):
        """注销节点"""
        with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id].status = NodeStatus.LEFT
                del self._nodes[node_id]

    def record_heartbeat(self, node_id: str):
        """记录心跳"""
        with self._lock:
            if node_id not in self._nodes:
                return
            node = self._nodes[node_id]
            node.last_heartbeat = time.time()
            if node.status == NodeStatus.SUSPICIOUS or node.status == NodeStatus.UNHEALTHY:
                node.status = NodeStatus.ACTIVE
                self._notify_callbacks(node_id, NodeStatus.ACTIVE)

    def get_node(self, node_id: str) -> Optional[NodeInfo]:
        """获取节点信息"""
        with self._lock:
            return self._nodes.get(node_id)

    def get_all_nodes(self) -> List[NodeInfo]:
        """获取所有节点"""
        with self._lock:
            return list(self._nodes.values())

    def get_active_nodes(self) -> List[NodeInfo]:
        """获取活跃节点"""
        with self._lock:
            return [
                node for node in self._nodes.values()
                if node.status == NodeStatus.ACTIVE or node.status == NodeStatus.LEADER
            ]

    def add_heartbeat_callback(self, callback: Callable[[str, NodeStatus], None]):
        """添加心跳回调"""
        self._heartbeat_callbacks.append(callback)

    def _notify_callbacks(self, node_id: str, status: NodeStatus):
        """通知回调"""
        for callback in self._heartbeat_callbacks:
            try:
                callback(node_id, status)
            except Exception:
                pass

    def start(self):
        """启动心跳管理"""
        if self._running:
            return
        self._running = True
        self._heartbeat_thread = threading.Thread(target=self._self_heartbeat_loop, daemon=True)
        self._check_thread = threading.Thread(target=self._check_health_loop, daemon=True)
        self._heartbeat_thread.start()
        self._check_thread.start()

    def stop(self):
        """停止心跳管理"""
        self._running = False
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2.0)
        if self._check_thread:
            self._check_thread.join(timeout=2.0)

    def _self_heartbeat_loop(self):
        """自身心跳循环"""
        while self._running:
            self.record_heartbeat(self.node_id)
            time.sleep(self.heartbeat_interval)

    def _check_health_loop(self):
        """健康检查循环"""
        while self._running:
            now = time.time()
            with self._lock:
                for node_id, node in self._nodes.items():
                    if node_id == self.node_id:
                        continue

                    elapsed = now - node.last_heartbeat
                    if elapsed > self.timeout_threshold:
                        if node.status == NodeStatus.ACTIVE or node.status == NodeStatus.LEADER:
                            node.status = NodeStatus.UNHEALTHY
                            self._notify_callbacks(node_id, NodeStatus.UNHEALTHY)
                    elif elapsed > (self.timeout_threshold * 0.6):
                        if node.status == NodeStatus.ACTIVE or node.status == NodeStatus.LEADER:
                            node.status = NodeStatus.SUSPICIOUS
                            self._notify_callbacks(node_id, NodeStatus.SUSPICIOUS)
            time.sleep(1.0)


class DistributedLock:
    """分布式锁"""

    def __init__(self, lock_id: str, config: Optional[DistributedLockConfig] = None):
        self.lock_id = lock_id
        self.config = config or DistributedLockConfig()
        self._holder: Optional[str] = None
        self._lock_acquired_time: Optional[float] = None
        self._lock = threading.RLock()
        self._wait_queue: queue.Queue = queue.Queue()
        self._lock_thread: Optional[threading.Thread] = None
        self._released = threading.Event()

    def acquire(
        self,
        client_id: str,
        timeout_seconds: Optional[float] = None
    ) -> bool:
        """获取锁"""
        timeout = timeout_seconds or self.config.lock_timeout_seconds
        deadline = time.time() + timeout

        retry_count = 0
        while time.time() < deadline:
            with self._lock:
                if self._holder is None:
                    self._holder = client_id
                    self._lock_acquired_time = time.time()
                    self._start_lock_renewal()
                    return True

            retry_count += 1
            if retry_count >= self.config.max_retries:
                return False

            try:
                self._wait_queue.get(timeout=self.config.retry_delay_seconds)
            except queue.Empty:
                continue

        return False

    def release(self, client_id: str) -> bool:
        """释放锁"""
        with self._lock:
            if self._holder != client_id:
                return False

            self._holder = None
            self._lock_acquired_time = None
            self._stop_lock_renewal()

            try:
                self._wait_queue.put(True, block=False)
            except queue.Full:
                pass

            return True

    def is_held(self) -> bool:
        """检查锁是否被持有"""
        with self._lock:
            return self._holder is not None

    def get_holder(self) -> Optional[str]:
        """获取锁持有者"""
        with self._lock:
            return self._holder

    def _start_lock_renewal(self):
        """启动锁续租"""
        self._released.clear()
        self._lock_thread = threading.Thread(target=self._renewal_loop, daemon=True)
        self._lock_thread.start()

    def _stop_lock_renewal(self):
        """停止锁续租"""
        self._released.set()

    def _renewal_loop(self):
        """锁续租循环"""
        while not self._released.is_set():
            time.sleep(self.config.heartbeat_interval_seconds)


class DistributedLockManager:
    """分布式锁管理器"""

    def __init__(self, default_config: Optional[DistributedLockConfig] = None):
        self.default_config = default_config or DistributedLockConfig()
        self._locks: Dict[str, DistributedLock] = {}
        self._lock = threading.RLock()

    def get_lock(self, lock_id: str, config: Optional[DistributedLockConfig] = None) -> DistributedLock:
        """获取或创建锁"""
        with self._lock:
            if lock_id not in self._locks:
                self._locks[lock_id] = DistributedLock(lock_id, config or self.default_config)
            return self._locks[lock_id]

    def try_acquire(
        self,
        lock_id: str,
        client_id: str,
        timeout_seconds: Optional[float] = None
    ) -> bool:
        """尝试获取锁"""
        lock = self.get_lock(lock_id)
        return lock.acquire(client_id, timeout_seconds)

    def release(self, lock_id: str, client_id: str) -> bool:
        """释放锁"""
        with self._lock:
            if lock_id not in self._locks:
                return False
            return self._locks[lock_id].release(client_id)

    def get_active_locks(self) -> Dict[str, str]:
        """获取活跃锁信息"""
        with self._lock:
            return {
                lock_id: lock.get_holder()
                for lock_id, lock in self._locks.items()
                if lock.is_held()
            }


class ConfigurationCenter:
    """配置中心"""

    def __init__(self):
        self._configs: Dict[str, ConfigEntry] = {}
        self._watchers: Dict[str, List[Callable[[str, str, int], None]]] = defaultdict(list)
        self._lock = threading.RLock()

    def set(self, key: str, value: str, created_by: str = "system") -> ConfigEntry:
        """设置配置"""
        with self._lock:
            now = time.time()
            if key in self._configs:
                entry = self._configs[key]
                entry.value = value
                entry.version += 1
                entry.modified_time = now
            else:
                entry = ConfigEntry(
                    key=key,
                    value=value,
                    version=1,
                    created_time=now,
                    modified_time=now,
                    created_by=created_by
                )
                self._configs[key] = entry

            self._notify_watchers(key, value, entry.version)
            return entry

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取配置"""
        with self._lock:
            entry = self._configs.get(key)
            return entry.value if entry else default

    def get_with_version(self, key: str) -> Optional[tuple]:
        """获取配置和版本"""
        with self._lock:
            entry = self._configs.get(key)
            return (entry.value, entry.version) if entry else None

    def delete(self, key: str) -> bool:
        """删除配置"""
        with self._lock:
            if key not in self._configs:
                return False
            del self._configs[key]
            self._notify_watchers(key, None, -1)
            return True

    def watch(self, key: str, callback: Callable[[str, str, int], None]):
        """监听配置变化"""
        with self._lock:
            self._watchers[key].append(callback)

    def unwatch(self, key: str, callback: Callable[[str, str, int], None]):
        """取消监听"""
        with self._lock:
            if key in self._watchers:
                if callback in self._watchers[key]:
                    self._watchers[key].remove(callback)

    def _notify_watchers(self, key: str, value: Optional[str], version: int):
        """通知监听者"""
        callbacks = self._watchers.get(key, [])
        for callback in callbacks:
            try:
                callback(key, value, version)
            except Exception:
                pass

    def get_all(self) -> Dict[str, ConfigEntry]:
        """获取所有配置"""
        with self._lock:
            return self._configs.copy()


class DistributedCoordinator:
    """分布式协调器"""

    def __init__(
        self,
        node_id: Optional[str] = None,
        heartbeat_interval: float = 5.0,
        timeout_threshold: float = 15.0
    ):
        self.node_id = node_id or str(uuid.uuid4())
        self.heartbeat_manager = HeartbeatManager(
            node_id=self.node_id,
            heartbeat_interval=heartbeat_interval,
            timeout_threshold=timeout_threshold
        )
        self.lock_manager = DistributedLockManager()
        self.config_center = ConfigurationCenter()
        self._consensus_status = ConsensusStatus.FOLLOWER
        self._lock = threading.RLock()

    def start(self):
        """启动协调器"""
        self.heartbeat_manager.start()

    def stop(self):
        """停止协调器"""
        self.heartbeat_manager.stop()

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        with self._lock:
            return {
                "node_id": self.node_id,
                "consensus_status": self._consensus_status.value,
                "active_nodes": len(self.heartbeat_manager.get_active_nodes()),
                "total_nodes": len(self.heartbeat_manager.get_all_nodes()),
                "active_locks": len(self.lock_manager.get_active_locks()),
                "config_count": len(self.config_center.get_all())
            }


def create_heartbeat_manager(
    node_id: str,
    heartbeat_interval: float = 5.0,
    timeout_threshold: float = 15.0
) -> HeartbeatManager:
    """创建心跳管理器"""
    return HeartbeatManager(node_id, heartbeat_interval, timeout_threshold)


def create_distributed_lock_manager(config: Optional[DistributedLockConfig] = None) -> DistributedLockManager:
    """创建分布式锁管理器"""
    return DistributedLockManager(config)


def create_configuration_center() -> ConfigurationCenter:
    """创建配置中心"""
    return ConfigurationCenter()


def create_distributed_coordinator(
    node_id: Optional[str] = None,
    heartbeat_interval: float = 5.0,
    timeout_threshold: float = 15.0
) -> DistributedCoordinator:
    """创建分布式协调器"""
    return DistributedCoordinator(node_id, heartbeat_interval, timeout_threshold)
