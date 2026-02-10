"""
Auto Fix Skill 入口模块
"""

import asyncio
import json
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base.base_adapter import BaseAdapter, HealthResult, Issue, IssueType, FixResult
from .services.database import DatabaseAdapter
from .services.redis import RedisAdapter
from .services.message_queue import MessageQueueAdapter
from .services.elasticsearch import ElasticsearchAdapter
from .services.configuration import ConfigurationAdapter


class AutoFixSkill:
    """后端服务自动诊断修复Skill"""

    def __init__(self):
        self.system = platform.system()
        self.adapters: Dict[str, BaseAdapter] = {}

        # 注册所有适配器
        self._register_adapters()

    def _register_adapters(self):
        """注册所有服务适配器"""
        self.adapters = {
            "database": DatabaseAdapter(),
            "redis": RedisAdapter(),
            "message_queue": MessageQueueAdapter(),
            "elasticsearch": ElasticsearchAdapter(),
            "configuration": ConfigurationAdapter(),
        }

    def get_service_names(self) -> List[str]:
        """获取所有已注册的服务名称"""
        return list(self.adapters.keys())

    async def health_check(self, service_name: Optional[str] = None) -> Dict[str, HealthResult]:
        """执行健康检查"""
        results = {}

        if service_name:
            if service_name in self.adapters:
                results[service_name] = await self.adapters[service_name].health_check()
            else:
                # 尝试解析具体数据库类型
                for adapter in self.adapters.values():
                    if hasattr(adapter, 'get_sub_services'):
                        sub_services = adapter.get_sub_services()
                        if service_name in sub_services:
                            results[service_name] = await adapter.health_check(service_name)
                            break
        else:
            # 检查所有服务
            for name, adapter in self.adapters.items():
                results[name] = await adapter.health_check()

        return results

    async def detect_issues(self, service_name: Optional[str] = None) -> List[Issue]:
        """检测问题"""
        issues = []

        if service_name:
            if service_name in self.adapters:
                issues.extend(await self.adapters[service_name].detect_issues())
        else:
            # 检测所有服务
            for adapter in self.adapters.values():
                issues.extend(await adapter.detect_issues())

        return issues

    async def fix_issue(self, issue: Issue, force: bool = False) -> FixResult:
        """修复单个问题"""
        adapter = self.adapters.get(issue.service_name)
        if not adapter:
            return FixResult(
                success=False,
                message=f"未找到服务 {issue.service_name} 的适配器",
                error=f"Unknown service: {issue.service_name}"
            )

        return await adapter.fix(issue, force=force)

    async def auto_fix(
        self,
        service: str = "all",
        dry_run: bool = False,
        force: bool = False
    ) -> Dict[str, Any]:
        """自动执行检测和修复

        Args:
            service: 指定服务名称，'all' 表示所有服务
            dry_run: 只检测不修复
            force: 强制执行修复（跳过确认）

        Returns:
            包含检测结果和修复结果的字典
        """
        result = {
            "system": platform.system(),
            "service": service,
            "dry_run": dry_run,
            "health_checks": {},
            "issues": [],
            "fixes": [],
            "summary": "",
            "success": True
        }

        # 1. 执行健康检查
        if service == "all":
            result["health_checks"] = await self.health_check()
        else:
            result["health_checks"][service] = await self.health_check(service)

        # 2. 检测问题
        if service == "all":
            issues = await self.detect_issues()
        else:
            issues = await self.detect_issues(service)

        result["issues"] = [issue.to_dict() for issue in issues]

        if not issues:
            result["summary"] = "✓ 所有服务运行正常，未发现问题"
            return result

        # 3. 修复问题（如果需要）
        if not dry_run:
            for issue in issues:
                fix_result = await self.fix_issue(issue, force=force)
                result["fixes"].append({
                    "issue": issue.to_dict(),
                    "fix_result": fix_result.to_dict()
                })

                if not fix_result.success:
                    result["success"] = False

        # 4. 生成汇总
        fixed_count = sum(1 for f in result["fixes"] if f["fix_result"].get("success"))
        total_issues = len(issues)

        if dry_run:
            result["summary"] = f"检测到 {total_issues} 个问题（dry_run模式，未执行修复）"
        else:
            if result["success"]:
                result["summary"] = f"✓ 已修复 {fixed_count}/{total_issues} 个问题"
            else:
                result["summary"] = f"部分问题修复失败: {fixed_count}/{total_issues} 成功"

        return result

    def get_usage_info(self) -> str:
        """获取使用说明"""
        return """
## Auto Fix Skill 使用说明

### 命令格式
/claude auto_fix [服务名] [选项]

### 参数说明
- `服务名`: 可选，指定要检测的服务
  - `mysql` - MySQL 数据库
  - `postgres` - PostgreSQL 数据库
  - `mongodb` - MongoDB 数据库
  - `redis` - Redis 缓存
  - `rabbitmq` - RabbitMQ 消息队列
  - `kafka` - Kafka 消息队列
  - `elasticsearch` - Elasticsearch 搜索引擎
  - `configuration` - 应用配置检测（API密钥、环境变量等）
  - `all` - 所有服务（默认值）

### 选项
- `--dry-run`: 只检测不修复
- `--force`: 强制执行修复（跳过确认）

### 使用示例

```bash
# 检测所有后端服务
/claude auto_fix

# 检测指定服务
/claude auto_fix --service mysql

# 检测应用配置（密钥、环境变量等）
/claude auto_fix --service configuration

# 只检测不修复
/claude auto_fix --service redis --dry-run

# 强制修复
/claude auto_fix --service all --force
```

### 配置检测支持以下配置项
- API 密钥: DATA_API_KEY, IMAGE_API_KEY, API_SECRET
- 数据库: DATABASE_URL, MONGODB_URI
- Redis: REDIS_URL
- JWT: JWT_SECRET
- 许可证: LICENSE_KEY
- 服务端点: API_BASE_URL
"""


async def execute(service: str = "all", dry_run: bool = False, force: bool = False) -> Dict[str, Any]:
    """执行自动修复的主入口函数"""
    skill = AutoFixSkill()
    return await skill.auto_fix(service=service, dry_run=dry_run, force=force)
