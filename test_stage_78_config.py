import unittest
import tempfile
import json
import os
from pathlib import Path

from src.first_principles_agent.config import (
    ConfigType, ConfigValidationError, ConfigItem,
    EnvironmentConfig, ConfigChangeEvent, ConfigChangeListener,
    ConfigManager,
    get_config_manager, set_config_manager,
    register_config_item, register_config_items,
    get, set, get_int, get_float, get_bool, get_list, get_dict,
    switch_environment, load_from_file, save_to_file,
    add_listener, remove_listener, validate_all
)


class TestConfigItem(unittest.TestCase):
    """测试配置项定义"""
    
    def test_config_item_creation(self):
        """测试配置项创建"""
        item = ConfigItem(
            key="app.name",
            type_=ConfigType.STRING,
            default="MyApp",
            required=True,
            description="应用名称"
        )
        self.assertEqual(item.key, "app.name")
        self.assertEqual(item.type_, ConfigType.STRING)
        self.assertEqual(item.default, "MyApp")
        self.assertTrue(item.required)
        self.assertEqual(item.description, "应用名称")
    
    def test_config_item_with_constraints(self):
        """测试带约束的配置项"""
        item = ConfigItem(
            key="app.port",
            type_=ConfigType.INTEGER,
            default=8080,
            min_value=1024,
            max_value=65535,
            allowed_values=[8080, 9090, 3000]
        )
        self.assertEqual(item.min_value, 1024)
        self.assertEqual(item.max_value, 65535)
        self.assertEqual(item.allowed_values, [8080, 9090, 3000])


class TestConfigValidation(unittest.TestCase):
    """测试配置验证"""
    
    def setUp(self):
        self.manager = ConfigManager()
    
    def test_type_validation(self):
        """测试类型验证"""
        self.manager.register_config_item(
            ConfigItem(key="test.string", type_=ConfigType.STRING)
        )
        self.manager.register_config_item(
            ConfigItem(key="test.int", type_=ConfigType.INTEGER)
        )
        self.manager.register_config_item(
            ConfigItem(key="test.bool", type_=ConfigType.BOOLEAN)
        )
        
        error = self.manager.validate_config("test.string", "valid")
        self.assertIsNone(error)
        
        error = self.manager.validate_config("test.string", 123)
        self.assertIsNotNone(error)
        self.assertIn("Invalid type", error.message)
        
        error = self.manager.validate_config("test.int", 123)
        self.assertIsNone(error)
        
        error = self.manager.validate_config("test.bool", True)
        self.assertIsNone(error)
    
    def test_range_validation(self):
        """测试范围验证"""
        self.manager.register_config_item(
            ConfigItem(key="test.range", type_=ConfigType.INTEGER, min_value=0, max_value=100)
        )
        
        error = self.manager.validate_config("test.range", 50)
        self.assertIsNone(error)
        
        error = self.manager.validate_config("test.range", -1)
        self.assertIsNotNone(error)
        self.assertIn("must be >=", error.message)
        
        error = self.manager.validate_config("test.range", 101)
        self.assertIsNotNone(error)
        self.assertIn("must be <=", error.message)
    
    def test_allowed_values_validation(self):
        """测试允许值验证"""
        self.manager.register_config_item(
            ConfigItem(
                key="test.allowed",
                type_=ConfigType.STRING,
                allowed_values=["dev", "test", "prod"]
            )
        )
        
        error = self.manager.validate_config("test.allowed", "dev")
        self.assertIsNone(error)
        
        error = self.manager.validate_config("test.allowed", "invalid")
        self.assertIsNotNone(error)
        self.assertIn("must be in", error.message)
    
    def test_length_validation(self):
        """测试长度验证"""
        self.manager.register_config_item(
            ConfigItem(
                key="test.length",
                type_=ConfigType.STRING,
                min_length=3,
                max_length=10
            )
        )
        
        error = self.manager.validate_config("test.length", "abc")
        self.assertIsNone(error)
        
        error = self.manager.validate_config("test.length", "ab")
        self.assertIsNotNone(error)
        self.assertIn("Length must be >=", error.message)
        
        error = self.manager.validate_config("test.length", "abcdefghijk")
        self.assertIsNotNone(error)
        self.assertIn("Length must be <=", error.message)
    
    def test_required_validation(self):
        """测试必填项验证"""
        self.manager.register_config_item(
            ConfigItem(key="test.required", type_=ConfigType.STRING, required=True)
        )
        
        error = self.manager.validate_config("test.required", None)
        self.assertIsNotNone(error)
        self.assertIn("Required config", error.message)
        
        error = self.manager.validate_config("test.required", "value")
        self.assertIsNone(error)
    
    def test_custom_validator(self):
        """测试自定义验证器"""
        def is_even(value):
            return value % 2 == 0
        
        self.manager.register_config_item(
            ConfigItem(
                key="test.even",
                type_=ConfigType.INTEGER,
                validator=is_even
            )
        )
        
        error = self.manager.validate_config("test.even", 4)
        self.assertIsNone(error)
        
        error = self.manager.validate_config("test.even", 5)
        self.assertIsNotNone(error)
        self.assertIn("Validation failed", error.message)


