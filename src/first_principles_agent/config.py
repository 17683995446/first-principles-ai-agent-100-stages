
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Callable, Union, Set
import threading
import json
import os
from pathlib import Path


class ConfigType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"


@dataclass
class ConfigValidationError:
    field: str
    message: str
    value: Any = None


@dataclass
class ConfigItem:
    key: str
    type_: ConfigType
    default: Any = None
    required: bool = False
    description: str = ""
    validator: Optional[Callable[[Any], bool]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None


@dataclass
class EnvironmentConfig:
    name: str
    configs: Dict[str, Any] = field(default_factory=dict)
    parent: Optional[str] = None


class ConfigChangeEvent:
    def __init__(self, key: str, old_value: Any, new_value: Any):
        self.key = key
        self.old_value = old_value
        self.new_value = new_value
        self.timestamp = time.time()


class ConfigChangeListener:
    def on_config_change(self, event: ConfigChangeEvent):
        pass


class ConfigManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._config_items: Dict[str, ConfigItem] = {}
        self._configs: Dict[str, Any] = {}
        self._environments: Dict[str, EnvironmentConfig] = {}
        self._current_environment: Optional[str] = None
        self._listeners: List[ConfigChangeListener] = []
        self._initialized = False

    def register_config_item(self, item: ConfigItem) -> None:
        with self._lock:
            self._config_items[item.key] = item
            if item.key not in self._configs and item.default is not None:
                self._configs[item.key] = item.default

    def register_config_items(self, items: List[ConfigItem]) -> None:
        for item in items:
            self.register_config_item(item)

    def get_config_item(self, key: str) -> Optional[ConfigItem]:
        return self._config_items.get(key)

    def validate_config(self, key: str, value: Any) -> Optional[ConfigValidationError]:
        item = self._config_items.get(key)
        if not item:
            return ConfigValidationError(key, "Config item not registered", value)
        
        if item.required and value is None:
            return ConfigValidationError(key, "Required config cannot be None", value)
        
        if value is None:
            return None
        
        if not self._validate_type(item.type_, value):
            return ConfigValidationError(key, f"Invalid type, expected {item.type_.value}", value)
        
        if item.min_value is not None and value < item.min_value:
            return ConfigValidationError(key, f"Value must be >= {item.min_value}", value)
        
        if item.max_value is not None and value > item.max_value:
            return ConfigValidationError(key, f"Value must be <= {item.max_value}", value)
        
        if item.allowed_values is not None and value not in item.allowed_values:
            return ConfigValidationError(key, f"Value must be in {item.allowed_values}", value)
        
        if isinstance(value, (str, list, dict)):
            if item.min_length is not None and len(value) < item.min_length:
                return ConfigValidationError(key, f"Length must be >= {item.min_length}", value)
            if item.max_length is not None and len(value) > item.max_length:
                return ConfigValidationError(key, f"Length must be <= {item.max_length}", value)
        
        if item.validator and not item.validator(value):
            return ConfigValidationError(key, "Validation failed", value)
        
        return None

    def _validate_type(self, type_: ConfigType, value: Any) -> bool:
        type_checks = {
            ConfigType.STRING: lambda v: isinstance(v, str),
            ConfigType.INTEGER: lambda v: isinstance(v, int) and not isinstance(v, bool),
            ConfigType.FLOAT: lambda v: isinstance(v, (int, float)),
            ConfigType.BOOLEAN: lambda v: isinstance(v, bool),
            ConfigType.LIST: lambda v: isinstance(v, list),
            ConfigType.DICT: lambda v: isinstance(v, dict),
        }
        return type_checks.get(type_, lambda v: False)(value)

    def set(self, key: str, value: Any, validate: bool = True) -> Optional[ConfigValidationError]:
        with self._lock:
            if validate:
                error = self.validate_config(key, value)
                if error:
                    return error
            
            old_value = self._configs.get(key)
            self._configs[key] = value
            
            if old_value != value:
                event = ConfigChangeEvent(key, old_value, value)
                self._notify_listeners(event)
            
            return None

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._configs.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        value = self.get(key, default)
        return int(value) if value is not None else default

    def get_float(self, key: str, default: float = 0.0) -> float:
        value = self.get(key, default)
        return float(value) if value is not None else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.get(key, default)
        return bool(value) if value is not None else default

    def get_list(self, key: str, default: Optional[List] = None) -> List:
        value = self.get(key, default or [])
        return value if isinstance(value, list) else (default or [])

    def get_dict(self, key: str, default: Optional[Dict] = None) -> Dict:
        value = self.get(key, default or {})
        return value if isinstance(value, dict) else (default or {})

    def batch_set(self, configs: Dict[str, Any], validate: bool = True) -> List[ConfigValidationError]:
        errors = []
        with self._lock:
            for key, value in configs.items():
                error = self.set(key, value, validate)
                if error:
                    errors.append(error)
        return errors

    def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        with self._lock:
            return {key: self._configs.get(key) for key in keys}

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._configs:
                old_value = self._configs.pop(key)
                event = ConfigChangeEvent(key, old_value, None)
                self._notify_listeners(event)
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._configs.clear()

    def register_environment(self, env: EnvironmentConfig) -> None:
        with self._lock:
            self._environments[env.name] = env

    def switch_environment(self, name: str) -> bool:
        with self._lock:
            if name not in self._environments:
                return False
            
            env = self._environments[name]
            
            if env.parent and env.parent in self._environments:
                parent_env = self._environments[env.parent]
                self._configs.update(parent_env.configs.copy())
            
            self._configs.update(env.configs.copy())
            self._current_environment = name
            return True

    def get_current_environment(self) -> Optional[str]:
        return self._current_environment

    def list_environments(self) -> List[str]:
        return list(self._environments.keys())

    def add_listener(self, listener: ConfigChangeListener) -> None:
        with self._lock:
            self._listeners.append(listener)

    def remove_listener(self, listener: ConfigChangeListener) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def _notify_listeners(self, event: ConfigChangeEvent) -> None:
        for listener in self._listeners:
            try:
                listener.on_config_change(event)
            except Exception:
                pass

    def load_from_dict(self, data: Dict[str, Any], validate: bool = True) -> List[ConfigValidationError]:
        return self.batch_set(data, validate)

    def load_from_json(self, json_str: str, validate: bool = True) -> List[ConfigValidationError]:
        try:
            data = json.loads(json_str)
            return self.load_from_dict(data, validate)
        except json.JSONDecodeError as e:
            return [ConfigValidationError("", f"JSON parse error: {str(e)}")]

    def load_from_file(self, file_path: str, validate: bool = True) -> List[ConfigValidationError]:
        path = Path(file_path)
        if not path.exists():
            return [ConfigValidationError("", f"File not found: {file_path}")]
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix == '.json':
                    data = json.load(f)
                else:
                    return [ConfigValidationError("", f"Unsupported file format: {path.suffix}")]
            
            return self.load_from_dict(data, validate)
        except Exception as e:
            return [ConfigValidationError("", f"Load error: {str(e)}")]

    def save_to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return self._configs.copy()

    def save_to_json(self, indent: int = 2) -> str:
        return json.dumps(self.save_to_dict(), indent=indent, ensure_ascii=False)

    def save_to_file(self, file_path: str, indent: int = 2) -> bool:
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                if path.suffix == '.json':
                    json.dump(self.save_to_dict(), f, indent=indent, ensure_ascii=False)
                else:
                    return False
            return True
        except Exception:
            return False

    def get_all_configs(self) -> Dict[str, Any]:
        with self._lock:
            return self._configs.copy()

    def get_all_config_items(self) -> List[ConfigItem]:
        with self._lock:
            return list(self._config_items.values())

    def validate_all(self) -> List[ConfigValidationError]:
        errors = []
        with self._lock:
            for key, item in self._config_items.items():
                value = self._configs.get(key)
                error = self.validate_config(key, value)
                if error:
                    errors.append(error)
        return errors

    def has(self, key: str) -> bool:
        return key in self._configs

    def keys(self) -> Set[str]:
        with self._lock:
            return set(self._configs.keys())

    def __contains__(self, key: str) -> bool:
        return self.has(key)

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)


