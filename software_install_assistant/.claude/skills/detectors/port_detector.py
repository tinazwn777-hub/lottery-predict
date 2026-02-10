"""
端口检测器

检测端口监听状态和端口冲突问题。
"""

import asyncio
import re
import socket
from typing import Any, Dict, List, Optional

from ..base.base_adapter import Issue, IssueType


class PortDetector:
    """端口检测器"""

    def __init__(self):
        self.system = self._detect_system()

    def _detect_system(self) -> str:
        """检测当前操作系统"""
        import platform
        return platform.system()

    async def check_port_listening(self, host: str, port: int, timeout: float = 2.0) -> bool:
        """检查端口是否正在监听"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            return False

    def check_port_listening_sync(self, host: str, port: int, timeout: float = 2.0) -> bool:
        """同步检查端口是否正在监听"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            result = sock.connect_ex((host, port))
            return result == 0
        except socket.timeout:
            return False
        finally:
            sock.close()

    async def get_listening_ports(self) -> List[int]:
        """获取当前系统所有监听的端口"""
        ports = []

        try:
            if self.system == "Linux":
                cmd = "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null"
            elif self.system == "Windows":
                cmd = 'netstat -an | findstr "LISTENING"'
            elif self.system == "Darwin":
                cmd = "netstat -an | grep LISTEN"
            else:
                return ports

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            output = stdout.decode()
            ports = self._extract_ports(output)

        except Exception:
            pass

        return list(set(ports))  # 去重

    def _extract_ports(self, output: str) -> List[int]:
        """从命令输出中提取端口号"""
        ports = []
        # 匹配常见的端口格式
        patterns = [
            r'(?:0\.0\.0\.0:|127\.0\.0\.1:|:)(?:\*|:)(\d+)',
            r'LISTEN\s+.*?:(\d+)',
            r' (\d+)\s*$'  # Windows 格式
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, output):
                try:
                    port = int(match.group(1))
                    if 1 <= port <= 65535:
                        ports.append(port)
                except (ValueError, IndexError):
                    continue

        return ports

    async def check_port_conflict(self, port: int, expected_process: Optional[str] = None) -> Dict[str, Any]:
        """检查端口冲突"""
        result = {
            "port": port,
            "is_listening": False,
            "conflict": False,
            "process": None,
            "message": ""
        }

        # 检查端口是否被监听
        is_listening = await self.check_port_listening("127.0.0.1", port)
        result["is_listening"] = is_listening

        if is_listening:
            # 获取占用端口的进程
            process = await self._get_process_using_port(port)
            result["process"] = process

            if expected_process and process:
                # 检查是否是预期的进程
                if expected_process.lower() not in process.lower():
                    result["conflict"] = True
                    result["message"] = f"端口 {port} 被 {process} 占用，而非预期的 {expected_process}"
                else:
                    result["message"] = f"端口 {port} 正常被 {process} 占用"
            else:
                result["message"] = f"端口 {port} 已被占用"

        return result

    async def _get_process_using_port(self, port: int) -> Optional[str]:
        """获取占用指定端口的进程名称"""
        try:
            if self.system == "Linux":
                cmd = f"lsof -i :{port} -t 2>/dev/null | xargs -I {{}} ps -p {{}} -o comm= 2>/dev/null"
            elif self.system == "Windows":
                cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"'
            elif self.system == "Darwin":
                cmd = f"lsof -i :{port} -t 2>/dev/null | xargs -I {{}} ps -p {{}} -o comm= 2>/dev/null"
            else:
                return None

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            process = stdout.decode().strip()
            return process if process else None

        except Exception:
            return None

    def detect_port_issues(
        self,
        service_name: str,
        expected_ports: List[int],
        expected_process: Optional[str] = None
    ) -> List[Issue]:
        """检测端口相关问题"""
        issues = []

        for port in expected_ports:
            # 简化处理：实际实现需要异步检查
            pass

        return issues
