"""
连通性检测器

检测网络连通性和服务可达性。
"""

import asyncio
import socket
from typing import Any, Dict, List, Optional


class ConnectivityDetector:
    """连通性检测器"""

    def __init__(self):
        self.system = self._detect_system()

    def _detect_system(self) -> str:
        """检测当前操作系统"""
        import platform
        return platform.system()

    async def check_connectivity(
        self,
        host: str,
        port: int,
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """检查到指定主机的连通性"""
        result = {
            "host": host,
            "port": port,
            "reachable": False,
            "latency_ms": 0,
            "error": None
        }

        try:
            # 尝试建立连接
            start_time = asyncio.get_event_loop().time()
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            latency = (asyncio.get_event_loop().time() - start_time) * 1000

            writer.close()
            await writer.wait_closed()

            result["reachable"] = True
            result["latency_ms"] = round(latency, 2)

        except socket.timeout:
            result["error"] = "连接超时"
        except ConnectionRefusedError:
            result["error"] = "连接被拒绝"
        except socket.gaierror:
            result["error"] = f"无法解析主机: {host}"
        except OSError as e:
            result["error"] = str(e)
        except Exception as e:
            result["error"] = f"未知错误: {str(e)}"

        return result

    async def check_http_endpoint(
        self,
        url: str,
        timeout: float = 10.0,
        expected_status: Optional[int] = None
    ) -> Dict[str, Any]:
        """检查 HTTP 端点可达性"""
        result = {
            "url": url,
            "reachable": False,
            "status_code": None,
            "response_time_ms": 0,
            "content": None,
            "error": None
        }

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    latency = (asyncio.get_event_loop().time() - start_time) * 1000

                    result["reachable"] = True
                    result["status_code"] = response.status
                    result["response_time_ms"] = round(latency, 2)

                    # 检查状态码
                    if expected_status and response.status != expected_status:
                        result["error"] = f"期望状态码 {expected_status}，实际 {response.status}"

                    # 读取少量内容用于验证
                    if response.status < 400:
                        content = await response.read()
                        result["content"] = content[:1024].decode('utf-8', errors='ignore')

        except asyncio.TimeoutError:
            result["error"] = "请求超时"
        except aiohttp.ClientError as e:
            result["error"] = str(e)
        except Exception as e:
            result["error"] = f"未知错误: {str(e)}"

        return result

    async def check_tcp_port_range(
        self,
        host: str,
        ports: List[int],
        timeout: float = 2.0
    ) -> Dict[int, Dict[str, Any]]:
        """检查多个端口的连通性"""
        results = {}

        # 并发检查所有端口
        tasks = []
        for port in ports:
            tasks.append(self.check_connectivity(host, port, timeout))

        if tasks:
            port_results = await asyncio.gather(*tasks)
            for i, port in enumerate(ports):
                results[port] = port_results[i]

        return results

    async def ping_host(self, host: str, count: int = 3) -> Dict[str, Any]:
        """Ping 主机检查可达性"""
        result = {
            "host": host,
            "reachable": False,
            "packets_sent": count,
            "packets_received": 0,
            "min_latency_ms": 0,
            "avg_latency_ms": 0,
            "max_latency_ms": 0,
            "error": None
        }

        try:
            if self.system == "Windows":
                cmd = f"ping -n {count} {host}"
            else:
                cmd = f"ping -c {count} {host}"

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode()

            # 解析 ping 输出
            if "bytes from" in output or "回复自" in output:
                result["reachable"] = True

                # 尝试提取延迟信息
                latencies = self._extract_latencies(output)
                if latencies:
                    result["packets_received"] = len(latencies)
                    result["min_latency_ms"] = min(latencies)
                    result["max_latency_ms"] = max(latencies)
                    result["avg_latency_ms"] = round(sum(latencies) / len(latencies), 2)

        except Exception as e:
            result["error"] = str(e)

        return result

    def _extract_latencies(self, ping_output: str) -> List[float]:
        """从 ping 输出中提取延迟值"""
        latencies = []

        # Windows 格式: "bytes=32 time<1ms TTL=128"
        # Linux 格式: "64 bytes from host: icmp_seq=1 ttl=64 time=0.042 ms"
        patterns = [
            r'time[=<]?([\d.]+)\s*ms',
            r'(\d+)\s*ms'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, ping_output, re.IGNORECASE)
            for match in matches:
                try:
                    latencies.append(float(match))
                except ValueError:
                    continue

        return latencies

    async def dns_lookup(self, hostname: str) -> Dict[str, Any]:
        """DNS 解析检查"""
        result = {
            "hostname": hostname,
            "resolved": False,
            "ip_addresses": [],
            "error": None
        }

        try:
            info = socket.getaddrinfo(hostname, None)
            result["ip_addresses"] = list(set([addr[4][0] for addr in info]))
            result["resolved"] = len(result["ip_addresses"]) > 0

        except socket.gaierror as e:
            result["error"] = f"DNS 解析失败: {str(e)}"
        except Exception as e:
            result["error"] = str(e)

        return result

    async def check_localhost_services(self, services: Dict[str, int]) -> Dict[str, Dict[str, Any]]:
        """检查本地服务连通性"""
        results = {}

        for service_name, port in services.items():
            results[service_name] = await self.check_connectivity("127.0.0.1", port)

        return results
