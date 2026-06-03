#!/usr/bin/env python3
"""快速验证配置模块功能"""

from src.first_principles_agent.config import (
    ConfigType, ConfigValidationError, ConfigItem,
    EnvironmentConfig, ConfigChangeEvent, ConfigChangeListener,
    ConfigManager,
    get_config_manager, set_config_manager,
    register_config_item, register_config_items,
    get, set, get_int, get_float, get_bool, get_list, get_dict,
    switch_environment, validate_all
)

print("=" * 60)
print("第78阶段：配置管理与环境适配系统 - 快速验证")
print("=" * 60)

# 1. 测试配置项注册和基本功能
print("\n1. 测试配置项注册和基本功能...")
manager = ConfigManager()
manager.register_config_item(
    ConfigItem(key="app.name", type_=ConfigType.STRING, default="MyApp")
)
manager.register_config_item(
    ConfigItem(key="app.port", type_=ConfigType.INTEGER, default=8080, min_value=1024, max_value=65535)
)
assert manager.get("app.name") == "MyApp"
assert manager.get_int("app.port") == 8080
print("   ✓ 基本功能测试通过")

# 2. 测试配置设置和验证
print("\n2. 测试配置设置和验证...")
error = manager.set("app.name", "NewApp")
assert error is None
assert manager.get("app.name") == "NewApp"

error = manager.set("app.port", 9090)
assert error is None
assert manager.get_int("app.port") == 9090

# 测试验证失败
error = manager.set("app.port", 99999)
assert error is not None
print("   ✓ 配置验证测试通过")

# 3. 测试环境配置
print("\n3. 测试环境配置...")
dev_env = EnvironmentConfig(
    name="dev",
    configs={"log.level": "DEBUG", "db.host": "localhost"}
)
prod_env = EnvironmentConfig(
    name="prod",
    configs={"log.level": "INFO", "db.host": "prod.db"}
)
manager.register_environment(dev_env)
manager.register_environment(prod_env)

manager.switch_environment("dev")
assert manager.get("log.level") == "DEBUG"
assert manager.get_current_environment() == "dev"

manager.switch_environment("prod")
assert manager.get("log.level") == "INFO"
assert manager.get_current_environment() == "prod"
print("   ✓ 环境配置测试通过")

# 4. 测试全局API
print("\n4. 测试全局API...")
set_config_manager(ConfigManager())
register_config_items([
    ConfigItem(key="global.key", type_=ConfigType.STRING, default="default"),
    ConfigItem(key="global.int", type_=ConfigType.INTEGER, default=100),
])

assert get("global.key") == "default"
set("global.key", "new value")
assert get("global.key") == "new value"
assert get_int("global.int") == 100
print("   ✓ 全局API测试通过")

# 5. 测试配置变更监听
print("\n5. 测试配置变更监听...")
changes = []

class TestListener(ConfigChangeListener):
    def on_config_change(self, event):
        changes.append(event)

listener = TestListener(changes)
manager = ConfigManager()
manager.register_config_item(ConfigItem(key="test.key", type_=ConfigType.STRING))
manager.add_listener(listener)
manager.set("test.key", "changed")
assert len(changes) == 1
assert changes[0].key == "test.key"
print("   ✓ 配置变更监听测试通过")

# 6. 测试JSON序列化
print("\n6. 测试JSON序列化...")
manager = ConfigManager()
manager.set("string", "value")
manager.set("int", 42)
json_str = manager.save_to_json()
assert "string" in json_str
assert "int" in json_str
print("   ✓ JSON序列化测试通过")

print("\n" + "=" * 60)
print("所有快速验证测试通过！✓")
print("=" * 60)
