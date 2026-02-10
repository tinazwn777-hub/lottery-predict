"""
进程检测器

检测进程运行状态和资源使用情况。
"""

import asyncio
import platform
from typing import Any, Dict, List, Optional


class ProcessDetector:
    """进程检测器"""

    def __init__(self):
        self.system = platform.system()

    async def check_process_running(self, process_names: List[str]) -> Optional[str]:
        """检查进程是否正在运行"""
        try:
            if self.system == "Windows":
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
                name_lower = name.lower()
                if name_lower in output:
                    # 排除 grep 进程本身
                    if 'grep' not in output[max(0, output.find(name_lower) - 10):output.find(name_lower) + len(name_lower) + 10]:
                        return name

            return None

        except Exception:
            return None

    async def get_process_info(self, process_name: str) -> Dict[str, Any]:
        """获取进程详细信息"""
        info = {
            "name": process_name,
            "running": False,
            "pid": None,
            "cpu_percent": 0,
            "memory_percent": 0,
            "command_line": ""
        }

        try:
            if self.system == "Windows":
                info.update(await self._get_windows_process_info(process_name))
            else:
                info.update(await self._get_unix_process_info(process_name))
        except Exception:
            pass

        return info

    async def _get_windows_process_info(self, process_name: str) -> Dict[str, Any]:
        """获取 Windows 进程信息"""
        result = {}

        try:
            cmd = f'powershell -Command "Get-Process -Name "{process_name}" -ErrorAction SilentlyContinue | Select-Object Id,CPU,PM,WS,CommandLine | ConvertTo-Json"'
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            if proc.returncode == 0 and stdout:
                import json
                data = json.loads(stdout.decode())
                if data:
                    result["running"] = True
                    result["pid"] = data.get("Id")
                    result["command_line"] = data.get("CommandLine", "")
                    # 注意: Windows PowerShell 返回的 CPU 单位可能不同
                    result["cpu_percent"] = 0  # 需要额外处理
                    result["memory_percent"] = 0  # 需要额外处理

        except Exception:
            pass

        return result

    async def _get_unix_process_info(self, process_name: str) -> Dict[str, Any]:
        """获取 Unix/Linux/macOS 进程信息"""
        result = {}

        try:
            # 使用 ps 命令获取进程信息
            cmd = f'ps aux | grep "{process_name}" | grep -v grep'
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            if stdout:
                lines = stdout.decode().strip().split('\n')
                if lines and lines[0]:
                    parts = lines[0].split()
                    if len(parts) >= 11:
                        result["running"] = True
                        result["pid"] = parts[1]
                        result["cpu_percent"] = float(parts[2])
                        result["memory_percent"] = float(parts[3])
                        result["command_line"] = ' '.join(parts[10:])

        except Exception:
            pass

        return result

    async def get_all_service_processes(self, service_names: List[str]) -> List[Dict[str, Any]]:
        """获取所有相关服务的进程信息"""
        processes = []

        for service in service_names:
            process = await self.get_process_info(service)
            if process.get("running"):
                processes.append(process)

        return processes

    async def kill_process(self, pid: int, force: bool = False) -> bool:
        """终止进程"""
        try:
            if self.system == "Windows":
                sig = "/F" if force else ""
                cmd = f"taskkill {sig} /PID {pid}"
            else:
                sig = " -9" if force else ""
                cmd = f"kill{sig} {pid}"

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0

        except Exception:
            return False

    async def wait_for_process_start(self, process_names: List[str], timeout: float = 30.0) -> Optional[str]:
        """等待进程启动"""
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            process = await self.check_process_running(process_names)
            if process:
                return process
            await asyncio.sleep(1)

        return None

    async def wait_for_process_stop(self, process_names: List[str], timeout: float = 30.0) -> bool:
        """等待进程停止"""
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            process = await self.check_process_running(process_names)
            if not process:
                return True
            await asyncio.sleep(1)

        return False