class TestConfigManager(unittest.TestCase):
    """测试配置管理器"""
    
    def setUp(self):
        self.manager = ConfigManager()
    
    def test_set_and_get(self):
        """测试设置和获取配置"""
        self.manager.register_config_item(
            ConfigItem(key="app.name", type_=ConfigType.STRING, default="MyApp")
        )
        
        self.assertEqual(self.manager.get("app.name"), "MyApp")
        
        error = self.manager.set("app.name", "NewApp")
        self.assertIsNone(error)
        self.assertEqual(self.manager.get("app.name"), "NewApp")
    
    def test_type_specific_getters(self):
        """测试类型特定的获取方法"""
        self.manager.register_config_items([
            ConfigItem(key="int.val", type_=ConfigType.INTEGER, default=42),
            ConfigItem(key="float.val", type_=ConfigType.FLOAT, default=3.14),
            ConfigItem(key="bool.val", type_=ConfigType.BOOLEAN, default=True),
            ConfigItem(key="list.val", type_=ConfigType.LIST, default=[1, 2, 3]),
            ConfigItem(key="dict.val", type_=ConfigType.DICT, default={"key": "val"}),
        ])
        
        self.assertEqual(self.manager.get_int("int.val"), 42)
        self.assertEqual(self.manager.get_float("float.val"), 3.14)
        self.assertEqual(self.manager.get_bool("bool.val"), True)
        self.assertEqual(self.manager.get_list("list.val"), [1, 2, 3])
        self.assertEqual(self.manager.get_dict("dict.val"), {"key": "val"})
    
    def test_batch_operations(self):
        """测试批量操作"""
        self.manager.register_config_items([
            ConfigItem(key="a", type_=ConfigType.INTEGER),
            ConfigItem(key="b", type_=ConfigType.STRING),
            ConfigItem(key="c", type_=ConfigType.BOOLEAN),
        ])
        
        errors = self.manager.batch_set({"a": 1, "b": "test", "c": True})
        self.assertEqual(len(errors), 0)
        
        result = self.manager.batch_get(["a", "b", "c"])
        self.assertEqual(result["a"], 1)
        self.assertEqual(result["b"], "test")
        self.assertEqual(result["c"], True)
    
    def test_delete_and_clear(self):
        """测试删除和清空"""
        self.manager.register_config_item(
            ConfigItem(key="test.key", type_=ConfigType.STRING, default="value")
        )
        
        self.assertTrue(self.manager.delete("test.key"))
        self.assertIsNone(self.manager.get("test.key"))
        
        self.manager.set("a", 1)
        self.manager.set("b", 2)
        self.manager.clear()
        self.assertEqual(len(self.manager.get_all_configs()), 0)
    
    def test_dict_access(self):
        """测试字典式访问"""
        self.manager.register_config_item(
            ConfigItem(key="test.key", type_=ConfigType.STRING, default="value")
        )
        
        self.assertEqual(self.manager["test.key"], "value")
        
        self.manager["test.key"] = "new value"
        self.assertEqual(self.manager["test.key"], "new value")
        
        self.assertTrue("test.key" in self.manager)
        self.assertFalse("nonexistent" in self.manager)


class TestConfigChangeListener(unittest.TestCase):
    """测试配置变更监听"""
    
    def setUp(self):
        self.manager = ConfigManager()
        self.changes = []
        
        class TestListener(ConfigChangeListener):
            def __init__(self, changes_list):
                self.changes_list = changes_list
            
            def on_config_change(self, event):
                self.changes_list.append(event)
        
        self.listener = TestListener(self.changes)
    
    def test_change_notification(self):
        """测试变更通知"""
        self.manager.register_config_item(
            ConfigItem(key="test.key", type_=ConfigType.STRING, default="initial")
        )
        
        self.manager.add_listener(self.listener)
        
        self.manager.set("test.key", "changed")
        
        self.assertEqual(len(self.changes), 1)
        self.assertEqual(self.changes[0].key, "test.key")
        self.assertEqual(self.changes[0].old_value, "initial")
        self.assertEqual(self.changes[0].new_value, "changed")
    
    def test_remove_listener(self):
        """测试移除监听器"""
        self.manager.register_config_item(
            ConfigItem(key="test.key", type_=ConfigType.STRING)
        )
        
        self.manager.add_listener(self.listener)
        self.manager.set("test.key", "first")
        self.assertEqual(len(self.changes), 1)
        
        self.manager.remove_listener(self.listener)
        self.manager.set("test.key", "second")
        self.assertEqual(len(self.changes), 1)


