"""
配置适配器

检测应用程序配置问题，如缺失的环境变量、密钥配置等。
"""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base.base_adapter import BaseAdapter, HealthResult, Issue, IssueType, FixResult
from .configuration_detector import ConfigurationDetector, ConfigCheckResult


class ConfigurationAdapter(BaseAdapter):
    """配置检测适配器"""

    SERVICE_NAME = "configuration"

    # 常见配置文件路径
    CONFIG_PATHS = [
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "config.yaml",
        "config.yml",
        "config.json",
        "settings.yaml",
        "settings.json",
        "app.config",
        "application.yaml"
    ]

    def __init__(self):
        super().__init__()
        self.detector = ConfigurationDetector()
        self._config_files: List[str] = []

    def add_custom_requirement(self, template: Dict[str, Any]):
        """添加自定义配置要求"""
        self.detector.from_template(template)

    def set_config_paths(self, paths: List[str]):
        """设置要检查的配置文件路径"""
        self._config_files = paths

    def discover_config_files(self, base_dir: Optional[str] = None) -> List[str]:
        """自动发现配置文件"""
        if base_dir is None:
            base_dir = os.getcwd()

        found = []
        base = Path(base_dir)

        for config_name in self.CONFIG_PATHS:
            # 检查根目录
            path = base / config_name
            if path.exists():
                found.append(str(path))

            # 检查 config 子目录
            config_dir = base / "config"
            if config_dir.exists():
                path = config_dir / config_name.replace('.env', '').replace('.', '')
                if config_name.startswith('.env'):
                    path = config_dir / config_name
                if path.exists():
                    found.append(str(path))

        self._config_files = found
        return found

    async def health_check(self, sub_service: Optional[str] = None) -> HealthResult:
        """执行配置健康检查"""
        # 检测配置状态
        results = await self.detector.check_all(self._config_files)
        missing = self.detector.get_missing_configs(results)
        invalid = self.detector.get_invalid_configs(results)

        if not missing and not invalid:
            return HealthResult(
                service_name=self.SERVICE_NAME,
                is_healthy=True,
                message="所有必需配置项已设置",
                details={
                    "checked_count": len(results),
                    "missing_count": 0,
                    "invalid_count": 0,
                    "config_files": self._config_files
                }
            )
        elif not missing:
            return HealthResult(
                service_name=self.SERVICE_NAME,
                is_healthy=True,
                message=f"配置项存在 {len(invalid)} 个值需要验证",
                details={
                    "checked_count": len(results),
                    "missing_count": 0,
                    "invalid_count": len(invalid),
                    "config_files": self._config_files,
                    "invalid_configs": [r.requirement.name for r in invalid]
                }
            )
        else:
            return HealthResult(
                service_name=self.SERVICE_NAME,
                is_healthy=False,
                message=f"缺少 {len(missing)} 个必需配置项",
                details={
                    "checked_count": len(results),
                    "missing_count": len(missing),
                    "invalid_count": len(invalid),
                    "config_files": self._config_files,
                    "missing_configs": [r.requirement.name for r in missing]
                }
            )

    async def detect_issues(self) -> List[Issue]:
        """检测配置问题"""
        issues = []

        # 如果没有发现配置文件，尝试自动发现
        if not self._config_files:
            self.discover_config_files()

        # 执行检查
        results = await self.detector.check_all(self._config_files)

        # 生成问题
        issues = self.detector.generate_issues(results)

        return issues

    async def fix(self, issue: Issue, force: bool = False) -> FixResult:
        """修复配置问题"""
        if issue.issue_type != IssueType.CONFIG_INVALID:
            return FixResult(
                success=False,
                message=f"不支持的问题类型: {issue.issue_type}",
                error="Unsupported issue type"
            )

        # 从 raw_data 中获取配置名称
        config_name = issue.raw_data.get("config_name", "")
        if not config_name:
            return FixResult(
                success=False,
                message="无法获取配置项名称",
                error="Config name not found"
            )

        # 获取配置要求
        requirement = None
        for req in self.detector.requirements:
            if req.name == config_name:
                requirement = req
                break

        if not requirement:
            return FixResult(
                success=False,
                message=f"未找到配置项 {config_name} 的定义",
                error="Requirement not found"
            )

        return await self._generate_fix_suggestion(requirement, issue)

    async def _generate_fix_suggestion(self, requirement, issue: Issue) -> FixResult:
        """生成修复建议"""
        env_names = requirement.env_names
        env_example = f"{env_names[0]}=your_value_here"

        suggestion = f"""
# 解决方案

## 方法 1: 设置环境变量

在终端中执行:
```bash
# Linux/macOS
export {env_example}

# Windows (CMD)
set {env_example}

# Windows (PowerShell)
$env:{env_example}
```

## 方法 2: 添加到 .env 文件

在项目根目录的 `.env` 文件中添加:
```
{env_example}
```

## 方法 3: 添加到系统环境变量

**Windows:**
1. 打开系统属性 → 高级 → 环境变量
2. 新建系统/用户变量
3. 变量名: {env_names[0]}
4. 变量值: <your_value>

**Linux/macOS:**
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export {env_example}' >> ~/.bashrc
source ~/.bashrc
```
"""

        if requirement.validation_pattern:
            suggestion += f"\n\n**注意**: 该值需要符合正则模式: `{requirement.validation_pattern}`"

        return FixResult(
            success=True,
            message=f"配置项 {requirement.name} 需要手动设置",
            changes=["需要用户手动配置"],
            requires_restart=True,
            verification_output=suggestion
        )

    async def create_env_template(self, output_path: str = ".env.example"):
        """创建环境变量模板"""
        lines = ["# Auto-generated environment template", ""]

        for req in self.detector.requirements:
            if req.required:
                if req.env_names:
                    lines.append(f"# {req.description}")
                    lines.append(f"# {req.env_names[0]}=your_{req.name.lower()}_here")
                    lines.append("")
            else:
                if req.env_names:
                    lines.append(f"# {req.description} (可选)")
                    if req.default_value:
                        lines.append(f"# {req.env_names[0]}={req.default_value}")
                    else:
                        lines.append(f"# {req.env_names[0]}=")
                    lines.append("")

        content = "\n".join(lines)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return FixResult(
                success=True,
                message=f"已创建模板文件: {output_path}",
                changes=[f"创建 {output_path}"],
                requires_restart=False
            )
        except Exception as e:
            return FixResult(
                success=False,
                message=f"创建模板失败: {str(e)}",
                error=str(e)
            )
