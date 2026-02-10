"""
健康检查通用逻辑

提供通用的健康检查方法和工具函数。
"""

import asyncio
import json
import re
import socket
from typing import Any, Dict, List, Optional, Tuple

from .base_adapter import HealthResult, Issue, IssueType


class HealthChecker:
    """健康检查工具类"""

    @staticmethod
    async def check_port_listening(host: str, port: int, timeout: float = 2.0) -> bool:
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

    @staticmethod
    def check_port_listening_sync(host: str, port: int, timeout: float = 2.0) -> bool:
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

    @staticmethod
    async def check_process_running(process_names: List[str]) -> Optional[str]:
        """检查进程是否正在运行"""
        import platform

        if platform.system() == "Windows":
            cmd = 'tasklist /NH /FO CSV'
        else:
            cmd = 'ps aux'

        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode().lower()

        for name in process_names:
            # 排除 grep 进程本身
            if name.lower() in output and 'grep' not in output:
                return name
        return None

    @staticmethod
    async def get_process_pids(process_name: str) -> List[int]:
        """获取进程的 PID 列表"""
        import platform

        pids = []
        try:
            if platform.system() == "Windows":
                cmd = f'powershell -Command "Get-Process -Name {process_name} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"'
            else:
                cmd = f"pgrep -x {process_name}"

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            for line in stdout.decode().strip().split('\n'):
                line = line.strip()
                if line:
                    try:
                        pids.append(int(line))
                    except ValueError:
                        continue
        except Exception:
            pass

        return pids

    @staticmethod
    async def check_service_status(service_name: str) -> Tuple[bool, str]:
        """检查系统服务状态"""
        import platform

        system = platform.system()

        if system == "Linux":
            # 使用 systemctl 检查服务状态
            cmd = f"systemctl is-active {service_name}"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            status = stdout.decode().strip()
            return status == "active", status

        elif system == "Windows":
            cmd = f'powershell -Command "(Get-Service -Name {service_name} -ErrorAction SilentlyContinue).Status"'
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            status = stdout.decode().strip()
            return status == "Running", status

        elif system == "Darwin":
            cmd = f"launchctl list | grep {service_name}"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            return bool(stdout.decode().strip()), "unknown"

        return False, "unknown"

    @staticmethod
    async def check_disk_usage(mount_point: str = "/", warning_threshold: int = 80, critical_threshold: int = 90) -> Dict[str, Any]:
        """检查磁盘使用情况"""
        import platform

        result = {
            "mount_point": mount_point,
            "warning_threshold": warning_threshold,
            "critical_threshold": critical_threshold,
            "status": "ok",
            "usage_percent": 0
        }

        try:
            if platform.system() == "Windows":
                cmd = f'powershell -Command "Get-Volume -ErrorAction SilentlyContinue | Where-Object {{$_.DriveLetter -eq \\"{mount_point[:1]}\\"}} | Select-Object Size,SizeRemaining"'
            else:
                cmd = f"df -h {mount_point} | tail -1"

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode()

            if platform.system() == "Windows":
                # 解析 Windows 输出
                lines = output.strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 2:
                        total = int(parts[0].replace(',', ''))
                        used = total - int(parts[1].replace(',', ''))
                        result["usage_percent"] = round(used / total * 100, 1)
            else:
                # 解析 Linux df 输出
                parts = output.split()
                if len(parts) >= 5:
                    usage = parts[4].rstrip('%')
                    result["usage_percent"] = float(usage)

        except Exception:
            pass

        # 确定状态
        if result["usage_percent"] >= critical_threshold:
            result["status"] = "critical"
        elif result["usage_percent"] >= warning_threshold:
            result["status"] = "warning"

        return result

    @staticmethod
    def parse_ini_config(content: str) -> Dict[str, Dict[str, str]]:
        """解析 INI 格式配置文件"""
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

    @staticmethod
    def parse_yaml_config(content: str) -> Dict[str, Any]:
        """解析 YAML 格式配置文件"""
        import yaml
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError:
            return {}

    @staticmethod
    def parse_json_config(content: str) -> Dict[str, Any]:
        """解析 JSON 格式配置文件"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def parse_env_config(content: str) -> Dict[str, str]:
        """解析 .env 格式配置文件"""
        config = {}

        for line in content.splitlines():
            line = line.strip()

            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue

            # 解析 KEY=VALUE 格式
            if '=' in line:
                key, value = line.split('=', 1)
                # 处理带引号的值
                value = value.strip().strip('"\'')
                config[key.strip()] = value

        return config

    @staticmethod
    def extract_tcp_ports(output: str) -> List[int]:
        """从命令输出中提取监听的 TCP 端口"""
        ports = []
        # netstat -tlnp 格式: proto recv-q send-q local-address foreign-address state
        # 或: tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN
        pattern = r'(?:0\.0\.0\.0:|127\.0\.0\.1:|:)(?:\*|:)(\d+)'

        for match in re.finditer(pattern, output):
            try:
                port = int(match.group(1))
                if 1 <= port <= 65535:
                    ports.append(port)
            except ValueError:
                continue

        return list(set(ports))  # 去重

    @staticmethod
    def extract_listening_info(output: str) -> List[Dict[str, str]]:
        """从命令输出中提取监听信息"""
        info = []
        # 简单匹配: proto ... local-address ... state LISTEN
        pattern = r'(tcp|udp)\s+\d+\s+\d+\s+([\d\.:]+)\s+([\d\.:*]+)\s+(LISTEN|\*)'

        for match in re.finditer(pattern, output, re.IGNORECASE):
            info.append({
                "protocol": match.group(1),
                "local_address": match.group(2),
                "state": match.group(4)
            })

        return info
