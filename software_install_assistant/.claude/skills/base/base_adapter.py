"""
基础适配器类定义

所有服务适配器的基类，提供通用的接口和方法。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class IssueType(Enum):
    """问题类型枚举"""
    SERVICE_NOT_RUNNING = auto()       # 服务未运行
    PORT_NOT_LISTENING = auto()        # 端口未监听
    PORT_CONFLICT = auto()             # 端口冲突
    CONFIG_INVALID = auto()            # 配置无效
    CONNECTIVITY_FAILED = auto()        # 连接失败
    DEPENDENCY_MISSING = auto()        # 依赖缺失
    PERMISSION_DENIED = auto()         # 权限不足
    STORAGE_FULL = auto()              # 存储空间不足
    UNKNOWN = auto()                   # 未知问题


@dataclass
class HealthResult:
    """健康检查结果"""
    service_name: str
    is_healthy: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "is_healthy": self.is_healthy,
            "message": self.message,
            "details": self.details
        }


@dataclass
class Issue:
    """问题描述"""
    service_name: str
    issue_type: IssueType
    title: str
    description: str
    severity: str = "medium"  # low, medium, high, critical
    detection_method: str = ""
    suggestion: str = ""
    affected_component: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "issue_type": self.issue_type.name,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "detection_method": self.detection_method,
            "suggestion": self.suggestion,
            "affected_component": self.affected_component,
            "raw_data": self.raw_data
        }


@dataclass
class FixResult:
    """修复操作结果"""
    success: bool
    message: str
    error: Optional[str] = None
    changes: List[str] = field(default_factory=list)
    requires_restart: bool = False
    verification_output: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "error": self.error,
            "changes": self.changes,
            "requires_restart": self.requires_restart,
            "verification_output": self.verification_output
        }


class BaseAdapter(ABC):
    """所有服务适配器的基类"""

    # 子类应该覆盖这些属性
    SERVICE_NAME = "base"
    DEFAULT_PORTS: List[int] = []

    def __init__(self):
        self.system = self._detect_system()

    def _detect_system(self) -> str:
        """检测当前操作系统"""
        import platform
        return platform.system()

    @property
    def is_windows(self) -> bool:
        return self.system == "Windows"

    @property
    def is_linux(self) -> bool:
        return self.system == "Linux"

    @property
    def is_macos(self) -> bool:
        return self.system == "Darwin"

    @abstractmethod
    async def health_check(self, sub_service: Optional[str] = None) -> HealthResult:
        """执行健康检查"""
        pass

    @abstractmethod
    async def detect_issues(self) -> List[Issue]:
        """检测问题"""
        pass

    @abstractmethod
    async def fix(self, issue: Issue, force: bool = False) -> FixResult:
        """修复问题"""
        pass

    def get_required_ports(self) -> List[int]:
        """获取需要检查的端口"""
        return self.DEFAULT_PORTS

    def get_config_paths(self) -> List[str]:
        """获取配置文件路径"""
        return []

    def get_sub_services(self) -> Dict[str, str]:
        """获取子服务映射（用于数据库等支持多种类型的服务）"""
        return {}

    async def verify_fix(self, issue: Issue) -> bool:
        """验证修复是否成功"""
        result = await self.health_check()
        return result.is_healthy

    def _run_command(self, cmd: str, capture_output: bool = True) -> tuple:
        """执行命令的封装（同步版本，子类可覆盖）"""
        import subprocess
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    async def _run_command_async(self, cmd: str, capture_output: bool = True) -> tuple:
        """执行命令的封装（异步版本）"""
        import asyncio
        import subprocess

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE if capture_output else asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE if capture_output else asyncio.subprocess.DEVNULL
            )
            stdout, stderr = await proc.communicate()
            return proc.returncode, stdout.decode(), stderr.decode()
        except Exception as e:
            return -1, "", str(e)
