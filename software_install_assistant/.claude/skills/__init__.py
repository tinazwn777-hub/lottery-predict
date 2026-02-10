"""
Auto Fix Skill - 后端服务自动诊断修复

帮助 AI 编程小白自动检测并修复后端服务的协同配置问题。
"""

from .auto_fix import AutoFixSkill, execute
from .ocr_skill import OcrSkill, analyze_image, analyze_base64

__all__ = ["AutoFixSkill", "execute", "OcrSkill", "analyze_image", "analyze_base64"]
