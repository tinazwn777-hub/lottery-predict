"""
测试课程总结图片 Skill - 完整功能测试
使用真实后端 API 验证（跳过需要 Playwright 的网页抓取）
"""

import asyncio
import sys
import os

# 添加 skills 目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skills.course_summary import CourseSummarySkill


async def test_skill():
    print("=" * 60)
    print("Course Summary Image Skill - 完整功能测试")
    print("=" * 60)

    skill = CourseSummarySkill()
    print(f"\n[1] API URL: {skill.api_url}")

    # 测试 1: API 健康检查
    print("\n[2] 测试 API 健康检查...")
    try:
        response = await skill.client.get(f"{skill.api_url}/health")
        print(f"    Status: {response.status_code}")
        print(f"    Response: {response.json()}")
        print("    [OK] API 健康检查通过")
    except Exception as e:
        print(f"    [ERROR] {e}")
        return False

    # 测试 2: 创建任务（会失败因为需要 Playwright，但验证 API 调用逻辑）
    print("\n[3] 测试创建任务 API...")
    try:
        task_data = {
            "source_type": "web",
            "source_url": "https://example.com",
            "config": {"theme": "light"}
        }
        response = await skill.client.post(f"{skill.api_url}/api/v1/tasks", json=task_data)
        print(f"    Status: {response.status_code}")
        if response.status_code in [200, 202]:
            print(f"    Task ID: {response.json().get('id')}")
            print("    [OK] 创建任务 API 调用成功")
        else:
            print(f"    Response: {response.text}")
    except Exception as e:
        print(f"    [ERROR] {e}")

    # 测试 3: 列出任务
    print("\n[4] 测试列出任务...")
    try:
        response = await skill.client.get(f"{skill.api_url}/api/v1/tasks")
        print(f"    Status: {response.status_code}")
        tasks = response.json()
        print(f"    任务数量: {len(tasks)}")
        print("    [OK] 列出任务 API 调用成功")
    except Exception as e:
        print(f"    [ERROR] {e}")

    # 测试 4: 获取单个任务详情
    print("\n[5] 测试获取任务详情...")
    if tasks:
        task_id = tasks[0].get('id')
        try:
            response = await skill.client.get(f"{skill.api_url}/api/v1/tasks/{task_id}")
            print(f"    Status: {response.status_code}")
            print(f"    Task: {response.json().get('id')}")
            print("    [OK] 获取任务详情 API 调用成功")
        except Exception as e:
            print(f"    [ERROR] {e}")

    await skill.close()

    print("\n" + "=" * 60)
    print("Skill API 调用测试完成")
    print("=" * 60)
    print("\n注意: 完整功能需要:")
    print("  1. 安装 Playwright: python -m playwright install chromium")
    print("  2. 或使用 VPN 解决网络问题")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_skill())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
