"""
Course Summary Image Generator Skill

从网页URL或PDF文件生成美观的课程总结图片
"""

from .course_summary import (
    generate_from_web,
    generate_from_pdf,
    list_tasks,
    get_task_status,
    regenerate_image,
    CourseSummarySkill
)

__all__ = [
    "generate_from_web",
    "generate_from_pdf",
    "list_tasks",
    "get_task_status",
    "regenerate_image",
    "CourseSummarySkill"
]
