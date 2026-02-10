"""
配置项检测器

检测应用程序必需的配置文件、环境变量、密钥等是否正确设置。
"""

import os
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base.base_adapter import BaseAdapter, HealthResult, Issue, IssueType, FixResult


class ConfigIssueType(Enum):
    """配置问题类型"""
    MISSING_ENV_VAR = auto()       # 缺失环境变量
    MISSING_CONFIG_KEY = auto()    # 缺失配置项
    INVALID_CONFIG_VALUE = auto()  # 配置值无效
    MISSING_FILE = auto()          # 缺失文件
    LICENSE_EXPIRED = auto()       # 许可证过期
    API_KEY_INVALID = auto()       # API 密钥无效


@dataclass
class ConfigRequirement:
    """配置项要求"""
    name: str                      # 配置项名称
    required: bool = True         # 是否必需
    env_names: List[str] = field(default_factory=list)    # 可能的环境变量名
    config_paths: List[str] = field(default_factory=list)  # 可能的配置文件路径
    default_value: str = ""        # 默认值
    validation_pattern: str = ""   # 验证正则
    validation_type: str = "string"  # 验证类型: string, email, url, path, license
    description: str = ""         # 描述
    hint: str = ""                # 提示信息


@dataclass
class ConfigCheckResult:
    """配置检查结果"""
    requirement: ConfigRequirement
    found: bool
    found_value: Optional[str] = None
    source: Optional[str] = None  # 找到的位置: env, config, default
    valid: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.requirement.name,
            "required": self.requirement.required,
            "found": self.found,
            "found_value": self.found_value,
            "source": self.source,
            "valid": self.valid,
            "error_message": self.error_message
        }


