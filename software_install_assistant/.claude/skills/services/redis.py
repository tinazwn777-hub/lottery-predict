"""
Redis 适配器

支持 Redis 的健康检查和问题检测与修复。
"""

import asyncio
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base.base_adapter import BaseAdapter, HealthResult, Issue, IssueType, FixResult
from ..base.health_checker import HealthChecker


class RedisAdapter(BaseAdapter):
    """Redis 适配器"""

    SERVICE_NAME = "redis"
    DEFAULT_PORTS = [6379, 16379]  # 默认端口和集群端口

    # Redis 服务进程名称
    SERVICE_NAMES = ["redis-server", "redis"]

    # 配置文件路径
    CONFIG_PATHS = [
        "/etc/redis/redis.conf",
        "/etc/redis.conf",
        "/etc/redis/redis.conf",
        "C:\\Program Files\\Redis\\redis.windows.conf",
        "C:\\Program Files\\Redis\\redis.windows-service.conf",
        "C:\\ProgramData\\Redis\\redis.conf"
    ]

    # AOF 文件路径
    AOF_PATHS = [
        "/var/lib/redis/appendonly.aof",
        "/etc/redis/appendonly.aof",
        "C:\\ProgramData\\Redis\\appendonly.aof"
    ]

    def __init__(self):
        super().__init__()
        self.config_data: Dict[str, Any] = {}

    async def health_check(self, sub_service: Optional[str] = None) -> HealthResult:
        """执行 Redis 健康检查"""
        # 1. 检查进程
        process = await HealthChecker.check_process_running(self.SERVICE_NAMES)
        if not process:
            return HealthResult(
                service_name=self.SERVICE_NAME,
                is_healthy=False,
                message="Redis 服务未运行"
            )

        # 2. 检查主端口
        main_port = self.DEFAULT_PORTS[0]
        port_open = await HealthChecker.check_port_listening("127.0.0.1", main_port)
        if not port_open:
            return HealthResult(
                service_name=self.SERVICE_NAME,
                is_healthy=False,
                message=f"Redis 端口 ({main_port}) 未监听",
                details={"port": main_port, "process": process}
            )

        # 3. 执行 PING 测试
        pong = await self._redis_ping(main_port)
        if not pong:
            return HealthResult(
                service_name=self.SERVICE_NAME,
                is_healthy=False,
                message="Redis PING 测试失败",
                details={"port": main_port, "process": process}
            )

        # 4. 获取 Redis 信息
        info = await self._redis_info(main_port)

        return HealthResult(
            service_name=self.SERVICE_NAME,
            is_healthy=True,
            message="Redis 服务运行正常",
            details={
                "port": main_port,
                "process": process,
                "version": info.get("redis_version", "unknown"),
                "mode": info.get("mode", "unknown"),
                "connected_clients": info.get("connected_clients", 0)
            }
        )

    async def detect_issues(self) -> List[Issue]:
        """检测 Redis 问题"""
        issues = []

        # 1. 检查服务是否运行
        process = await HealthChecker.check_process_running(self.SERVICE_NAMES)
        if not process:
            issues.append(Issue(
                service_name=self.SERVICE_NAME,
                issue_type=IssueType.SERVICE_NOT_RUNNING,
                title="Redis 服务未运行",
                description="Redis 服务进程未在系统中运行",
                severity="critical",
                detection_method="process_check",
                suggestion="请执行: redis-server 或 sudo systemctl start redis",
                affected_component="Redis Server"
            ))
            return issues

        # 2. 检查端口
        main_port = self.DEFAULT_PORTS[0]
        port_open = await HealthChecker.check_port_listening("127.0.0.1", main_port)
        if not port_open:
            issues.append(Issue(
                service_name=self.SERVICE_NAME,
                issue_type=IssueType.PORT_NOT_LISTENING,
                title="Redis 端口未监听",
                description=f"Redis 服务运行中，但端口 {main_port} 未监听连接",
                severity="high",
                detection_method="port_check",
                suggestion="检查 bind-address 配置，确保 Redis 绑定到可用地址",
                affected_component="Redis Network"
            ))

        # 3. 检查配置问题
        config_issues = await self._check_redis_config()
        issues.extend(config_issues)

        # 4. 检查 AOF/RDB 文件
        file_issues = await self._check_redis_files()
        issues.extend(file_issues)

        # 5. 检查内存使用
        memory_issues = await self._check_redis_memory()
        issues.extend(memory_issues)

        return issues

    async def _redis_ping(self, port: int = 6379) -> bool:
        """执行 Redis PING 命令"""
        cmd = f"redis-cli -p {port} PING 2>/dev/null || echo 'PONG_FAILED'"
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return b"PONG" in stdout or b"+PONG" in stdout

    async def _redis_info(self, port: int = 6379) -> Dict[str, Any]:
        """获取 Redis INFO"""
        info = {}
        cmd = f"redis-cli -p {port} INFO 2>/dev/null"
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()

        for line in stdout.decode().splitlines():
            if ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()

        return info

    async def _redis_command(self, port: int = 6379, *args) -> Optional[str]:
        """执行 Redis 命令"""
        cmd = f"redis-cli -p {port} {' '.join(args)} 2>/dev/null"
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return stdout.decode().strip() if stdout else None

    async def _check_redis_config(self) -> List[Issue]:
        """检查 Redis 配置问题"""
        issues = []

        # 尝试读取配置
        await self._load_redis_config()

        # 检查 protected-mode
        protected_mode = self.config_data.get("protected-mode", "").lower()
        if protected_mode == "no":
            issues.append(Issue(
                service_name=self.SERVICE_NAME,
                issue_type=IssueType.CONFIG_INVALID,
                title="Redis protected-mode 关闭",
                description="protected-mode 设置为 no，可能存在安全风险",
                severity="medium",
                detection_method="config_check",
                suggestion="建议启用 protected-mode 或配置 bind-address 和密码",
                affected_component="Security",
                raw_data={"protected-mode": protected_mode}
            ))

        # 检查 bind
        bind_addresses = self.config_data.get("bind", "")
        if bind_addresses and "127.0.0.1" not in bind_addresses and "localhost" not in bind_addresses:
            issues.append(Issue(
                service_name=self.SERVICE_NAME,
                issue_type=IssueType.CONFIG_INVALID,
                title="Redis 绑定到非本地地址",
                description=f"Redis bind 设置为 {bind_addresses}，可能存在网络暴露风险",
                severity="high",
                detection_method="config_check",
                suggestion="建议绑定到 localhost 或配置防火墙规则",
                affected_component="Security",
                raw_data={"bind": bind_addresses}
            ))

        # 检查是否设置密码
        requirepass = self.config_data.get("requirepass", "")
        if not requirepass:
            issues.append(Issue(
                service_name=self.SERVICE_NAME,
                issue_type=IssueType.CONFIG_INVALID,
                title="Redis 未设置密码",
                description="Redis 服务未配置认证密码",
                severity="medium",
                detection_method="config_check",
                suggestion="建议配置 requirepass 以提高安全性",
                affected_component="Security"
            ))

        return issues

    async def _load_redis_config(self) -> None:
        """加载 Redis 配置"""
        config_path = self._find_redis_config()
        if config_path:
            try:
                # 尝试使用 CONFIG GET
                info = await self._redis_info()
                self.config_data = info
            except Exception:
                # 如果连接失败，尝试读取配置文件
                self.config_data = self._read_config_file(config_path)

    def _find_redis_config(self) -> Optional[str]:
        """查找 Redis 配置文件"""
        for path_pattern in self.CONFIG_PATHS:
            if "*" in path_pattern:
                # 处理通配符
                import glob
                matches = glob.glob(path_pattern)
                if matches:
                    return matches[0]
            else:
                if Path(path_pattern).exists():
                    return path_pattern
        return None

    def _read_config_file(self, config_path: str) -> Dict[str, Any]:
        """读取 Redis 配置文件"""
        config = {}
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if ' ' in line:
                            parts = line.split(' ', 1)
                            if len(parts) == 2:
                                config[parts[0]] = parts[1]
                        elif ' ' not in line and ':' in line:
                            parts = line.split(':', 1)
                            if len(parts) == 2:
                                config[parts[0]] = parts[1]
        except Exception:
            pass
        return config

    async def _check_redis_files(self) -> List[Issue]:
        """检查 Redis 数据文件"""
        issues = []

        # 检查 AOF 文件
        aof_path = self.AOF_PATHS[0] if self.is_linux else self.AOF_PATHS[2]
        if self.is_windows:
            aof_path = self.AOF_PATHS[2]

        if Path(aof_path).exists():
            try:
                size = Path(aof_path).stat().st_size
                # 检查 AOF 文件大小是否异常
                if size == 0:
                    issues.append(Issue(
                        service_name=self.SERVICE_NAME,
                        issue_type=IssueType.CONFIG_INVALID,
                        title="Redis AOF 文件为空",
                        description="AOF 持久化文件大小为 0，可能需要重建",
                        severity="medium",
                        detection_method="file_check",
                        suggestion="执行 BGSAVE 或检查 AOF 配置",
                        affected_component="Persistence"
                    ))
            except Exception:
                pass

        return issues

    async def _check_redis_memory(self) -> List[Issue]:
        """检查 Redis 内存使用"""
        issues = []

        try:
            info = await self._redis_info()
            used_memory = int(info.get("used_memory_human", "0K")[:-1]) * 1024
            max_memory = int(info.get("maxmemory_human", "0K")[:-1]) * 1024 if info.get("maxmemory_human") else 0

            if max_memory > 0 and used_memory > max_memory * 0.9:
                issues.append(Issue(
                    service_name=self.SERVICE_NAME,
                    issue_type=IssueType.STORAGE_FULL,
                    title="Redis 内存使用率过高",
                    description="Redis 内存使用接近最大限制，可能触发内存淘汰策略",
                    severity="high",
                    detection_method="memory_check",
                    suggestion="考虑增加 maxmemory 或优化数据存储",
                    affected_component="Memory",
                    raw_data={"used_memory": used_memory, "max_memory": max_memory}
                ))
        except Exception:
            pass

        return issues

    async def fix(self, issue: Issue, force: bool = False) -> FixResult:
        """修复 Redis 问题"""
        if issue.issue_type == IssueType.SERVICE_NOT_RUNNING:
            return await self._start_redis()

        elif issue.issue_type == IssueType.PORT_NOT_LISTENING:
            return await self._fix_port_issue()

        return FixResult(
            success=False,
            message=f"暂不支持自动修复此问题: {issue.title}",
            error="Not implemented"
        )

    async def _start_redis(self) -> FixResult:
        """启动 Redis 服务"""
        try:
            if self.is_windows:
                cmd = 'net start "Redis"'
            elif self.is_linux:
                cmd = "sudo systemctl start redis"
            elif self.is_macos:
                cmd = "brew services start redis"
            else:
                cmd = "redis-server &"

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()

            if proc.returncode == 0:
                # 等待服务启动
                await asyncio.sleep(2)
                pong = await self._redis_ping()
                if pong:
                    return FixResult(
                        success=True,
                        message="已成功启动 Redis 服务",
                        changes=[f"执行命令: {cmd}"],
                        requires_restart=False
                    )

            return FixResult(
                success=False,
                message=f"启动 Redis 服务失败: {stderr.decode()}",
                error=stderr.decode()
            )

        except Exception as e:
            return FixResult(
                success=False,
                message=f"启动 Redis 时发生错误: {str(e)}",
                error=str(e)
            )

    async def _fix_port_issue(self) -> FixResult:
        """修复端口监听问题"""
        return FixResult(
            success=False,
            message="端口监听问题通常需要检查配置文件中的 bind 设置，请手动处理",
            suggestion="检查 redis.conf 中的 bind 配置"
        )
