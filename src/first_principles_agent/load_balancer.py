"""
第70阶段：负载均衡与资源分配
第一性原理AI Agent任务规划系统

核心原则：图难于其易，为大于其细。天下难事，必作于易；天下大事，必作于细。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
import time
import threading
from collections import defaultdict


class ResourceType(Enum):
    """资源类型枚举"""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK_IO = "network_io"
    DISK_IO = "disk_io"
    GPU = "gpu"


class LoadBalanceStrategy(Enum):
    """负载均衡策略枚举"""
    ROUND_ROBIN = "round_robin"  # 轮询
    LEAST_CONNECTIONS = "least_connections"  # 最少连接
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"  # 加权轮询
    LEAST_RESOURCE_USAGE = "least_resource_usage"  # 最少资源使用
    RANDOM = "random"  # 随机


@dataclass
class ResourceCapacity:
    """资源容量配置"""
    cpu_cores: float = 8.0
    memory_gb: float = 32.0
    network_mbps: float = 1000.0
    disk_iops: float = 10000.0
    gpu_count: int = 0


@dataclass
class ResourceUsage:
    """资源使用状态"""
    cpu_usage: float = 0.0
    memory_used_gb: float = 0.0
    network_used_mbps: float = 0.0
    disk_used_iops: float = 0.0
    gpu_used: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass
class WorkerNode:
    """工作节点"""
    node_id: str
    name: str
    capacity: ResourceCapacity = field(default_factory=ResourceCapacity)
    current_usage: ResourceUsage = field(default_factory=ResourceUsage)
    active_tasks: int = 0
    weight: float = 1.0
    is_healthy: bool = True
    last_heartbeat: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_resource_usage_ratio(self, resource_type: ResourceType) -> float:
        """获取资源使用率"""
        if resource_type == ResourceType.CPU:
            return self.current_usage.cpu_usage / self.capacity.cpu_cores if self.capacity.cpu_cores > 0 else 0
        elif resource_type == ResourceType.MEMORY:
            return self.current_usage.memory_used_gb / self.capacity.memory_gb if self.capacity.memory_gb > 0 else 0
        elif resource_type == ResourceType.NETWORK_IO:
            return self.current_usage.network_used_mbps / self.capacity.network_mbps if self.capacity.network_mbps > 0 else 0
        elif resource_type == ResourceType.DISK_IO:
            return self.current_usage.disk_used_iops / self.capacity.disk_iops if self.capacity.disk_iops > 0 else 0
        elif resource_type == ResourceType.GPU:
            return self.current_usage.gpu_used / self.capacity.gpu_count if self.capacity.gpu_count > 0 else 0
        return 0.0
    
    def get_overall_load(self) -> float:
        """获取综合负载（0-1）"""
        cpu_ratio = self.get_resource_usage_ratio(ResourceType.CPU)
        mem_ratio = self.get_resource_usage_ratio(ResourceType.MEMORY)
        net_ratio = self.get_resource_usage_ratio(ResourceType.NETWORK_IO)
        disk_ratio = self.get_resource_usage_ratio(ResourceType.DISK_IO)
        
        return (cpu_ratio + mem_ratio + net_ratio + disk_ratio) / 4.0


@dataclass
class TaskResourceRequirement:
    """任务资源需求"""
    task_id: str
    cpu_cores: float = 1.0
    memory_gb: float = 2.0
    network_mbps: float = 10.0
    disk_iops: float = 100.0
    gpu_count: int = 0
    priority: float = 5.0
    deadline: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    
    def can_allocate_on(self, node: WorkerNode) -> bool:
        """检查是否可以在节点上分配"""
        if not node.is_healthy:
            return False
        
        available_cpu = node.capacity.cpu_cores - node.current_usage.cpu_usage
        available_mem = node.capacity.memory_gb - node.current_usage.memory_used_gb
        available_net = node.capacity.network_mbps - node.current_usage.network_used_mbps
        available_disk = node.capacity.disk_iops - node.current_usage.disk_used_iops
        available_gpu = node.capacity.gpu_count - node.current_usage.gpu_used
        
        return (
            available_cpu >= self.cpu_cores and
            available_mem >= self.memory_gb and
            available_net >= self.network_mbps and
            available_disk >= self.disk_iops and
            available_gpu >= self.gpu_count
        )


@dataclass
class AllocationDecision:
    """资源分配决策"""
    task_id: str
    node_id: str
    success: bool
    reason: str = ""
    timestamp: float = field(default_factory=time.time)


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, strategy: LoadBalanceStrategy = LoadBalanceStrategy.LEAST_RESOURCE_USAGE):
        self.strategy = strategy
        self.nodes: Dict[str, WorkerNode] = {}
        self.round_robin_index = 0
        self._lock = threading.RLock()
        self.primary_resource: ResourceType = ResourceType.CPU
        
    def register_node(self, node: WorkerNode) -> None:
        """注册工作节点"""
        with self._lock:
            self.nodes[node.node_id] = node
    
    def unregister_node(self, node_id: str) -> None:
        """注销工作节点"""
        with self._lock:
            if node_id in self.nodes:
                del self.nodes[node_id]
    
    def update_node_usage(self, node_id: str, usage: ResourceUsage) -> bool:
        """更新节点资源使用情况"""
        with self._lock:
            if node_id not in self.nodes:
                return False
            self.nodes[node_id].current_usage = usage
            self.nodes[node_id].last_heartbeat = time.time()
            return True
    
    def update_node_health(self, node_id: str, is_healthy: bool) -> bool:
        """更新节点健康状态"""
        with self._lock:
            if node_id not in self.nodes:
                return False
            self.nodes[node_id].is_healthy = is_healthy
            self.nodes[node_id].last_heartbeat = time.time()
            return True
    
    def get_healthy_nodes(self) -> List[WorkerNode]:
        """获取所有健康节点"""
        with self._lock:
            return [node for node in self.nodes.values() if node.is_healthy]
    
    def select_node(self, requirement: TaskResourceRequirement) -> Optional[WorkerNode]:
        """根据策略选择节点"""
        healthy_nodes = self.get_healthy_nodes()
        if not healthy_nodes:
            return None
        
        # 筛选能满足资源需求的节点
        eligible_nodes = [node for node in healthy_nodes if requirement.can_allocate_on(node)]
        if not eligible_nodes:
            return None
        
        if self.strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._select_round_robin(eligible_nodes)
        elif self.strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return self._select_least_connections(eligible_nodes)
        elif self.strategy == LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN:
            return self._select_weighted_round_robin(eligible_nodes)
        elif self.strategy == LoadBalanceStrategy.LEAST_RESOURCE_USAGE:
            return self._select_least_resource(eligible_nodes)
        elif self.strategy == LoadBalanceStrategy.RANDOM:
            return self._select_random(eligible_nodes)
        else:
            return eligible_nodes[0]
    
    def _select_round_robin(self, nodes: List[WorkerNode]) -> WorkerNode:
        """轮询策略"""
        with self._lock:
            node = nodes[self.round_robin_index % len(nodes)]
            self.round_robin_index += 1
            return node
    
    def _select_least_connections(self, nodes: List[WorkerNode]) -> WorkerNode:
        """最少连接策略"""
        return min(nodes, key=lambda n: n.active_tasks)
    
    def _select_weighted_round_robin(self, nodes: List[WorkerNode]) -> WorkerNode:
        """加权轮询策略"""
        with self._lock:
            total_weight = sum(node.weight for node in nodes)
            target = (self.round_robin_index % int(total_weight * 100)) / 100.0
            self.round_robin_index += 1
            
            current = 0.0
            for node in nodes:
                current += node.weight
                if current >= target:
                    return node
            return nodes[-1]
    
    def _select_least_resource(self, nodes: List[WorkerNode]) -> WorkerNode:
        """最少资源使用策略"""
        return min(nodes, key=lambda n: n.get_overall_load())
    
    def _select_random(self, nodes: List[WorkerNode]) -> WorkerNode:
        """随机策略"""
        import random
        return random.choice(nodes)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            healthy_count = sum(1 for n in self.nodes.values() if n.is_healthy)
            total_active_tasks = sum(n.active_tasks for n in self.nodes.values())
            avg_load = (
                sum(n.get_overall_load() for n in self.nodes.values()) / len(self.nodes)
                if self.nodes else 0.0
            )
            
            return {
                "total_nodes": len(self.nodes),
                "healthy_nodes": healthy_count,
                "active_tasks": total_active_tasks,
                "average_load": avg_load,
                "strategy": self.strategy.value,
                "nodes": {
                    node_id: {
                        "name": node.name,
                        "active_tasks": node.active_tasks,
                        "load": node.get_overall_load(),
                        "healthy": node.is_healthy
                    }
                    for node_id, node in self.nodes.items()
                }
            }


class ResourceAllocator:
    """资源分配器"""
    
    def __init__(self, load_balancer: LoadBalancer):
        self.load_balancer = load_balancer
        self.allocations: Dict[str, AllocationDecision] = {}
        self.task_node_map: Dict[str, str] = {}
        self._lock = threading.RLock()
        self.allocation_history: List[AllocationDecision] = []
    
    def allocate(self, requirement: TaskResourceRequirement) -> AllocationDecision:
        """分配资源"""
        with self._lock:
            # 选择节点
            node = self.load_balancer.select_node(requirement)
            
            if not node:
                decision = AllocationDecision(
                    task_id=requirement.task_id,
                    node_id="",
                    success=False,
                    reason="No eligible node available"
                )
                self._record_allocation(decision)
                return decision
            
            # 分配资源
            node.current_usage.cpu_usage += requirement.cpu_cores
            node.current_usage.memory_used_gb += requirement.memory_gb
            node.current_usage.network_used_mbps += requirement.network_mbps
            node.current_usage.disk_used_iops += requirement.disk_iops
            node.current_usage.gpu_used += requirement.gpu_count
            node.active_tasks += 1
            
            decision = AllocationDecision(
                task_id=requirement.task_id,
                node_id=node.node_id,
                success=True,
                reason="Allocation successful"
            )
            
            self.task_node_map[requirement.task_id] = node.node_id
            self._record_allocation(decision)
            return decision
    
    def release(self, task_id: str) -> bool:
        """释放资源"""
        with self._lock:
            if task_id not in self.task_node_map:
                return False
            
            node_id = self.task_node_map[task_id]
            node = self.load_balancer.nodes.get(node_id)
            
            if not node:
                del self.task_node_map[task_id]
                return False
            
            # 查找原始需求（简化实现，实际应存储）
            # 这里假设释放1单位资源作为示例
            node.current_usage.cpu_usage = max(0, node.current_usage.cpu_usage - 1.0)
            node.current_usage.memory_used_gb = max(0, node.current_usage.memory_used_gb - 2.0)
            node.current_usage.network_used_mbps = max(0, node.current_usage.network_used_mbps - 10.0)
            node.current_usage.disk_used_iops = max(0, node.current_usage.disk_used_iops - 100.0)
            node.current_usage.gpu_used = max(0, node.current_usage.gpu_used)
            
            node.active_tasks = max(0, node.active_tasks - 1)
            
            del self.task_node_map[task_id]
            return True
    
    def _record_allocation(self, decision: AllocationDecision) -> None:
        """记录分配历史"""
        self.allocations[decision.task_id] = decision
        self.allocation_history.append(decision)
        # 保留最近1000条记录
        if len(self.allocation_history) > 1000:
            self.allocation_history = self.allocation_history[-1000:]
    
    def get_allocation(self, task_id: str) -> Optional[AllocationDecision]:
        """获取任务分配信息"""
        return self.allocations.get(task_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            success_count = sum(1 for d in self.allocations.values() if d.success)
            total_count = len(self.allocations)
            success_rate = success_count / total_count if total_count > 0 else 0.0
            
            node_allocations = defaultdict(int)
            for task_id, node_id in self.task_node_map.items():
                node_allocations[node_id] += 1
            
            return {
                "total_allocations": total_count,
                "success_rate": success_rate,
                "active_allocations": len(self.task_node_map),
                "node_allocations": dict(node_allocations),
                "history_count": len(self.allocation_history)
            }


class LoadBalancedScheduler:
    """负载均衡调度器（集成版）"""
    
    def __init__(
        self,
        strategy: LoadBalanceStrategy = LoadBalanceStrategy.LEAST_RESOURCE_USAGE
    ):
        self.load_balancer = LoadBalancer(strategy)
        self.resource_allocator = ResourceAllocator(self.load_balancer)
        self._lock = threading.RLock()
    
    def add_worker_node(
        self,
        node_id: str,
        name: str,
        capacity: Optional[ResourceCapacity] = None,
        weight: float = 1.0
    ) -> None:
        """添加工作节点"""
        node = WorkerNode(
            node_id=node_id,
            name=name,
            capacity=capacity or ResourceCapacity(),
            weight=weight
        )
        self.load_balancer.register_node(node)
    
    def submit_task(self, requirement: TaskResourceRequirement) -> AllocationDecision:
        """提交任务并分配资源"""
        return self.resource_allocator.allocate(requirement)
    
    def complete_task(self, task_id: str) -> bool:
        """完成任务并释放资源"""
        return self.resource_allocator.release(task_id)
    
    def update_node_metrics(self, node_id: str, usage: ResourceUsage) -> bool:
        """更新节点指标"""
        return self.load_balancer.update_node_usage(node_id, usage)
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """获取系统统计"""
        with self._lock:
            lb_stats = self.load_balancer.get_statistics()
            alloc_stats = self.resource_allocator.get_statistics()
            
            return {
                "load_balancer": lb_stats,
                "resource_allocator": alloc_stats,
                "timestamp": time.time()
            }


def create_load_balancer(
    strategy: str = "least_resource_usage"
) -> LoadBalancer:
    """创建负载均衡器的便捷函数"""
    strategy_map = {
        "round_robin": LoadBalanceStrategy.ROUND_ROBIN,
        "least_connections": LoadBalanceStrategy.LEAST_CONNECTIONS,
        "weighted_round_robin": LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN,
        "least_resource_usage": LoadBalanceStrategy.LEAST_RESOURCE_USAGE,
        "random": LoadBalanceStrategy.RANDOM
    }
    return LoadBalancer(strategy_map.get(strategy, LoadBalanceStrategy.LEAST_RESOURCE_USAGE))


def create_resource_capacity(
    cpu_cores: float = 8.0,
    memory_gb: float = 32.0,
    network_mbps: float = 1000.0,
    disk_iops: float = 10000.0,
    gpu_count: int = 0
) -> ResourceCapacity:
    """创建资源容量配置的便捷函数"""
    return ResourceCapacity(
        cpu_cores=cpu_cores,
        memory_gb=memory_gb,
        network_mbps=network_mbps,
        disk_iops=disk_iops,
        gpu_count=gpu_count
    )


def create_task_requirement(
    task_id: str,
    cpu_cores: float = 1.0,
    memory_gb: float = 2.0,
    network_mbps: float = 10.0,
    disk_iops: float = 100.0,
    gpu_count: int = 0,
    priority: float = 5.0,
    deadline: Optional[float] = None,
    tags: Optional[List[str]] = None
) -> TaskResourceRequirement:
    """创建任务资源需求的便捷函数"""
    return TaskResourceRequirement(
        task_id=task_id,
        cpu_cores=cpu_cores,
        memory_gb=memory_gb,
        network_mbps=network_mbps,
        disk_iops=disk_iops,
        gpu_count=gpu_count,
        priority=priority,
        deadline=deadline,
        tags=tags or []
    )
