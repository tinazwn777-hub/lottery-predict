"""
数据库适配器

支持 MySQL、PostgreSQL、MongoDB 的健康检查和问题检测。
"""

import asyncio
import json
import platform
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base.base_adapter import BaseAdapter, HealthResult, Issue, IssueType, FixResult
from ..base.health_checker import HealthChecker


class DatabaseAdapter(BaseAdapter):
    """数据库适配器 - 支持 MySQL, PostgreSQL, MongoDB"""

    SERVICE_NAME = "database"

    # 各数据库的默认端口
    DEFAULT_PORTS = {
        "mysql": 3306,
        "postgres": 5432,
        "mongodb": 27017
    }

    # 各数据库的服务名称
    SERVICE_NAMES = {
        "mysql": ["mysql", "mysqld", "mariadb"],
        "postgres": ["postgres", "postgresql", "pg_ctl"],
        "mongodb": ["mongod", "mongodb"]
    }

    # 配置文件路径
    CONFIG_PATHS = {
        "mysql": [
            "/etc/my.cnf",
            "/etc/mysql/my.cnf",
            "/etc/my.cnf.d/",
            "C:\\ProgramData\\MySQL\\MySQL Server*\\my.ini"
        ],
        "postgres": [
            "/etc/postgresql/*/main/postgresql.conf",
            "/var/lib/pgsql/data/postgresql.conf",
            "C:\\Program Files\\PostgreSQL\\*\\data\\postgresql.conf"
        ],
        "mongodb": [
            "/etc/mongod.conf",
            "/etc/mongodb.conf",
            "C:\\Program Files\\MongoDB\\Server*\\bin\\mongod.cfg"
        ]
    }

    def __init__(self):
        super().__init__()
        self.databases = {
            "mysql": self._check_mysql,
            "postgres": self._check_postgres,
            "mongodb": self._check_mongodb
        }

    def get_sub_services(self) -> Dict[str, str]:
        return {
            "mysql": "MySQL 数据库",
            "postgres": "PostgreSQL 数据库",
            "mongodb": "MongoDB 数据库"
        }

    def get_config_paths(self, db_type: str) -> List[str]:
        return self.CONFIG_PATHS.get(db_type, [])

    async def health_check(self, sub_service: Optional[str] = None) -> HealthResult:
        """执行数据库健康检查"""
        if sub_service:
            checker = self.databases.get(sub_service.lower())
            if checker:
                return await checker()
            return HealthResult(
                service_name=sub_service,
                is_healthy=False,
                message=f"未知的数据库类型: {sub_service}"
            )

        # 检查所有数据库
        results = {}
        all_healthy = True

        for name, checker in self.databases.items():
            result = await checker()
            results[name] = result.to_dict()
            if not result.is_healthy:
                all_healthy = False

        if all_healthy:
            return HealthResult(
                service_name=self.SERVICE_NAME,
                is_healthy=True,
                message="所有数据库服务运行正常",
                details=results
            )
        else:
            return HealthResult(
                service_name=self.SERVICE_NAME,
                is_healthy=False,
                message="部分数据库服务存在异常",
                details=results
            )

    async def _check_mysql(self) -> HealthResult:
        """检查 MySQL 健康状态"""
        service_names = self.SERVICE_NAMES["mysql"]
        default_port = self.DEFAULT_PORTS["mysql"]

        # 1. 检查进程
        process = await HealthChecker.check_process_running(service_names)
        if not process:
            return HealthResult(
                service_name="mysql",
                is_healthy=False,
                message="MySQL 服务未运行",
                details={"port": default_port}
            )

        # 2. 检查端口
        port_open = await HealthChecker.check_port_listening("127.0.0.1", default_port)
        if not port_open:
            return HealthResult(
                service_name="mysql",
                is_healthy=False,
                message=f"MySQL 端口 ({default_port}) 未监听",
                details={"port": default_port, "process": process}
            )

        # 3. 尝试连接测试
        connected = await self._test_mysql_connection(default_port)
        if not connected:
            return HealthResult(
                service_name="mysql",
                is_healthy=False,
                message="MySQL 连接失败",
                details={"port": default_port, "process": process}
            )

        return HealthResult(
            service_name="mysql",
            is_healthy=True,
            message="MySQL 服务运行正常",
            details={"port": default_port, "process": process}
        )

    async def _check_postgres(self) -> HealthResult:
        """检查 PostgreSQL 健康状态"""
        service_names = self.SERVICE_NAMES["postgres"]
        default_port = self.DEFAULT_PORTS["postgres"]

        # 1. 检查进程
        process = await HealthChecker.check_process_running(service_names)
        if not process:
            return HealthResult(
                service_name="postgres",
                is_healthy=False,
                message="PostgreSQL 服务未运行",
                details={"port": default_port}
            )

        # 2. 检查端口
        port_open = await HealthChecker.check_port_listening("127.0.0.1", default_port)
        if not port_open:
            return HealthResult(
                service_name="postgres",
                is_healthy=False,
                message=f"PostgreSQL 端口 ({default_port}) 未监听",
                details={"port": default_port, "process": process}
            )

        # 3. 尝试连接测试
        connected = await self._test_postgres_connection(default_port)
        if not connected:
            return HealthResult(
                service_name="postgres",
                is_healthy=False,
                message="PostgreSQL 连接失败",
                details={"port": default_port, "process": process}
            )

        return HealthResult(
            service_name="postgres",
            is_healthy=True,
            message="PostgreSQL 服务运行正常",
            details={"port": default_port, "process": process}
        )

    async def _check_mongodb(self) -> HealthResult:
        """检查 MongoDB 健康状态"""
        service_names = self.SERVICE_NAMES["mongodb"]
        default_port = self.DEFAULT_PORTS["mongodb"]

        # 1. 检查进程
        process = await HealthChecker.check_process_running(service_names)
        if not process:
            return HealthResult(
                service_name="mongodb",
                is_healthy=False,
                message="MongoDB 服务未运行",
                details={"port": default_port}
            )

        # 2. 检查端口
        port_open = await HealthChecker.check_port_listening("127.0.0.1", default_port)
        if not port_open:
            return HealthResult(
                service_name="mongodb",
                is_healthy=False,
                message=f"MongoDB 端口 ({default_port}) 未监听",
                details={"port": default_port, "process": process}
            )

        # 3. 尝试连接测试
        connected = await self._test_mongodb_connection(default_port)
        if not connected:
            return HealthResult(
                service_name="mongodb",
                is_healthy=False,
                message="MongoDB 连接失败",
                details={"port": default_port, "process": process}
            )

        return HealthResult(
            service_name="mongodb",
            is_healthy=True,
            message="MongoDB 服务运行正常",
            details={"port": default_port, "process": process}
        )

    async def _test_mysql_connection(self, port: int) -> bool:
        """测试 MySQL 连接"""
        cmd = f"mysqladmin ping -h 127.0.0.1 -P {port} 2>/dev/null || echo 'failed'"
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return b"alive" in stdout or b"running" in stdout

    async def _test_postgres_connection(self, port: int) -> bool:
        """测试 PostgreSQL 连接"""
        cmd = f"pg_isready -h 127.0.0.1 -p {port} 2>/dev/null || echo 'failed'"
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return b"accepting" in stdout or b"ready" in stdout

    async def _test_mongodb_connection(self, port: int) -> bool:
        """测试 MongoDB 连接"""
        cmd = f"mongosh --eval 'db.runCommand({{ping:1}})' --port {port} --quiet 2>/dev/null || echo 'failed'"
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return b"ok" in stdout.lower() or b"true" in stdout.lower()

    async def detect_issues(self) -> List[Issue]:
        """检测数据库问题"""
        issues = []

        for db_type in self.databases.keys():
            db_issues = await self._detect_db_issues(db_type)
            issues.extend(db_issues)

        return issues

    async def _detect_db_issues(self, db_type: str) -> List[Issue]:
        """检测特定数据库的问题"""
        issues = []
        service_names = self.SERVICE_NAMES.get(db_type, [])
        default_port = self.DEFAULT_PORTS.get(db_type, 0)

        # 1. 检查服务是否运行
        process = await HealthChecker.check_process_running(service_names)
        if not process:
            issues.append(Issue(
                service_name=db_type,
                issue_type=IssueType.SERVICE_NOT_RUNNING,
                title=f"{db_type.upper()} 服务未运行",
                description=f"{db_type.upper()} 服务进程未在系统中运行",
                severity="critical",
                detection_method="process_check",
                suggestion=f"请执行: sudo systemctl start {db_type} (Linux) 或 net start {db_type} (Windows)",
                affected_component=f"{db_type.upper()} Server"
            ))
            return issues  # 服务都没运行，后续检查无意义

        # 2. 检查端口是否监听
        port_open = await HealthChecker.check_port_listening("127.0.0.1", default_port)
        if not port_open:
            issues.append(Issue(
                service_name=db_type,
                issue_type=IssueType.PORT_NOT_LISTENING,
                title=f"{db_type.upper()} 端口未监听",
                description=f"{db_type.upper()} 服务进程运行中，但端口 {default_port} 未监听连接",
                severity="high",
                detection_method="port_check",
                suggestion=f"检查配置文件中的 bind-address 设置，确认服务绑定到正确的地址",
                affected_component=f"{db_type.upper()} Network"
            ))

        # 3. 检查配置文件
        config_issues = await self._check_db_config(db_type)
        issues.extend(config_issues)

        # 4. 检查磁盘空间
        disk_issues = await self._check_db_disk_usage(db_type)
        issues.extend(disk_issues)

        return issues

    async def _check_db_config(self, db_type: str) -> List[Issue]:
        """检查数据库配置文件"""
        issues = []

        # 获取配置路径
        config_paths = self.get_config_paths(db_type)
        if not config_paths:
            return issues

        # 检查常见配置问题
        common_issues = self._analyze_db_config(db_type)
        issues.extend(common_issues)

        return issues

    async def _analyze_db_config(self, db_type: str) -> List[Issue]:
        """分析数据库配置，返回发现的问题"""
        issues = []

        if db_type == "mysql":
            # 检查 MySQL 常见配置问题
            # 1. bind-address 检查
            # 2. max_connections 检查
            # 3. 字符集配置
            pass  # 简化实现

        elif db_type == "postgres":
            # 检查 PostgreSQL 常见配置问题
            # 1. listen_addresses 检查
            # 2. max_connections 检查
            # 3. shared_buffers 配置
            pass  # 简化实现

        elif db_type == "mongodb":
            # 检查 MongoDB 常见配置问题
            # 1. bindIp 检查
            # 2. net.port 检查
            pass  # 简化实现

        return issues

    async def _check_db_disk_usage(self, db_type: str) -> List[Issue]:
        """检查数据库磁盘使用情况"""
        issues = []

        try:
            if self.is_windows:
                cmd = 'wmic logicaldisk get size,freespace,caption'
            else:
                cmd = "df -h /var/lib/" + db_type + " 2>/dev/null | tail -1"

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            # 简单解析 - 实际实现需要更复杂的解析
            if b"100%" in stdout or b"90%" in stdout:
                issues.append(Issue(
                    service_name=db_type,
                    issue_type=IssueType.STORAGE_FULL,
                    title=f"{db_type.upper()} 数据目录磁盘空间不足",
                    description="数据库存储空间即将用尽，可能导致写入失败",
                    severity="critical",
                    detection_method="disk_check",
                    suggestion="建议清理旧数据或扩展存储空间",
                    affected_component="Storage"
                ))

        except Exception:
            pass

        return issues

    async def fix(self, issue: Issue, force: bool = False) -> FixResult:
        """修复数据库问题"""
        service_name = issue.service_name.lower()

        if service_name == "mysql":
            return await self._fix_mysql_issue(issue, force)
        elif service_name == "postgres":
            return await self._fix_postgres_issue(issue, force)
        elif service_name == "mongodb":
            return await self._fix_mongodb_issue(issue, force)

        return FixResult(
            success=False,
            message=f"不支持的数据库类型: {service_name}",
            error="Unknown database type"
        )

    async def _fix_mysql_issue(self, issue: Issue, force: bool = False) -> FixResult:
        """修复 MySQL 问题"""
        if issue.issue_type == IssueType.SERVICE_NOT_RUNNING:
            # 尝试启动服务
            return await self._start_service("mysql")

        return FixResult(
            success=False,
            message=f"暂不支持自动修复此问题: {issue.title}",
            error="Not implemented"
        )

    async def _fix_postgres_issue(self, issue: Issue, force: bool = False) -> FixResult:
        """修复 PostgreSQL 问题"""
        if issue.issue_type == IssueType.SERVICE_NOT_RUNNING:
            return await self._start_service("postgres")

        return FixResult(
            success=False,
            message=f"暂不支持自动修复此问题: {issue.title}",
            error="Not implemented"
        )

    async def _fix_mongodb_issue(self, issue: Issue, force: bool = False) -> FixResult:
        """修复 MongoDB 问题"""
        if issue.issue_type == IssueType.SERVICE_NOT_RUNNING:
            return await self._start_service("mongodb")

        return FixResult(
            success=False,
            message=f"暂不支持自动修复此问题: {issue.title}",
            error="Not implemented"
        )

    async def _start_service(self, service_name: str) -> FixResult:
        """启动系统服务"""
        try:
            if self.is_windows:
                cmd = f'net start "{service_name}"'
            elif self.is_linux:
                cmd = f"sudo systemctl start {service_name}"
            elif self.is_macos:
                cmd = f"brew services start {service_name}"
            else:
                return FixResult(
                    success=False,
                    message=f"未知操作系统: {self.system}",
                    error="Unknown OS"
                )

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()

            if proc.returncode == 0:
                return FixResult(
                    success=True,
                    message=f"已成功启动 {service_name} 服务",
                    changes=[f"执行命令: {cmd}"],
                    requires_restart=False
                )
            else:
                return FixResult(
                    success=False,
                    message=f"启动 {service_name} 服务失败",
                    error=stderr.decode()
                )

        except Exception as e:
            return FixResult(
                success=False,
                message=f"启动服务时发生错误: {str(e)}",
                error=str(e)
            )
