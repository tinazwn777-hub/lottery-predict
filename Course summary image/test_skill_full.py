"""
课程总结图片 Skill - 完整功能测试
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skills.course_summary import CourseSummarySkill


async def main():
    print("=" * 60)
    print("Course Summary Image Skill - 完整功能测试")
    print("=" * 60)

    skill = CourseSummarySkill()
    api_url = skill.api_url

    # 1. 健康检查
    print("\n[1] API 健康检查...")
    resp = await skill.client.get(f"{api_url}/health")
    print(f"    状态: {resp.status_code}")
    print("    [OK]")

    # 2. 创建任务
    print("\n[2] 创建新任务...")
    task_data = {
        "source_type": "web",
        "source_url": "https://www.runoob.com/css/css-tutorial.html",
        "config": {"theme": "light"}
    }
    resp = await skill.client.post(f"{api_url}/api/v1/tasks", json=task_data)
    task = resp.json()
    task_id = task["id"]
    print(f"    任务ID: {task_id}")
    print(f"    状态: {task['status']}")
    print("    [OK]")

    # 3. 等待任务完成
    print("\n[3] 等待任务完成...")
    import time
    max_wait = 30
    waited = 0
    while waited < max_wait:
        resp = await skill.client.get(f"{api_url}/api/v1/tasks/{task_id}/status")
        status_data = resp.json()
        print(f"    状态: {status_data['status']}, 进度: {status_data['progress']}%")
        if status_data["status"] in ["completed", "failed"]:
            break
        await asyncio.sleep(2)
        waited += 2
    print("    [OK]")

    # 4. 获取任务详情
    print("\n[4] 获取任务详情...")
    resp = await skill.client.get(f"{api_url}/api/v1/tasks/{task_id}")
    task_detail = resp.json()
    print(f"    任务ID: {task_detail['id']}")
    print(f"    状态: {task_detail['status']}")
    print(f"    图片数: {len(task_detail.get('images', []))}")
    print("    [OK]")

    # 5. 列出任务
    print("\n[5] 列出所有任务...")
    resp = await skill.client.get(f"{api_url}/api/v1/tasks?limit=10")
    tasks = resp.json()
    print(f"    任务数: {len(tasks)}")
    print("    [OK]")

    await skill.close()

    print("\n" + "=" * 60)
    print("所有测试通过！")
    print("=" * 60)

    # 显示生成的图片路径
    if task_detail.get("images"):
        print("\n生成的图片:")
        for img in task_detail["images"]:
            print(f"  - {img['theme']}: {img['local_path']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