_global_config_manager: Optional[ConfigManager] = None
_global_lock = threading.Lock()


def get_config_manager() -> ConfigManager:
    global _global_config_manager
    with _global_lock:
        if _global_config_manager is None:
            _global_config_manager = ConfigManager()
        return _global_config_manager


def set_config_manager(manager: ConfigManager) -> None:
    global _global_config_manager
    with _global_lock:
        _global_config_manager = manager


def register_config_item(item: ConfigItem) -> None:
    get_config_manager().register_config_item(item)


def register_config_items(items: List[ConfigItem]) -> None:
    get_config_manager().register_config_items(items)


def get(key: str, default: Any = None) -> Any:
    return get_config_manager().get(key, default)


def set(key: str, value: Any, validate: bool = True) -> Optional[ConfigValidationError]:
    return get_config_manager().set(key, value, validate)


def get_int(key: str, default: int = 0) -> int:
    return get_config_manager().get_int(key, default)


def get_float(key: str, default: float = 0.0) -> float:
    return get_config_manager().get_float(key, default)


def get_bool(key: str, default: bool = False) -> bool:
    return get_config_manager().get_bool(key, default)


def get_list(key: str, default: Optional[List] = None) -> List:
    return get_config_manager().get_list(key, default)


def get_dict(key: str, default: Optional[Dict] = None) -> Dict:
    return get_config_manager().get_dict(key, default)


def switch_environment(name: str) -> bool:
    return get_config_manager().switch_environment(name)


def load_from_file(file_path: str, validate: bool = True) -> List[ConfigValidationError]:
    return get_config_manager().load_from_file(file_path, validate)


def save_to_file(file_path: str, indent: int = 2) -> bool:
    return get_config_manager().save_to_file(file_path, indent)


def add_listener(listener: ConfigChangeListener) -> None:
    get_config_manager().add_listener(listener)


def remove_listener(listener: ConfigChangeListener) -> None:
    get_config_manager().remove_listener(listener)


def validate_all() -> List[ConfigValidationError]:
    return get_config_manager().validate_all()

import time