class ConfigurationDetector:
    """配置检测器"""

    def __init__(self):
        self.requirements: List[ConfigRequirement] = []
        self.load_default_requirements()

    def load_default_requirements(self):
        """加载默认配置要求"""
        # 通用配置要求
        self.requirements = [
            # 应用基础配置
            ConfigRequirement(
                name="APP_ENV",
                required=True,
                env_names=["APP_ENV", "NODE_ENV", "ENVIRONMENT"],
                default_value="development",
                validation_type="string",
                description="应用运行环境"
            ),
            ConfigRequirement(
                name="DEBUG_MODE",
                required=False,
                env_names=["DEBUG", "DEBUG_MODE", "LOG_LEVEL"],
                default_value="false",
                validation_type="string",
                description="调试模式开关"
            ),
            # API 密钥配置
            ConfigRequirement(
                name="DATA_API_KEY",
                required=True,
                env_names=["DATA_API_KEY", "DATA_KEY", "API_DATA_KEY"],
                validation_pattern=r"^[a-zA-Z0-9]{16,}$",
                validation_type="string",
                description="数据 API 密钥",
                hint="请从服务商处获取数据 API 密钥"
            ),
            ConfigRequirement(
                name="IMAGE_API_KEY",
                required=True,
                env_names=["IMAGE_API_KEY", "IMAGE_KEY", "API_IMAGE_KEY"],
                validation_pattern=r"^[a-zA-Z0-9]{16,}$",
                validation_type="string",
                description="图片 API 密钥",
                hint="请从服务商处获取图片 API 密钥"
            ),
            ConfigRequirement(
                name="API_SECRET",
                required=True,
                env_names=["API_SECRET", "API_SECRET_KEY", "SECRET_KEY"],
                validation_pattern=r"^[a-zA-Z0-9_\-]{16,}$",
                validation_type="string",
                description="API 密钥"
            ),
            # 数据库配置
            ConfigRequirement(
                name="DATABASE_URL",
                required=True,
                env_names=["DATABASE_URL", "DB_URL", "MONGODB_URI"],
                validation_pattern=r"^(mongodb|postgresql|mysql)://",
                validation_type="string",
                description="数据库连接字符串"
            ),
            ConfigRequirement(
                name="DATABASE_HOST",
                required=False,
                env_names=["DB_HOST", "DATABASE_HOST"],
                default_value="localhost",
                validation_type="string",
                description="数据库主机"
            ),
            ConfigRequirement(
                name="DATABASE_PORT",
                required=False,
                env_names=["DB_PORT", "DATABASE_PORT"],
                default_value="27017",
                validation_type="string",
                description="数据库端口"
            ),
            # Redis 配置
            ConfigRequirement(
                name="REDIS_URL",
                required=False,
                env_names=["REDIS_URL", "REDIS_HOST"],
                validation_pattern=r"^redis://",
                validation_type="string",
                description="Redis 连接字符串"
            ),
            # JWT 配置
            ConfigRequirement(
                name="JWT_SECRET",
                required=True,
                env_names=["JWT_SECRET", "JWT_SECRET_KEY"],
                validation_pattern=r"^[a-zA-Z0-9_\-]{32,}$",
                validation_type="string",
                description="JWT 密钥"
            ),
            ConfigRequirement(
                name="JWT_EXPIRES_IN",
                required=False,
                env_names=["JWT_EXPIRES_IN", "JWT_EXPIRE"],
                default_value="7d",
                validation_type="string",
                description="JWT 过期时间"
            ),
            # 许可配置
            ConfigRequirement(
                name="LICENSE_KEY",
                required=True,
                env_names=["LICENSE_KEY", "LICENSE", "PRODUCT_KEY"],
                validation_pattern=r"^[A-Z0-9]{8,}-[A-Z0-9]{4,}-[A-Z0-9]{4,}$",
                validation_type="license",
                description="软件许可证密钥"
            ),
            # 服务端点
            ConfigRequirement(
                name="API_BASE_URL",
                required=True,
                env_names=["API_BASE_URL", "API_URL", "BASE_URL"],
                validation_pattern=r"^https?://",
                validation_type="url",
                description="API 基础地址"
            ),
            ConfigRequirement(
                name="UPLOAD_URL",
                required=False,
                env_names=["UPLOAD_URL", "UPLOAD_ENDPOINT"],
                validation_pattern=r"^https?://",
                validation_type="url",
                description="上传服务地址"
            ),
        ]

    def add_requirement(self, requirement: ConfigRequirement):
        """添加配置要求"""
        self.requirements.append(requirement)

    def remove_requirement(self, name: str):
        """移除配置要求"""
        self.requirements = [r for r in self.requirements if r.name != name]

    def from_template(self, template: Dict[str, Any]):
        """从模板加载配置要求"""
        for name, config in template.items():
            if isinstance(config, dict):
                self.requirements.append(ConfigRequirement(
                    name=name,
                    **config
                ))

    async def check_all(self, config_paths: Optional[List[str]] = None) -> List[ConfigCheckResult]:
        """检查所有配置项"""
        results = []

        for requirement in self.requirements:
            result = await self.check_requirement(requirement, config_paths)
            results.append(result)

        return results

    async def check_requirement(
        self,
        requirement: ConfigRequirement,
        config_paths: Optional[List[str]] = None
    ) -> ConfigCheckResult:
        """检查单个配置项"""
        result = ConfigCheckResult(requirement=requirement, found=False)

        # 1. 优先从环境变量查找
        for env_name in requirement.env_names:
            value = os.environ.get(env_name)
            if value:
                result.found = True
                result.found_value = value
                result.source = f"env:{env_name}"
                result.valid = self._validate_value(value, requirement)
                if not result.valid:
                    result.error_message = f"环境变量 {env_name} 的值验证失败"
                return result

        # 2. 从配置文件查找
        if config_paths:
            for config_path in config_paths:
                value = self._search_in_config_file(config_path, requirement)
                if value is not None:
                    result.found = True
                    result.found_value = value
                    result.source = f"config:{config_path}"
                    result.valid = self._validate_value(value, requirement)
                    if not result.valid:
                        result.error_message = f"配置文件中的 {requirement.name} 值验证失败"
                    return result

        # 3. 检查是否有默认值
        if requirement.default_value and not requirement.required:
            result.found = True
            result.found_value = requirement.default_value
            result.source = "default"
            result.valid = self._validate_value(requirement.default_value, requirement)

        return result

    def _search_in_config_file(self, config_path: str, requirement: ConfigRequirement) -> Optional[str]:
        """在配置文件中搜索配置项"""
        if not Path(config_path).exists():
            return None

        try:
            # 尝试解析不同格式的配置文件
            if config_path.endswith('.env'):
                return self._parse_env_file(config_path, requirement)
            elif config_path.endswith(('.yaml', '.yml')):
                return self._parse_yaml_file(config_path, requirement)
            elif config_path.endswith('.json'):
                return self._parse_json_file(config_path, requirement)
            elif config_path.endswith('.ini'):
                return self._parse_ini_file(config_path, requirement)
        except Exception:
            pass

        return None

    def _parse_env_file(self, config_path: str, requirement: ConfigRequirement) -> Optional[str]:
        """解析 .env 文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        # 检查所有可能的名称变体
                        if key.upper() in [n.upper() for n in requirement.env_names]:
                            return value
        except Exception:
            pass
        return None

    def _parse_yaml_file(self, config_path: str, requirement: ConfigRequirement) -> Optional[str]:
        """解析 YAML 文件"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config:
                    # 检查所有可能的名称变体
                    for env_name in requirement.env_names:
                        keys = env_name.lower().split('_')
                        value = config
                        for k in keys:
                            if isinstance(value, dict) and k in value:
                                value = value[k]
                            else:
                                value = None
                                break
                        if value is not None:
                            return str(value)
        except Exception:
            pass
        return None

    def _parse_json_file(self, config_path: str, requirement: ConfigRequirement) -> Optional[str]:
        """解析 JSON 文件"""
        try:
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if config:
                    for env_name in requirement.env_names:
                        keys = env_name.lower().split('_')
                        value = config
                        for k in keys:
                            if isinstance(value, dict) and k in value:
                                value = value[k]
                            else:
                                value = None
                                break
                        if value is not None:
                            return str(value)
        except Exception:
            pass
        return None

    def _parse_ini_file(self, config_path: str, requirement: ConfigRequirement) -> Optional[str]:
        """解析 INI 文件"""
        try:
            configparser = __import__('configparser')
            parser = configparser.ConfigParser()
            parser.read(config_path)
            for env_name in requirement.env_names:
                if parser.has_option('DEFAULT', env_name):
                    return parser.get('DEFAULT', env_name)
                # 检查各个 section
                for section in parser.sections():
                    if parser.has_option(section, env_name):
                        return parser.get(section, env_name)
        except Exception:
            pass
        return None

    def _validate_value(self, value: str, requirement: ConfigRequirement) -> bool:
        """验证配置值"""
        if not value:
            return False

        if requirement.validation_pattern:
            return bool(re.match(requirement.validation_pattern, value))

        return True

    def get_missing_configs(self, results: List[ConfigCheckResult]) -> List[ConfigCheckResult]:
        """获取缺失的必要配置"""
        return [r for r in results if r.requirement.required and not r.found]

    def get_invalid_configs(self, results: List[ConfigCheckResult]) -> List[ConfigCheckResult]:
        """获取无效的配置"""
        return [r for r in results if r.found and not r.valid]

    def generate_issues(self, results: List[ConfigCheckResult]) -> List[Issue]:
        """从检查结果生成问题列表"""
        issues = []

        for result in results:
            if result.requirement.required and not result.found:
                # 必需配置缺失
                issue = Issue(
                    service_name="configuration",
                    issue_type=IssueType.CONFIG_INVALID,
                    title=f"必需配置缺失: {result.requirement.name}",
                    description=f"应用程序必需的配置文件 {result.requirement.name} 未设置。{result.requirement.description}",
                    severity="critical",
                    detection_method="config_check",
                    suggestion=result.requirement.hint or f"请设置环境变量 {', '.join(result.requirement.env_names)} 或在配置文件中添加",
                    affected_component=result.requirement.name,
                    raw_data={
                        "config_name": result.requirement.name,
                        "expected_in_env": result.requirement.env_names,
                        "expected_in_config": result.requirement.config_paths,
                        "validation_type": result.requirement.validation_type
                    }
                )
                issues.append(issue)

            elif result.found and not result.valid:
                # 配置值无效
                issue = Issue(
                    service_name="configuration",
                    issue_type=IssueType.CONFIG_INVALID,
                    title=f"配置值无效: {result.requirement.name}",
                    description=f"配置项 {result.requirement.name} 的值格式不正确",
                    severity="high",
                    detection_method="config_validation",
                    suggestion=f"请检查 {result.requirement.name} 的值是否符合要求",
                    affected_component=result.requirement.name,
                    raw_data={
                        "config_name": result.requirement.name,
                        "found_value": result.found_value,
                        "source": result.source,
                        "validation_pattern": result.requirement.validation_pattern
                    }
                )
                issues.append(issue)

        return issues

    def export_template(self, format: str = "json") -> str:
        """导出配置要求模板"""
        data = {
            "config_requirements": [
                {
                    "name": r.name,
                    "required": r.required,
                    "env_names": r.env_names,
                    "config_paths": r.config_paths,
                    "default_value": r.default_value,
                    "validation_pattern": r.validation_pattern,
                    "validation_type": r.validation_type,
                    "description": r.description,
                    "hint": r.hint
                }
                for r in self.requirements
            ]
        }

        if format == "json":
            import json
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format == "yaml":
            import yaml
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        else:
            return str(data)
