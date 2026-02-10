"""
Elasticsearch 适配器

支持 Elasticsearch 的健康检查和问题检测与修复。
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base.base_adapter import BaseAdapter, HealthResult, Issue, IssueType, FixResult
from ..base.health_checker import HealthChecker


class ElasticsearchAdapter(BaseAdapter):
    """Elasticsearch 适配器"""

    SERVICE_NAME = "elasticsearch"
    DEFAULT_PORTS = [9200, 9300]  # HTTP 端口和集群通信端口

    # Elasticsearch 服务进程名称
    SERVICE_NAMES = ["elasticsearch", "java"]

    # 配置文件路径
    CONFIG_PATHS = [
        "/etc/elasticsearch/elasticsearch.yml",
        "/etc/elasticsearch.yml",
        "/usr/local/etc/elasticsearch/elasticsearch.yml",
        "C:\\Program Files\\Elasticsearch\\config\\elasticsearch.yml",
        "C:\\Elastic\\config\\elasticsearch.yml"
    ]

    # JVM 配置路径
    JVM_PATHS = [
        "/etc/elasticsearch/jvm.options",
        "/etc/elasticsearch/jvm.options.d/",
        "/usr/local/etc/elasticsearch/jvm.options",
        "C:\\Program Files\\Elasticsearch\\config\\jvm.options",
        "C:\\Elastic\\config\\jvm.options"
    ]

    def __init__(self):
        super().__init__()
        self.cluster_info: Dict[str, Any] = {}

    async def health_check(self, sub_service: Optional[str] = None) -> HealthResult:
        """执行 Elasticsearch 健康检查"""
        # 1. 检查进程
        process = await HealthChecker.check_process_running(self.SERVICE_NAMES)
        if not process:
            return HealthResult(
                service_name=self.SERVICE_NAME,
                is_healthy=False,
                message="Elasticsearch 服务未运行"
            )

        # 2. 检查 HTTP 端口
        http_port = self.DEFAULT_PORTS[0]
        port_open = await HealthChecker.check_port_listening("127.0.0.1", http_port)
        if not port_open:
            return HealthResult(
                service_name=self.SERVICE_NAME,
                is_healthy=False,
                message=f"Elasticsearch 端口 ({http_port}) 未监听",
                details={"port": http_port, "process": process}
            )

        # 3. 获取集群健康状态
        cluster_healthy, info = await self._get_cluster_info()
        if not cluster_healthy:
            return HealthResult(
                service_name=self.SERVICE_NAME,
                is_healthy=False,
                message=info.get("message", "Elasticsearch 集群状态异常"),
                details=info
            )

        return HealthResult(
            service_name=self.SERVICE_NAME,
            is_healthy=True,
            message="Elasticsearch 服务运行正常",
            details={
                "cluster_name": info.get("cluster_name"),
                "status": info.get("status"),
                "number_of_nodes": info.get("number_of_nodes"),
                "version": info.get("version", {}).get("number")
            }
        )

    async def detect_issues(self) -> List[Issue]:
        """检测 Elasticsearch 问题"""
        issues = []

        # 1. 检查服务是否运行
        process = await HealthChecker.check_process_running(self.SERVICE_NAMES)
        if not process:
            issues.append(Issue(
                service_name=self.SERVICE_NAME,
                issue_type=IssueType.SERVICE_NOT_RUNNING,
                title="Elasticsearch 服务未运行",
                description="Elasticsearch 服务进程未在系统中运行",
                severity="critical",
                detection_method="process_check",
                suggestion="请执行: sudo systemctl start elasticsearch",
                affected_component="Elasticsearch Server"
            ))
            return issues

        # 2. 检查端口
        http_port = self.DEFAULT_PORTS[0]
        port_open = await HealthChecker.check_port_listening("127.0.0.1", http_port)
        if not port_open:
            issues.append(Issue(
                service_name=self.SERVICE_NAME,
                issue_type=IssueType.PORT_NOT_LISTENING,
                title="Elasticsearch 端口未监听",
                description=f"Elasticsearch HTTP 端口 ({http_port}) 未监听",
                severity="high",
                detection_method="port_check",
                suggestion="检查 Elasticsearch 配置文件中的 http.port 设置",
                affected_component="Elasticsearch Network"
            ))
            return issues

        # 3. 检查集群健康状态
        health_issues = await self._check_cluster_health()
        issues.extend(health_issues)

        # 4. 检查 JVM 内存配置
        jvm_issues = await self._check_jvm_config()
        issues.extend(jvm_issues)

        # 5. 检查磁盘空间
        disk_issues = await self._check_disk_usage()
        issues.extend(disk_issues)

        # 6. 检查插件问题
        plugin_issues = await self._check_plugins()
        issues.extend(plugin_issues)

        return issues

    async def _get_cluster_info(self) -> tuple:
        """获取集群信息"""
        try:
            http_port = self.DEFAULT_PORTS[0]
            cmd = f"curl -s http://127.0.0.1:{http_port}/_cluster/health 2>/dev/null"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            if proc.returncode == 0 and stdout:
                info = json.loads(stdout.decode())
                self.cluster_info = info

                # 检查状态
                status = info.get("status", "red")
                if status in ["red"]:
                    return False, {"message": f"集群状态异常: {status}", **info}
                elif status in ["yellow"]:
                    return True, {"message": "集群状态警告", **info}

                return True, {"message": "集群状态正常", **info}

            return False, {"message": "无法获取集群信息"}

        except Exception as e:
            return False, {"message": str(e)}

    async def _check_cluster_health(self) -> List[Issue]:
        """检查集群健康状态"""
        issues = []

        try:
            http_port = self.DEFAULT_PORTS[0]
            cmd = f"curl -s http://127.0.0.1:{http_port}/_cluster/health 2>/dev/null"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            if proc.returncode == 0 and stdout:
                health = json.loads(stdout.decode())
                status = health.get("status", "red")

                if status == "red":
                    issues.append(Issue(
                        service_name=self.SERVICE_NAME,
                        issue_type=IssueType.CONFIG_INVALID,
                        title="Elasticsearch 集群状态为红色",
                        description="集群存在严重问题，部分分片可能不可用",
                        severity="critical",
                        detection_method="cluster_health_check",
                        suggestion="检查日志文件，查看具体错误信息，可能需要修复或删除问题索引",
                        affected_component="Cluster",
                        raw_data=health
                    ))

                elif status == "yellow":
                    issues.append(Issue(
                        service_name=self.SERVICE_NAME,
                        issue_type=IssueType.CONFIG_INVALID,
                        title="Elasticsearch 集群状态为黄色",
                        description="集群存在警告，某些分片可能未分配",
                        severity="medium",
                        detection_method="cluster_health_check",
                        suggestion="可能是由于副本分片未分配，检查集群配置或增加节点",
                        affected_component="Cluster",
                        raw_data=health
                    ))

                # 检查未分配的分片
                unassigned_shards = health.get("unassigned_shards", 0)
                if unassigned_shards > 0:
                    issues.append(Issue(
                        service_name=self.SERVICE_NAME,
                        issue_type=IssueType.CONFIG_INVALID,
                        title=f"存在 {unassigned_shards} 个未分配的分片",
                        description="集群中有未分配的分片，影响数据可用性",
                        severity="high",
                        detection_method="shard_check",
                        suggestion="检查集群健康日志，查看分片未分配的原因",
                        affected_component="Shards"
                    ))

        except Exception as e:
            pass

        return issues

    async def _check_jvm_config(self) -> List[Issue]:
        """检查 JVM 配置问题"""
        issues = []

        jvm_path = self._find_jvm_config()
        if not jvm_path:
            return issues

        try:
            # 读取 JVM 配置
            if Path(jvm_path).is_file():
                with open(jvm_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查堆内存设置
                heap_match = re.search(r'-Xmx(\d+)([mMgG])', content)
                if heap_match:
                    heap_size = int(heap_match.group(1)) * (1024 if heap_match.group(2) == 'm' else 1)
                    # 检查是否低于推荐值
                    if heap_size < 512:
                        issues.append(Issue(
                            service_name=self.SERVICE_NAME,
                            issue_type=IssueType.CONFIG_INVALID,
                            title="JVM 堆内存设置过小",
                            description=f"当前最大堆内存为 {heap_match.group(1)}{heap_match.group(2)}，建议至少 512m",
                            severity="medium",
                            detection_method="jvm_config_check",
                            suggestion=f"修改 {jvm_path} 中的 -Xmx 和 -Xms 设置",
                            affected_component="JVM"
                        ))

        except Exception:
            pass

        return issues

    def _find_jvm_config(self) -> Optional[str]:
        """查找 JVM 配置文件"""
        for path in self.JVM_PATHS:
            if Path(path).exists():
                return str(path)
        return None

    async def _check_disk_usage(self) -> List[Issue]:
        """检查磁盘使用情况"""
        issues = []

        try:
            http_port = self.DEFAULT_PORTS[0]
            cmd = f"curl -s http://127.0.0.1:{http_port}/_cat/allocation?v 2>/dev/null"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            if proc.returncode == 0 and stdout:
                lines = stdout.decode().splitlines()
                if len(lines) > 1:
                    # 解析磁盘使用率
                    for line in lines[1:]:
                        parts = line.split()
                        if len(parts) >= 2:
                            disk_avail = parts[-1]  # 可用空间
                            # 简化处理，实际需要更复杂的解析
                            pass

        except Exception:
            pass

        return issues

    async def _check_plugins(self) -> List[Issue]:
        """检查插件问题"""
        issues = []

        try:
            http_port = self.DEFAULT_PORTS[0]
            cmd = f"curl -s http://127.0.0.1:{http_port}/_cat/plugins?v 2>/dev/null"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            # 插件检查通常不需要特别操作，仅记录信息
            if proc.returncode == 0:
                plugins = stdout.decode()
                # 常见的冲突插件检查需要更复杂的逻辑
                pass

        except Exception:
            pass

        return issues

    async def fix(self, issue: Issue, force: bool = False) -> FixResult:
        """修复 Elasticsearch 问题"""
        if issue.issue_type == IssueType.SERVICE_NOT_RUNNING:
            return await self._start_elasticsearch()

        elif issue.issue_type == IssueType.CONFIG_INVALID:
            if "JVM" in issue.title:
                return await self._fix_jvm_config()

        return FixResult(
            success=False,
            message=f"暂不支持自动修复此问题: {issue.title}",
            error="Not implemented"
        )

    async def _start_elasticsearch(self) -> FixResult:
        """启动 Elasticsearch 服务"""
        try:
            if self.is_windows:
                cmd = 'net start "Elasticsearch"'
            elif self.is_linux:
                cmd = "sudo systemctl start elasticsearch"
            elif self.is_macos:
                cmd = "brew services start elasticsearch"
            else:
                cmd = "elasticsearch &"

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()

            if proc.returncode == 0:
                # 等待服务启动
                await asyncio.sleep(10)
                port_open = await HealthChecker.check_port_listening("127.0.0.1", self.DEFAULT_PORTS[0])
                if port_open:
                    return FixResult(
                        success=True,
                        message="已成功启动 Elasticsearch 服务",
                        changes=[f"执行命令: {cmd}"],
                        requires_restart=False
                    )

            return FixResult(
                success=False,
                message=f"启动 Elasticsearch 服务失败: {stderr.decode()}",
                error=stderr.decode()
            )

        except Exception as e:
            return FixResult(
                success=False,
                message=f"启动 Elasticsearch 时发生错误: {str(e)}",
                error=str(e)
            )

    async def _fix_jvm_config(self) -> FixResult:
        """修复 JVM 配置"""
        jvm_path = self._find_jvm_config()
        if not jvm_path:
            return FixResult(
                success=False,
                message="未找到 JVM 配置文件",
                error="Config file not found"
            )

        return FixResult(
            success=False,
            message="JVM 配置修改需要手动操作，请编辑配置文件并重启服务",
            suggestion=f"修改 {jvm_path} 中的 -Xmx 和 -Xms 设置，建议设置为物理内存的 50%"
        )
