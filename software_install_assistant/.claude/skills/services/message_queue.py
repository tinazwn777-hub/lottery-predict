"""
消息队列适配器

支持 RabbitMQ、Kafka 的健康检查和问题检测与修复。
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base.base_adapter import BaseAdapter, HealthResult, Issue, IssueType, FixResult
from ..base.health_checker import HealthChecker


class MessageQueueAdapter(BaseAdapter):
    """消息队列适配器 - 支持 RabbitMQ, Kafka"""

    SERVICE_NAME = "message_queue"

    # 各消息队列的默认配置
    DEFAULT_PORTS = {
        "rabbitmq": 5672,
        "kafka": 9092
    }

    SERVICE_NAMES = {
        "rabbitmq": ["rabbitmq-server", "rabbitmqctl", "rabbitmq"],
        "kafka": ["kafka", "kafka-server", "zookeeper"]
    }

    def __init__(self):
        super().__init__()
        self.queues = {
            "rabbitmq": self._check_rabbitmq,
            "kafka": self._check_kafka
        }

    def get_sub_services(self) -> Dict[str, str]:
        return {
            "rabbitmq": "RabbitMQ 消息队列",
            "kafka": "Kafka 消息队列"
        }

    async def health_check(self, sub_service: Optional[str] = None) -> HealthResult:
        """执行消息队列健康检查"""
        if sub_service:
            checker = self.queues.get(sub_service.lower())
            if checker:
                return await checker()
            return HealthResult(
                service_name=sub_service,
                is_healthy=False,
                message=f"未知的消息队列类型: {sub_service}"
            )

        # 检查所有消息队列
        results = {}
        all_healthy = True

        for name, checker in self.queues.items():
            result = await checker()
            results[name] = result.to_dict()
            if not result.is_healthy:
                all_healthy = False

        if all_healthy:
            return HealthResult(
                service_name=self.SERVICE_NAME,
                is_healthy=True,
                message="所有消息队列服务运行正常",
                details=results
            )
        else:
            return HealthResult(
                service_name=self.SERVICE_NAME,
                is_healthy=False,
                message="部分消息队列服务存在异常",
                details=results
            )

    async def _check_rabbitmq(self) -> HealthResult:
        """检查 RabbitMQ 健康状态"""
        service_names = self.SERVICE_NAMES["rabbitmq"]
        default_port = self.DEFAULT_PORTS["rabbitmq"]

        # 1. 检查进程
        process = await HealthChecker.check_process_running(service_names)
        if not process:
            return HealthResult(
                service_name="rabbitmq",
                is_healthy=False,
                message="RabbitMQ 服务未运行"
            )

        # 2. 检查端口
        port_open = await HealthChecker.check_port_listening("127.0.0.1", default_port)
        if not port_open:
            return HealthResult(
                service_name="rabbitmq",
                is_healthy=False,
                message=f"RabbitMQ 端口 ({default_port}) 未监听"
            )

        # 3. 检查管理插件
        healthy, status = await self._check_rabbitmq_status()
        if not healthy:
            return HealthResult(
                service_name="rabbitmq",
                is_healthy=False,
                message=status,
                details={"port": default_port, "process": process}
            )

        return HealthResult(
            service_name="rabbitmq",
            is_healthy=True,
            message="RabbitMQ 服务运行正常",
            details={"port": default_port, "process": process}
        )

    async def _check_kafka(self) -> HealthResult:
        """检查 Kafka 健康状态"""
        kafka_service = self.SERVICE_NAMES["kafka"][0]
        zookeeper_service = self.SERVICE_NAMES["kafka"][2]

        # 1. 检查 Kafka 进程
        kafka_process = await HealthChecker.check_process_running([kafka_service])

        # 2. 检查 Zookeeper 进程（Kafka 依赖 Zookeeper）
        zk_process = await HealthChecker.check_process_running([zookeeper_service])

        if not kafka_process:
            return HealthResult(
                service_name="kafka",
                is_healthy=False,
                message="Kafka 服务未运行"
            )

        if not zk_process:
            return HealthResult(
                service_name="kafka",
                is_healthy=False,
                message="Kafka 依赖的 Zookeeper 未运行"
            )

        # 3. 检查端口
        default_port = self.DEFAULT_PORTS["kafka"]
        port_open = await HealthChecker.check_port_listening("127.0.0.1", default_port)
        if not port_open:
            return HealthResult(
                service_name="kafka",
                is_healthy=False,
                message=f"Kafka 端口 ({default_port}) 未监听"
            )

        # 4. 测试连接
        connected = await self._test_kafka_connection(default_port)
        if not connected:
            return HealthResult(
                service_name="kafka",
                is_healthy=False,
                message="Kafka 连接测试失败"
            )

        return HealthResult(
            service_name="kafka",
            is_healthy=True,
            message="Kafka 服务运行正常",
            details={"port": default_port}
        )

    async def _check_rabbitmq_status(self) -> tuple:
        """检查 RabbitMQ 状态"""
        try:
            cmd = "rabbitmqctl status 2>/dev/null"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            return proc.returncode == 0, "RabbitMQ 服务运行正常" if proc.returncode == 0 else "RabbitMQ 状态检查失败"
        except Exception as e:
            return False, str(e)

    async def _test_kafka_connection(self, port: int = 9092) -> bool:
        """测试 Kafka 连接"""
        try:
            # 使用 kafka-topics 或 kafka-broker-api-versions
            cmd = f"kafka-broker-api-versions --bootstrap-server 127.0.0.1:{port} --timeout 5000 2>/dev/null | head -1"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(proc.communicate(), timeout=10)
            return proc.returncode == 0
        except Exception:
            return False

    async def detect_issues(self) -> List[Issue]:
        """检测消息队列问题"""
        issues = []

        for queue_type in self.queues.keys():
            queue_issues = await self._detect_queue_issues(queue_type)
            issues.extend(queue_issues)

        return issues

    async def _detect_queue_issues(self, queue_type: str) -> List[Issue]:
        """检测特定消息队列的问题"""
        issues = []
        service_names = self.SERVICE_NAMES.get(queue_type, [])
        default_port = self.DEFAULT_PORTS.get(queue_type, 0)

        if queue_type == "rabbitmq":
            issues.extend(await self._detect_rabbitmq_issues(service_names, default_port))
        elif queue_type == "kafka":
            issues.extend(await self._detect_kafka_issues(service_names, default_port))

        return issues

    async def _detect_rabbitmq_issues(self, service_names: List[str], default_port: int) -> List[Issue]:
        """检测 RabbitMQ 问题"""
        issues = []

        # 1. 检查服务是否运行
        process = await HealthChecker.check_process_running(service_names)
        if not process:
            issues.append(Issue(
                service_name="rabbitmq",
                issue_type=IssueType.SERVICE_NOT_RUNNING,
                title="RabbitMQ 服务未运行",
                description="RabbitMQ 服务进程未在系统中运行",
                severity="critical",
                detection_method="process_check",
                suggestion="请执行: sudo systemctl start rabbitmq-server",
                affected_component="RabbitMQ Server"
            ))
            return issues

        # 2. 检查 Erlang 是否安装
        erlang_ok, _ = await self._check_erlang_installation()
        if not erlang_ok:
            issues.append(Issue(
                service_name="rabbitmq",
                issue_type=IssueType.DEPENDENCY_MISSING,
                title="Erlang 环境缺失",
                description="RabbitMQ 依赖 Erlang 运行，但未检测到有效的 Erlang 环境",
                severity="critical",
                detection_method="dependency_check",
                suggestion="请安装与当前 RabbitMQ 版本兼容的 Erlang",
                affected_component="Erlang Runtime"
            ))

        # 3. 检查端口
        port_open = await HealthChecker.check_port_listening("127.0.0.1", default_port)
        if not port_open:
            issues.append(Issue(
                service_name="rabbitmq",
                issue_type=IssueType.PORT_NOT_LISTENING,
                title="RabbitMQ 端口未监听",
                description=f"RabbitMQ 端口 ({default_port}) 未监听，可能配置错误",
                severity="high",
                detection_method="port_check",
                suggestion="检查 RabbitMQ 配置文件中的端口设置",
                affected_component="RabbitMQ Network"
            ))

        # 4. 检查必需插件
        plugin_issues = await self._check_rabbitmq_plugins()
        issues.extend(plugin_issues)

        return issues

    async def _detect_kafka_issues(self, service_names: List[str], default_port: int) -> List[Issue]:
        """检测 Kafka 问题"""
        issues = []

        # 1. 检查服务是否运行
        kafka_process = await HealthChecker.check_process_running([service_names[0]])
        if not kafka_process:
            issues.append(Issue(
                service_name="kafka",
                issue_type=IssueType.SERVICE_NOT_RUNNING,
                title="Kafka 服务未运行",
                description="Kafka 服务进程未在系统中运行",
                severity="critical",
                detection_method="process_check",
                suggestion="请执行: sudo systemctl start kafka",
                affected_component="Kafka Server"
            ))
            return issues

        # 2. 检查 Zookeeper 依赖
        zk_process = await HealthChecker.check_process_running([service_names[2]])
        if not zk_process:
            issues.append(Issue(
                service_name="kafka",
                issue_type=IssueType.DEPENDENCY_MISSING,
                title="Kafka 依赖的 Zookeeper 未运行",
                description="Kafka 依赖 Zookeeper 进行元数据管理",
                severity="critical",
                detection_method="dependency_check",
                suggestion="请先启动 Zookeeper 服务",
                affected_component="Zookeeper"
            ))

        # 3. 检查端口
        port_open = await HealthChecker.check_port_listening("127.0.0.1", default_port)
        if not port_open:
            issues.append(Issue(
                service_name="kafka",
                issue_type=IssueType.PORT_NOT_LISTENING,
                title="Kafka 端口未监听",
                description=f"Kafka 端口 ({default_port}) 未监听",
                severity="high",
                detection_method="port_check",
                suggestion="检查 Kafka 配置文件中的 listeners 设置",
                affected_component="Kafka Network"
            ))

        return issues

    async def _check_erlang_installation(self) -> tuple:
        """检查 Erlang 安装"""
        try:
            cmd = "erl -version 2>&1 | head -1"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            return proc.returncode == 0, stdout.decode().strip()
        except Exception as e:
            return False, str(e)

    async def _check_rabbitmq_plugins(self) -> List[Issue]:
        """检查 RabbitMQ 必需插件"""
        issues = []

        try:
            cmd = "rabbitmq-plugins list -m 2>/dev/null"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            # 检查必需的插件
            required_plugins = ["rabbitmq_management", "rabbitmq_amqp1_0"]
            enabled_plugins = []

            for line in stdout.decode().splitlines():
                plugin = line.strip()
                if plugin and not plugin.startswith('['):
                    enabled_plugins.append(plugin.lower())

            # 检查 management 插件
            if "rabbitmq_management" not in enabled_plugins:
                issues.append(Issue(
                    service_name="rabbitmq",
                    issue_type=IssueType.CONFIG_INVALID,
                    title="RabbitMQ 管理插件未启用",
                    description="rabbitmq_management 插件未启用，影响管理功能",
                    severity="low",
                    detection_method="plugin_check",
                    suggestion="执行: rabbitmq-plugins enable rabbitmq_management",
                    affected_component="Management Plugin"
                ))

        except Exception:
            pass

        return issues

    async def fix(self, issue: Issue, force: bool = False) -> FixResult:
        """修复消息队列问题"""
        service_name = issue.service_name.lower()

        if service_name == "rabbitmq":
            return await self._fix_rabbitmq_issue(issue, force)
        elif service_name == "kafka":
            return await self._fix_kafka_issue(issue, force)

        return FixResult(
            success=False,
            message=f"未支持的消息队列类型: {service_name}",
            error="Unknown message queue type"
        )

    async def _fix_rabbitmq_issue(self, issue: Issue, force: bool = False) -> FixResult:
        """修复 RabbitMQ 问题"""
        if issue.issue_type == IssueType.SERVICE_NOT_RUNNING:
            return await self._start_rabbitmq()

        elif issue.issue_type == IssueType.DEPENDENCY_MISSING:
            return FixResult(
                success=False,
                message="Erlang 依赖需要手动安装，请查看 RabbitMQ 官网获取兼容版本信息",
                error="Manual installation required"
            )

        elif issue.issue_type == IssueType.CONFIG_INVALID:
            if "插件" in issue.title:
                return await self._enable_rabbitmq_plugin("rabbitmq_management")

        return FixResult(
            success=False,
            message=f"暂不支持自动修复此问题: {issue.title}",
            error="Not implemented"
        )

    async def _fix_kafka_issue(self, issue: Issue, force: bool = False) -> FixResult:
        """修复 Kafka 问题"""
        if issue.issue_type == IssueType.SERVICE_NOT_RUNNING:
            return await self._start_kafka()

        elif issue.issue_type == IssueType.DEPENDENCY_MISSING:
            return FixResult(
                success=False,
                message="Zookeeper 需要先启动，请执行: sudo systemctl start zookeeper",
                error="Zookeeper must be started first"
            )

        return FixResult(
            success=False,
            message=f"暂不支持自动修复此问题: {issue.title}",
            error="Not implemented"
        )

    async def _start_rabbitmq(self) -> FixResult:
        """启动 RabbitMQ 服务"""
        try:
            if self.is_windows:
                cmd = 'net start "RabbitMQ"'
            elif self.is_linux:
                cmd = "sudo systemctl start rabbitmq-server"
            elif self.is_macos:
                cmd = "brew services start rabbitmq"
            else:
                cmd = "rabbitmq-server &"

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()

            if proc.returncode == 0:
                # 等待服务启动
                await asyncio.sleep(5)
                healthy, _ = await self._check_rabbitmq_status()
                if healthy:
                    return FixResult(
                        success=True,
                        message="已成功启动 RabbitMQ 服务",
                        changes=[f"执行命令: {cmd}"],
                        requires_restart=False
                    )

            return FixResult(
                success=False,
                message=f"启动 RabbitMQ 服务失败: {stderr.decode()}",
                error=stderr.decode()
            )

        except Exception as e:
            return FixResult(
                success=False,
                message=f"启动 RabbitMQ 时发生错误: {str(e)}",
                error=str(e)
            )

    async def _start_kafka(self) -> FixResult:
        """启动 Kafka 服务"""
        try:
            if self.is_linux:
                cmd = "sudo systemctl start kafka"
            elif self.is_macos:
                cmd = "brew services start kafka"
            else:
                cmd = "kafka-server-start.sh &"

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()

            if proc.returncode == 0:
                await asyncio.sleep(10)
                connected = await self._test_kafka_connection()
                if connected:
                    return FixResult(
                        success=True,
                        message="已成功启动 Kafka 服务",
                        changes=[f"执行命令: {cmd}"],
                        requires_restart=False
                    )

            return FixResult(
                success=False,
                message=f"启动 Kafka 服务失败: {stderr.decode()}",
                error=stderr.decode()
            )

        except Exception as e:
            return FixResult(
                success=False,
                message=f"启动 Kafka 时发生错误: {str(e)}",
                error=str(e)
            )

    async def _enable_rabbitmq_plugin(self, plugin_name: str) -> FixResult:
        """启用 RabbitMQ 插件"""
        try:
            cmd = f"sudo rabbitmq-plugins enable {plugin_name}"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()

            if proc.returncode == 0:
                return FixResult(
                    success=True,
                    message=f"已成功启用 {plugin_name} 插件",
                    changes=[f"执行命令: {cmd}"],
                    requires_restart=True
                )
            else:
                return FixResult(
                    success=False,
                    message=f"启用插件失败: {stderr.decode()}",
                    error=stderr.decode()
                )

        except Exception as e:
            return FixResult(
                success=False,
                message=f"启用插件时发生错误: {str(e)}",
                error=str(e)
            )
