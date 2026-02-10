"""
命令执行封装

提供跨平台的命令执行功能。
"""

import asyncio
import os
import platform
import shlex
import signal
import subprocess
from typing import Any, Dict, List, Optional, Tuple


class CommandRunner:
    """命令执行器"""

    def __init__(self):
        self.system = platform.system()
        self._last_result: Optional[Dict[str, Any]] = None

    def run(
        self,
        command: str,
        capture_output: bool = True,
        timeout: float = 30.0,
        shell: bool = True,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """同步执行命令

        Args:
            command: 要执行的命令
            capture_output: 是否捕获输出
            timeout: 超时时间（秒）
            shell: 是否使用 shell 执行
            env: 环境变量
            cwd: 工作目录

        Returns:
            包含 returncode, stdout, stderr 的字典
        """
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                env=self._merge_env(env),
                cwd=cwd
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out",
                "command": command,
                "error": "timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": command,
                "error": str(e)
            }

    async def run_async(
        self,
        command: str,
        capture_output: bool = True,
        timeout: float = 30.0,
        shell: bool = True,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """异步执行命令

        Args:
            command: 要执行的命令
            capture_output: 是否捕获输出
            timeout: 超时时间（秒）
            shell: 是否使用 shell 执行
            env: 环境变量
            cwd: 工作目录

        Returns:
            包含 returncode, stdout, stderr 的字典
        """
        try:
            # 创建子进程
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE if capture_output else asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE if capture_output else asyncio.subprocess.DEVNULL,
                env=self._merge_env(env),
                cwd=cwd
            )

            # 等待完成（带超时）
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                returncode = proc.returncode
                return {
                    "success": returncode == 0,
                    "returncode": returncode,
                    "stdout": stdout.decode('utf-8', errors='replace'),
                    "stderr": stderr.decode('utf-8', errors='replace'),
                    "command": command
                }
            except asyncio.TimeoutExpired:
                # 超时，尝试终止进程
                proc.terminate()
                try:
                    await proc.wait()
                except Exception:
                    pass
                return {
                    "success": False,
                    "returncode": -1,
                    "stdout": "",
                    "stderr": "Command timed out",
                    "command": command,
                    "error": "timeout"
                }

        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": command,
                "error": str(e)
            }

    def run_with_sudo(
        self,
        command: str,
        capture_output: bool = True,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """使用 sudo 执行命令（仅 Linux/macOS）"""
        if self.system == "Windows":
            # Windows 使用管理员权限运行
            return self.run(command, capture_output, timeout)

        # Linux/macOS 使用 sudo
        if self.system == "Darwin":
            sudo_cmd = f"sudo -S {command}"
        else:
            sudo_cmd = f"sudo -S {command}"

        return self.run(sudo_cmd, capture_output, timeout)

    def get_service_command(self, service_name: str, action: str) -> str:
        """获取服务管理命令

        Args:
            service_name: 服务名称
            action: 操作类型 (start, stop, restart, status)

        Returns:
            完整的命令字符串
        """
        if self.system == "Windows":
            if action == "start":
                return f'net start "{service_name}"'
            elif action == "stop":
                return f'net stop "{service_name}"'
            elif action == "restart":
                return f'net stop "{service_name}" && net start "{service_name}"'
            elif action == "status":
                return f'powershell -Command "(Get-Service -Name \\"{service_name}\\" -ErrorAction SilentlyContinue).Status"'

        elif self.system == "Darwin":
            if action == "start":
                return f"brew services start {service_name}"
            elif action == "stop":
                return f"brew services stop {service_name}"
            elif action == "restart":
                return f"brew services restart {service_name}"
            elif action == "status":
                return f"brew services list | grep {service_name}"

        else:  # Linux
            if action == "start":
                return f"sudo systemctl start {service_name}"
            elif action == "stop":
                return f"sudo systemctl stop {service_name}"
            elif action == "restart":
                return f"sudo systemctl restart {service_name}"
            elif action == "status":
                return f"sudo systemctl is-active {service_name}"

        return ""

    def _merge_env(self, env: Optional[Dict[str, str]] = None) -> Optional[Dict[str, str]]:
        """合并环境变量"""
        if env is None:
            return None

        # 获取当前环境变量
        current_env = os.environ.copy()

        # 合并传入的环境变量
        for key, value in env.items():
            current_env[key] = value

        return current_env

    def escape_shell_args(self, args: List[str]) -> str:
        """转义命令行参数（用于安全执行）"""
        return ' '.join(shlex.quote(arg) for arg in args)

    def check_command_available(self, command: str) -> bool:
        """检查命令是否可用"""
        if self.system == "Windows":
            cmd = f"where {command}"
        else:
            cmd = f"which {command}"

        result = self.run(cmd, capture_output=True)
        return result["success"]