class TestEnvironmentConfig(unittest.TestCase):
    """测试环境配置"""
    
    def setUp(self):
        self.manager = ConfigManager()
    
    def test_register_and_switch_environment(self):
        """测试注册和切换环境"""
        dev_env = EnvironmentConfig(
            name="dev",
            configs={"log.level": "DEBUG", "db.host": "localhost"}
        )
        prod_env = EnvironmentConfig(
            name="prod",
            configs={"log.level": "INFO", "db.host": "prod.db"}
        )
        
        self.manager.register_environment(dev_env)
        self.manager.register_environment(prod_env)
        
        self.assertEqual(self.manager.list_environments(), ["dev", "prod"])
        
        self.assertTrue(self.manager.switch_environment("dev"))
        self.assertEqual(self.manager.get("log.level"), "DEBUG")
        self.assertEqual(self.manager.get_current_environment(), "dev")
        
        self.assertTrue(self.manager.switch_environment("prod"))
        self.assertEqual(self.manager.get("log.level"), "INFO")
        self.assertEqual(self.manager.get_current_environment(), "prod")
    
    def test_environment_inheritance(self):
        """测试环境继承"""
        base_env = EnvironmentConfig(
            name="base",
            configs={"log.level": "INFO", "common.key": "common"}
        )
        dev_env = EnvironmentConfig(
            name="dev",
            configs={"log.level": "DEBUG", "dev.key": "dev"},
            parent="base"
        )
        
        self.manager.register_environment(base_env)
        self.manager.register_environment(dev_env)
        
        self.assertTrue(self.manager.switch_environment("dev"))
        self.assertEqual(self.manager.get("log.level"), "DEBUG")
        self.assertEqual(self.manager.get("common.key"), "common")
        self.assertEqual(self.manager.get("dev.key"), "dev")


class TestConfigPersistence(unittest.TestCase):
    """测试配置持久化"""
    
    def setUp(self):
        self.manager = ConfigManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_json_serialization(self):
        """测试JSON序列化"""
        self.manager.set("string", "value")
        self.manager.set("int", 42)
        self.manager.set("float", 3.14)
        self.manager.set("bool", True)
        self.manager.set("list", [1, 2, 3])
        self.manager.set("dict", {"key": "val"})
        
        json_str = self.manager.save_to_json()
        self.assertIsInstance(json_str, str)
        
        data = json.loads(json_str)
        self.assertEqual(data["string"], "value")
        self.assertEqual(data["int"], 42)
        self.assertEqual(data["float"], 3.14)
        self.assertEqual(data["bool"], True)
        self.assertEqual(data["list"], [1, 2, 3])
        self.assertEqual(data["dict"], {"key": "val"})
    
    def test_file_persistence(self):
        """测试文件持久化"""
        self.manager.set("app.name", "TestApp")
        self.manager.set("app.version", "1.0.0")
        
        file_path = os.path.join(self.temp_dir, "config.json")
        
        self.assertTrue(self.manager.save_to_file(file_path))
        self.assertTrue(os.path.exists(file_path))
        
        new_manager = ConfigManager()
        errors = new_manager.load_from_file(file_path)
        self.assertEqual(len(errors), 0)
        
        self.assertEqual(new_manager.get("app.name"), "TestApp")
        self.assertEqual(new_manager.get("app.version"), "1.0.0")
    
    def test_load_from_dict(self):
        """测试从字典加载"""
        data = {"a": 1, "b": "test", "c": True}
        errors = self.manager.load_from_dict(data)
        self.assertEqual(len(errors), 0)
        
        self.assertEqual(self.manager.get("a"), 1)
        self.assertEqual(self.manager.get("b"), "test")
        self.assertEqual(self.manager.get("c"), True)


class TestGlobalConfig(unittest.TestCase):
    """测试全局配置API"""
    
    def setUp(self):
        set_config_manager(ConfigManager())
    
    def test_global_operations(self):
        """测试全局操作"""
        register_config_item(
            ConfigItem(key="global.key", type_=ConfigType.STRING, default="default")
        )
        
        self.assertEqual(get("global.key"), "default")
        
        error = set("global.key", "new value")
        self.assertIsNone(error)
        self.assertEqual(get("global.key"), "new value")
    
    def test_global_type_getters(self):
        """测试全局类型获取方法"""
        register_config_items([
            ConfigItem(key="g.int", type_=ConfigType.INTEGER, default=100),
            ConfigItem(key="g.float", type_=ConfigType.FLOAT, default=99.9),
            ConfigItem(key="g.bool", type_=ConfigType.BOOLEAN, default=False),
            ConfigItem(key="g.list", type_=ConfigType.LIST, default=[4, 5, 6]),
            ConfigItem(key="g.dict", type_=ConfigType.DICT, default={"g": "val"}),
        ])
        
        self.assertEqual(get_int("g.int"), 100)
        self.assertEqual(get_float("g.float"), 99.9)
        self.assertEqual(get_bool("g.bool"), False)
        self.assertEqual(get_list("g.list"), [4, 5, 6])
        self.assertEqual(get_dict("g.dict"), {"g": "val"})
    
    def test_global_validate_all(self):
        """测试全局验证"""
        register_config_items([
            ConfigItem(key="valid1", type_=ConfigType.STRING, required=True),
            ConfigItem(key="valid2", type_=ConfigType.INTEGER, min_value=0),
        ])
        
        set("valid1", "value")
        set("valid2", 10)
        
        errors = validate_all()
        self.assertEqual(len(errors), 0)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestConfigItem))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigManager))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigChangeListener))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigPersistence))
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalConfig))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
