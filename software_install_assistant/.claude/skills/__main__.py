#!/usr/bin/env python3
"""
Auto Fix Skill CLI Entry Point

用于命令行测试的入口点
"""

import asyncio
import json
import sys

# 添加 .claude 到路径
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from .skills.auto_fix import AutoFixSkill


async def main():
    """主函数"""
    skill = AutoFixSkill()

    # 解析命令行参数
    service = "all"
    dry_run = False
    force = False

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg in ["--dry-run", "-d"]:
            dry_run = True
        elif arg in ["--force", "-f"]:
            force = True
        elif arg.startswith("--service="):
            service = arg.split("=", 1)[1]
        elif arg.startswith("--"):
            continue
        else:
            service = arg

    # 执行自动修复
    print("开始执行后端服务诊断...")
    print(f"服务: {service}")
    print(f"干运行模式: {dry_run}")
    print(f"强制修复: {force}")
    print("-" * 50)

    result = await skill.auto_fix(service=service, dry_run=dry_run, force=force)

    # 输出结果
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
