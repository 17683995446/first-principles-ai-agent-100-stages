# First Principles AI Agent - 快速开始指南

## 前言

欢迎使用基于第一性原理设计的 AI Agent 任务规划与执行系统！本指南将帮助您在5分钟内开始使用系统的核心功能。

## 核心概念速览

在开始之前，了解几个核心概念：

- **Task Quartet（任务四元组）**: 任务的标准化表示
  - Target: 目标
  - Preconditions: 前置条件
  - Constraints: 约束条件
  - End Rule: 终止规则

- **四层架构**:
  1. 任务归一建模层
  2. 拓扑依赖拆解层
  3. 原子动作收敛层
  4. 校验收敛机制层

## 5分钟快速开始

### 1. 安装（零依赖）

本项目仅依赖 Python 标准库，无需安装额外包！

```bash
cd /workspace
```

### 2. 运行最简单的示例

```bash
python quick_start.py
```

或运行简单工作版本：

```bash
python working_agent.py
```

### 3. 查看完整示例

```bash
python examples/complete_workflow.py
```

## 核心模块快速上手

### 模块1: 任务建模

```python
from first_principles_agent import Task, TaskQuartet

# 创建任务四元组
def end_condition(ctx):
    return "result" in ctx

quartet = TaskQuartet(
    target="Calculate (a + b) * c",
    end_rule=end_condition
)

# 创建主任务
task = Task("main_task", quartet, context={"a": 2, "b": 3, "c": 5})
```

### 模块2: 拓扑依赖拆解

```python
from first_principles_agent import TopologicalDecomposer, Task

decomposer = TopologicalDecomposer()

# 添加任务和依赖
task1 = Task("add", TaskQuartet(target="Add a and b"))
task2 = Task("multiply", TaskQuartet(target="Multiply by c"))

decomposer.add_task(task1)
decomposer.add_task(task2, dependencies=["add"])

# 获取执行顺序
order = decomposer.get_execution_order()
print(f"执行顺序: {order}")
```

### 模块3: 原子动作

```python
from first_principles_agent import AtomicAction

def add_func(ctx):
    return {"sum": ctx["a"] + ctx["b"]}

def multiply_func(ctx):
    return {"result": ctx["sum"] * ctx["c"]}

action1 = AtomicAction("add", "Addition", add_func)
action2 = AtomicAction("multiply", "Multiplication", multiply_func)
```

### 模块4: 验证机制

```python
from first_principles_agent import VerificationLayer, VerificationConfig

verifier = VerificationLayer()

# 配置验证
config = VerificationConfig(
    check_preconditions=True,
    check_constraints=True,
    check_postconditions=True
)

# 执行验证
result = verifier.verify(task, context, config)
print(f"验证结果: {result.success}")
```

### 模块5: 完整Agent使用

```python
from first_principles_agent import FirstPrinciplesAgent, Task, TaskQuartet, AtomicAction

# 1. 初始化 Agent
agent = FirstPrinciplesAgent()

# 2. 创建任务
def end_condition(ctx):
    return "final_result" in ctx

quartet = TaskQuartet(target="Complex calculation", end_rule=end_condition)
task = Task("main", quartet, context={"x": 10, "y": 20})
agent.set_task(task)

# 3. 创建子任务（有依赖）
sub1 = Task("step1", TaskQuartet(target="First step"))
sub2 = Task("step2", TaskQuartet(target="Second step"))
agent.add_subtask(sub1)
agent.add_subtask(sub2, dependencies=["step1"])

# 4. 添加原子动作
def step1_func(ctx):
    return {"intermediate": ctx["x"] + ctx["y"]}

def step2_func(ctx):
    return {"final_result": ctx["intermediate"] * 2}

action1 = AtomicAction("act1", "Step 1", step1_func)
action2 = AtomicAction("act2", "Step 2", step2_func)
agent.set_atomic_actions([action1, action2])

# 5. 执行
result = agent.execute()

# 6. 查看结果
print(f"Success: {result.success}")
print(f"Final Context: {result.context}")
```

## 高级功能快速入门

### 1. 任务调度

```python
from first_principles_agent import TaskScheduler, QueuedTask, TaskPriority

scheduler = TaskScheduler()

# 添加任务到队列
scheduler.enqueue(QueuedTask(
    task_id="task1",
    priority=TaskPriority.HIGH,
    task_data={"name": "Urgent task"}
))

# 执行调度
scheduler.start()
```

### 2. 重试与恢复

```python
from first_principles_agent import RetryManager, RetryConfig, RetryStrategy

retry_config = RetryConfig(
    max_retries=3,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    initial_delay=1
)
retry_manager = RetryManager(retry_config)

# 执行可重试操作
def unstable_operation():
    # 可能失败的操作
    pass

result = retry_manager.execute_with_retry(unstable_operation)
```

### 3. 配置管理

```python
from first_principles_agent import (
    ConfigManager, ConfigItem, ConfigType,
    get, set, get_int
)

# 创建配置管理器
manager = ConfigManager()

# 注册配置项
manager.register_config_item(ConfigItem(
    key="app.name",
    type_=ConfigType.STRING,
    default="My App"
))

# 使用全局API
set("app.name", "Updated App")
print(get("app.name"))  # "Updated App"
```

### 4. 日志记录

```python
from first_principles_agent import (
    get_logger, add_default_handler,
    info, warning, error, debug,
    LogLevel
)

# 添加处理器
add_default_handler(LogLevel.DEBUG)

# 记录日志
info("Application started")
debug("Debug information")
warning("Potential issue")
error("Error occurred")
```

### 5. 权限管理

```python
from first_principles_agent import (
    create_user, assign_role, register_role,
    register_permission, grant_access,
    check_user_permission,
    Permission, Role, PermissionType, ResourceType
)

# 注册权限和角色
register_permission(Permission("task.read", PermissionType.READ, ResourceType.TASK))
register_role(Role("admin", permissions={"task.read", "task.write"}))

# 创建用户并分配角色
user = create_user("admin_user")
assign_role(user.id, "admin")

# 授予资源访问权限
grant_access(user.id, "user", "task-001", PermissionType.READ)

# 检查权限
has_perm = check_user_permission(user.id, "task-001", PermissionType.READ)
```

### 6. 系统监控

```python
from first_principles_agent import (
    MonitoringManager, MetricType,
    create_monitoring_manager, create_alert_rule
)

# 创建监控管理器
monitor = create_monitoring_manager()

# 记录指标
monitor.record_gauge("system.load", 0.75)
monitor.record_counter("requests.total", 1)

# 配置告警
alert_rule = create_alert_rule(
    metric_name="system.load",
    threshold=0.9,
    comparison=">"
)
monitor.add_alert_rule(alert_rule)

# 获取监控数据
stats = monitor.get_statistics("system.load", 60)
```

## 运行测试

### 快速验证

```bash
# 运行快速验证
python quick_start.py
```

### 运行特定阶段测试

```bash
# 第78阶段配置管理测试
python test_stage_78_config.py

# 第79阶段安全管理测试
python test_stage_79_security.py

# 运行所有阶段测试
python test_runner.py
```

## 下一步

- 阅读完整文档：[README.md](README.md)
- 查看项目总结：[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- 深入学习示例：[examples/](examples/)
- 查看阶段文档：[stages/](stages/)

## 获取帮助

遇到问题时：
1. 查看相关阶段的完成报告
2. 运行对应测试文件验证功能
3. 检查源代码中的 docstring

---

祝使用愉快！
