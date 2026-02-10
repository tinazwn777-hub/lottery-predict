"""
配置检测器

解析和检测各种配置文件的问题。
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..base.base_adapter import Issue, IssueType


class ConfigDetector:
    """配置检测器"""

    # 支持的配置文件格式
    SUPPORTED_FORMATS = ["ini", "yaml", "json", "env", "properties"]

    def __init__(self):
        pass

    def parse_config(self, config_path: str) -> Dict[str, Any]:
        """解析配置文件"""
        content = self._read_file(config_path)
        if not content:
            return {}

        ext = Path(config_path).suffix.lower()

        if ext in [".yml", ".yaml"]:
            return self._parse_yaml(content)
        elif ext == ".json":
            return self._parse_json(content)
        elif ext in [".env", ".properties", ".conf"]:
            return self._parse_key_value(content)
        elif ext == ".ini":
            return self._parse_ini(content)
        else:
            # 尝试自动检测
            return self._detect_and_parse(content)

    def _read_file(self, config_path: str) -> Optional[str]:
        """读取文件内容"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None

    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        """解析 YAML 配置"""
        try:
            import yaml
            return yaml.safe_load(content) or {}
        except ImportError:
            # 如果没有 pyyaml，使用简单解析
            return self._parse_key_value(content)
        except Exception:
            return {}

    def _parse_json(self, content: str) -> Dict[str, Any]:
        """解析 JSON 配置"""
        try:
            return json.loads(content)
        except Exception:
            return {}

    def _parse_key_value(self, content: str) -> Dict[str, Any]:
        """解析 KEY=VALUE 格式配置"""
        config = {}

        for line in content.splitlines():
            line = line.strip()

            # 跳过注释和空行
            if not line or line.startswith('#') or line.startswith(';'):
                continue

            # 解析 KEY=VALUE 格式
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # 处理带引号的值
                value = value.strip('"\'')
                value = value.strip()

                config[key] = value

        return config

    def _parse_ini(self, content: str) -> Dict[str, Dict[str, str]]:
        """解析 INI 格式配置"""
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

    def _detect_and_parse(self, content: str) -> Dict[str, Any]:
        """自动检测并解析配置"""
        # 检测格式
        content_stripped = content.strip()

        if content_stripped.startswith('{'):
            return self._parse_json(content)
        elif content_stripped.startswith('['):
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    return {"root": data}
                return data
            except Exception:
                pass

        # 尝试 YAML
        if ': ' in content or content_stripped.startswith('- '):
            result = self._parse_yaml(content)
            if result:
                return result

        # 默认使用 KV 解析
        return self._parse_key_value(content)

    def detect_config_issues(
        self,
        config_path: str,
        rules: Optional[List[Dict[str, Any]]] = None
    ) -> List[Issue]:
        """检测配置文件中的问题"""
        issues = []

        config = self.parse_config(config_path)
        if not config:
            return issues

        # 应用默认规则
        if rules is None:
            rules = self._get_default_rules()

        for rule in rules:
            issue = self._check_rule(config, rule, config_path)
            if issue:
                issues.append(issue)

        return issues

    def _get_default_rules(self) -> List[Dict[str, Any]]:
        """获取默认检测规则"""
        return [
            {
                "name": "bind_address",
                "keys": ["bind", "bind-address", "network.bind_host"],
                "severity": "medium",
                "check": lambda v: v in ["0.0.0.0", "*"] or "0.0.0.0" in str(v),
                "message": "服务绑定到所有网络接口，可能存在安全风险",
                "suggestion": "建议绑定到 localhost 或配置防火墙规则"
            },
            {
                "name": "no_password",
                "keys": ["requirepass", "password", "passwd", "auth"],
                "severity": "medium",
                "check": lambda v: not v,
                "message": "未配置访问密码，可能存在安全风险",
                "suggestion": "建议配置强密码或启用认证"
            },
            {
                "name": "debug_mode",
                "keys": ["debug", "logging.level"],
                "severity": "low",
                "check": lambda v: str(v).lower() in ["true", "debug", "verbose"],
                "message": "调试模式已启用，可能泄露敏感信息",
                "suggestion": "生产环境建议关闭调试模式"
            }
        ]

    def _check_rule(
        self,
        config: Dict[str, Any],
        rule: Dict[str, Any],
        config_path: str
    ) -> Optional[Issue]:
        """检查单个规则"""
        keys = rule.get("keys", [])
        check_func = rule.get("check", lambda x: False)
        message = rule.get("message", "")
        suggestion = rule.get("suggestion", "")
        severity = rule.get("severity", "medium")

        for key in keys:
            value = self._get_nested_value(config, key)
            if value is not None and check_func(value):
                return Issue(
                    service_name="config",
                    issue_type=IssueType.CONFIG_INVALID,
                    title=rule.get("name", "配置问题").replace("_", " ").title(),
                    description=message,
                    severity=severity,
                    detection_method="config_check",
                    suggestion=suggestion,
                    affected_component=key,
                    raw_data={"config_path": config_path, "key": key, "value": value}
                )

        return None

    def _get_nested_value(self, config: Dict[str, Any], key: str) -> Any:
        """获取嵌套配置值，支持点号分隔的路径"""
        keys = key.split(".")
        value = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None

        return value

    def check_syntax_errors(self, config_path: str) -> List[Issue]:
        """检查配置文件语法错误"""
        issues = []

        content = self._read_file(config_path)
        if not content:
            issues.append(Issue(
                service_name="config",
                issue_type=IssueType.CONFIG_INVALID,
                title="配置文件无法读取",
                description=f"无法读取配置文件: {config_path}",
                severity="high",
                detection_method="file_check",
                suggestion="检查文件权限和路径是否正确"
            ))
            return issues

        ext = Path(config_path).suffix.lower()

        # 验证特定格式的语法
        if ext in [".yml", ".yaml"]:
            syntax_issues = self._check_yaml_syntax(content, config_path)
        elif ext == ".json":
            syntax_issues = self._check_json_syntax(content, config_path)
        else:
            syntax_issues = []

        issues.extend(syntax_issues)
        return issues

    def _check_yaml_syntax(self, content: str, config_path: str) -> List[Issue]:
        """检查 YAML 语法"""
        issues = []

        try:
            import yaml
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            issues.append(Issue(
                service_name="config",
                issue_type=IssueType.CONFIG_INVALID,
                title="YAML 语法错误",
                description=f"YAML 配置文件存在语法错误: {str(e)}",
                severity="high",
                detection_method="syntax_check",
                suggestion="检查 YAML 缩进和格式",
                affected_component=config_path
            ))

        return issues

    def _check_json_syntax(self, content: str, config_path: str) -> List[Issue]:
        """检查 JSON 语法"""
        issues = []

        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            issues.append(Issue(
                service_name="config",
                issue_type=IssueType.CONFIG_INVALID,
                title="JSON 语法错误",
                description=f"JSON 配置文件存在语法错误: {str(e)}",
                severity="high",
                detection_method="syntax_check",
                suggestion="检查 JSON 语法，确保逗号、引号等正确",
                affected_component=config_path
            ))

        return issues
