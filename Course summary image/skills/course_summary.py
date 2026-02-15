"""
Course Summary Image Generator Skill

从网页URL或PDF文件生成美观的课程总结图片
"""

import asyncio
import httpx
import os
from typing import Optional
from datetime import datetime

# API 基础地址 - 默认为本地服务
API_BASE_URL = os.getenv("COURSE_SUMMARY_API_URL", "http://localhost:8000")


class CourseSummarySkill:
    """课程总结图片生成 Skill"""

    def __init__(self, api_url: str = None):
        self.api_url = api_url or API_BASE_URL
        self.client = httpx.AsyncClient(timeout=300.0)

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

    async def _wait_for_completion(self, task_id: str, max_wait: int = 300, poll_interval: int = 2) -> dict:
        """等待任务完成"""
        start_time = datetime.now()
        while (datetime.now() - start_time).seconds < max_wait:
            response = await self.client.get(f"{self.api_url}/api/v1/tasks/{task_id}/status")
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                if status == "completed":
                    return data
                elif status == "failed":
                    raise Exception(f"任务失败: {data.get('error_message')}")
            await asyncio.sleep(poll_interval)
        raise TimeoutError("等待任务完成超时")

    async def generate_from_web(
        self,
        url: str,
        title: str = None,
        theme: str = "light"
    ) -> dict:
        """
        从网页URL生成总结图片

        Args:
            url: 网页URL地址
            title: 图片标题（可选）
            theme: 主题风格，"light"或"dark"
        """
        # 创建任务
        task_data = {
            "source_type": "web",
            "source_url": url,
            "config": {
                "theme": theme,
                "title": title
            }
        }

        response = await self.client.post(f"{self.api_url}/api/v1/tasks", json=task_data)
        if response.status_code != 200:
            raise Exception(f"创建任务失败: {response.text}")

        task = response.json()
        task_id = task.get("id")
        print(f"任务已创建: {task_id}")

        # 等待任务完成
        result = await self._wait_for_completion(task_id)

        # 获取生成的图片
        task_response = await self.client.get(f"{self.api_url}/api/v1/tasks/{task_id}")
        task_data = task_response.json()

        images = task_data.get("images", [])
        target_theme = theme or "light"

        image_url = None
        for img in images:
            if img.get("theme") == target_theme:
                image_url = img.get("image_url") or f"{self.api_url}/api/v1/files/outputs/{os.path.basename(img.get('local_path', ''))}"
                break

        return {
            "task_id": task_id,
            "status": "completed",
            "image_url": image_url,
            "images": images,
            "content": task_data.get("content")
        }

    async def generate_from_pdf(
        self,
        file_path: str,
        title: str = None,
        theme: str = "light"
    ) -> dict:
        """
        从PDF文件生成总结图片

        Args:
            file_path: PDF文件路径
            title: 图片标题（可选，默认使用文件名）
            theme: 主题风格，"light"或"dark"
        """
        if not os.path.exists(file_path):
            raise Exception(f"文件不存在: {file_path}")

        # 上传文件
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/pdf")}
            response = await self.client.post(f"{self.api_url}/api/v1/uploads/file", files=files)

        if response.status_code != 200:
            raise Exception(f"上传文件失败: {response.text}")

        upload_result = response.json()
        filename = upload_result.get("filename")

        # 创建任务
        task_data = {
            "source_type": "pdf",
            "source_filename": filename,
            "config": {
                "theme": theme,
                "title": title
            }
        }

        task_response = await self.client.post(f"{self.api_url}/api/v1/tasks", json=task_data)
        if task_response.status_code != 200:
            raise Exception(f"创建任务失败: {task_response.text}")

        task = task_response.json()
        task_id = task.get("id")
        print(f"任务已创建: {task_id}")

        # 等待任务完成
        result = await self._wait_for_completion(task_id)

        # 获取生成的图片
        task_response = await self.client.get(f"{self.api_url}/api/v1/tasks/{task_id}")
        task_data = task_response.json()

        images = task_data.get("images", [])
        target_theme = theme or "light"

        image_url = None
        for img in images:
            if img.get("theme") == target_theme:
                image_url = img.get("image_url") or f"{self.api_url}/api/v1/files/outputs/{os.path.basename(img.get('local_path', ''))}"
                break

        return {
            "task_id": task_id,
            "status": "completed",
            "image_url": image_url,
            "images": images,
            "content": task_data.get("content")
        }

    async def list_tasks(self, limit: int = 20) -> list:
        """列出历史任务"""
        response = await self.client.get(f"{self.api_url}/api/v1/tasks", params={"limit": limit})
        if response.status_code != 200:
            raise Exception(f"获取任务列表失败: {response.text}")
        return response.json()

    async def get_task_status(self, task_id: str) -> dict:
        """查询任务状态"""
        response = await self.client.get(f"{self.api_url}/api/v1/tasks/{task_id}/status")
        if response.status_code == 404:
            raise Exception(f"任务不存在: {task_id}")
        if response.status_code != 200:
            raise Exception(f"查询失败: {response.text}")
        return response.json()

    async def get_task_detail(self, task_id: str) -> dict:
        """获取任务详情"""
        response = await self.client.get(f"{self.api_url}/api/v1/tasks/{task_id}")
        if response.status_code == 404:
            raise Exception(f"任务不存在: {task_id}")
        if response.status_code != 200:
            raise Exception(f"获取详情失败: {response.text}")
        return response.json()

    async def regenerate_image(self, task_id: str, theme: str) -> dict:
        """重新生成图片"""
        if theme not in ["light", "dark"]:
            raise Exception("主题必须为 'light' 或 'dark'")

        response = await self.client.post(f"{self.api_url}/api/v1/tasks/{task_id}/regenerate/{theme}")
        if response.status_code == 404:
            raise Exception(f"任务不存在: {task_id}")
        if response.status_code != 200:
            raise Exception(f"重新生成失败: {response.text}")

        task = response.json()
        new_task_id = task.get("id")
        print(f"重新生成任务已创建: {new_task_id}")

        # 等待任务完成
        result = await self._wait_for_completion(new_task_id)

        return {
            "original_task_id": task_id,
            "new_task_id": new_task_id,
            "status": "completed",
            "theme": theme
        }


# Skill 命令处理器
async def generate_from_web(url: str, title: str = None, theme: str = "light") -> dict:
    """从网页URL生成总结图片"""
    skill = CourseSummarySkill()
    try:
        return await skill.generate_from_web(url=url, title=title, theme=theme)
    finally:
        await skill.close()


async def generate_from_pdf(file_path: str, title: str = None, theme: str = "light") -> dict:
    """从PDF文件生成总结图片"""
    skill = CourseSummarySkill()
    try:
        return await skill.generate_from_pdf(file_path=file_path, title=title, theme=theme)
    finally:
        await skill.close()


async def list_tasks(limit: int = 20) -> list:
    """列出历史任务"""
    skill = CourseSummarySkill()
    try:
        return await skill.list_tasks(limit=limit)
    finally:
        await skill.close()


async def get_task_status(task_id: str) -> dict:
    """查询任务状态"""
    skill = CourseSummarySkill()
    try:
        return await skill.get_task_status(task_id=task_id)
    finally:
        await skill.close()


async def regenerate_image(task_id: str, theme: str) -> dict:
    """使用不同主题重新生成图片"""
    skill = CourseSummarySkill()
    try:
        return await skill.regenerate_image(task_id=task_id, theme=theme)
    finally:
        await skill.close()
