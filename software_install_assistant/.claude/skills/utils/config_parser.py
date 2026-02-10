"""
配置文件解析

支持多种配置文件格式的解析和生成。
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ConfigParser:
    """配置文件解析器"""

    # 格式到文件扩展名的映射
    FORMAT_EXTENSIONS = {
        "yaml": [".yaml", ".yml"],
        "json": [".json"],
        "ini": [".ini", ".conf", ".cfg"],
        "env": [".env"],
        "properties": [".properties", ".props"]
    }

    def __init__(self):
        pass

    def parse(self, config_path: str) -> Dict[str, Any]:
        """解析配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            解析后的配置字典
        """
        path = Path(config_path)

        # 检测格式
        format_type = self._detect_format(path)
        if format_type is None:
            # 尝试读取内容自动检测
            content = self._read_file(config_path)
            if content:
                return self._parse_by_content(content)
            return {}

        return self._parse_by_format(config_path, format_type)

    def _detect_format(self, path: Path) -> Optional[str]:
        """检测配置文件格式"""
        suffix = path.suffix.lower()

        for format_type, extensions in self.FORMAT_EXTENSIONS.items():
            if suffix in extensions:
                return format_type

        return None

    def _read_file(self, config_path: str) -> Optional[str]:
        """读取文件内容"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None

    def _parse_by_content(self, content: str) -> Dict[str, Any]:
        """根据内容检测并解析"""
        content = content.strip()

        # 检测 JSON
        if content.startswith('{') or content.startswith('['):
            try:
                return json.loads(content)
            except Exception:
                pass

        # 检测 YAML（通过特征）
        if ': ' in content or content.startswith('- '):
            try:
                import yaml
                return yaml.safe_load(content) or {}
            except ImportError:
                pass

        # 默认使用 KV 解析
        return self._parse_kv(content)

    def _parse_by_format(self, config_path: str, format_type: str) -> Dict[str, Any]:
        """根据格式解析"""
        content = self._read_file(config_path)
        if not content:
            return {}

        if format_type == "yaml":
            return self._parse_yaml(content)
        elif format_type == "json":
            return self._parse_json(content)
        elif format_type == "ini":
            return self._parse_ini(content)
        elif format_type in ["env", "properties"]:
            return self._parse_kv(content)

        return {}

    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        """解析 YAML"""
        try:
            import yaml
            return yaml.safe_load(content) or {}
        except ImportError:
            # 简单处理
            return self._parse_kv(content)
        except Exception:
            return {}

    def _parse_json(self, content: str) -> Dict[str, Any]:
        """解析 JSON"""
        try:
            return json.loads(content)
        except Exception:
            return {}

    def _parse_ini(self, content: str) -> Dict[str, Dict[str, str]]:
        """解析 INI 格式"""
        config = {}
        current_section = "default"

        for line in content.splitlines():
            line = line.strip()

            # 跳过注释和空行
            if not line or line.startswith('#') or line.startswith(';'):
                continue

            # 检查是否是 section
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].strip()
                config[current_section] = {}
                continue

            # 解析 key-value
            if '=' in line:
                key, value = line.split('=', 1)
                if current_section not in config:
                    config[current_section] = {}
                config[current_section][key.strip()] = value.strip()

        return config

    def _parse_kv(self, content: str) -> Dict[str, str]:
        """解析 KEY=VALUE 格式"""
        config = {}

        for line in content.splitlines():
            line = line.strip()

            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue

            # 解析 KEY=VALUE 格式
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                config[key] = value

        return config

    def generate(self, config_data: Dict[str, Any], format_type: str = "yaml") -> str:
        """生成配置文件内容

        Args:
            config_data: 配置数据
            format_type: 输出格式 (yaml, json, ini, env)

        Returns:
            配置文件内容字符串
        """
        if format_type == "yaml":
            return self._generate_yaml(config_data)
        elif format_type == "json":
            return self._generate_json(config_data)
        elif format_type == "ini":
            return self._generate_ini(config_data)
        elif format_type == "env":
            return self._generate_env(config_data)

        return ""

    def _generate_yaml(self, data: Dict[str, Any]) -> str:
        """生成 YAML"""
        try:
            import yaml
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        except ImportError:
            # 简单处理
            return self._generate_env(data)

    def _generate_json(self, data: Dict[str, Any]) -> str:
        """生成 JSON"""
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _generate_ini(self, data: Dict[str, Any]) -> str:
        """生成 INI"""
        lines = []

        for section, values in data.items():
            if isinstance(values, dict):
                lines.append(f"[{section}]")
                for key, value in values.items():
                    lines.append(f"{key}={value}")
            else:
                lines.append(f"{section}={values}")

        return '\n'.join(lines)

    def _generate_env(self, data: Dict[str, Any]) -> str:
        """生成 env 格式"""
        lines = []

        def flatten_dict(d: Dict[str, Any], prefix: str = ""):
            items = []
            for key, value in d.items():
                new_key = f"{prefix}_{key}".upper() if prefix else key.upper()
                if isinstance(value, dict):
                    items.extend(flatten_dict(value, new_key))
                else:
                    items.append((new_key, str(value)))
            return items

        lines = [f"{k}={v}" for k, v in flatten_dict(data)]
        return '\n'.join(lines)

    def merge_configs(
        self,
        base_config: Dict[str, Any],
        override_config: Dict[str, Any],
        deep_merge: bool = True
    ) -> Dict[str, Any]:
        """合并配置

        Args:
            base_config: 基础配置
            override_config: 覆盖配置
            deep_merge: 是否深度合并

        Returns:
            合并后的配置
        """
        if not deep_merge:
            base_config.update(override_config)
            return base_config

        # 深度合并
        result = base_config.copy()
        self._deep_merge(result, override_config)
        return result

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """深度合并辅助函数"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get_value(
        self,
        config: Dict[str, Any],
        key: str,
        default: Any = None,
        key_separator: str = "."
    ) -> Any:
        """获取嵌套配置值

        Args:
            config: 配置字典
            key: 键路径（如 "database.host"）
            default: 默认值
            key_separator: 键分隔符

        Returns:
            配置值
        """
        keys = key.split(key_separator)
        value = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set_value(
        self,
        config: Dict[str, Any],
        key: str,
        value: Any,
        key_separator: str = "."
    ) -> None:
        """设置嵌套配置值

        Args:
            config: 配置字典
            key: 键路径（如 "database.host"）
            value: 要设置的值
            key_separator: 键分隔符
        """
        keys = key.split(key_separator)
        current = config

        for i, k in enumerate(keys[:-1]):
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value
