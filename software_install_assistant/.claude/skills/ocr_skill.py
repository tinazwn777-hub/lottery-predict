"""
OCR Skill - 图片识别问题分析

识别用户上传的图片中的错误信息，并分类为相应的问题类型。
"""

import json
import base64
from pathlib import Path
from typing import Any, Dict, Optional

from ..skills.auto_fix import AutoFixSkill
from ..skills.services.ocr import OcrService, OcrResult
from ..skills.base.base_adapter import Issue, IssueType


class OcrSkill:
    """OCR 图片识别 Skill"""

    def __init__(self):
        self.ocr_service = OcrService()

    def get_issue_type_from_category(self, category: str) -> IssueType:
        """将 OCR 类别映射到 IssueType"""
        category_mapping = {
            "SYNTAX_ERROR": IssueType.CONFIG_INVALID,
            "RUNTIME_ERROR": IssueType.UNKNOWN,
            "CONNECTION_ERROR": IssueType.CONNECTIVITY_FAILED,
            "CONFIGURATION_ERROR": IssueType.CONFIG_INVALID,
            "PERMISSION_ERROR": IssueType.PERMISSION_DENIED,
            "MEMORY_ERROR": IssueType.STORAGE_FULL,
            "DISK_ERROR": IssueType.STORAGE_FULL,
            "TIMEOUT_ERROR": IssueType.CONNECTIVITY_FAILED,
            "IMPORT_ERROR": IssueType.DEPENDENCY_MISSING,
            "DEPENDENCY_ERROR": IssueType.DEPENDENCY_MISSING,
            "SERVICE_ERROR": IssueType.SERVICE_NOT_RUNNING,
            "DATABASE_ERROR": IssueType.CONNECTIVITY_FAILED,
        }
        return category_mapping.get(category, IssueType.UNKNOWN)

    def create_issue_from_ocr(self, ocr_result: OcrResult, image_path: str = "") -> Issue:
        """根据 OCR 结果创建 Issue"""
        # 选择最可能的类别
        primary_category = ocr_result.categories[0] if ocr_result.categories else "UNKNOWN"

        issue_type = self.get_issue_type_from_category(primary_category)

        return Issue(
            service_name="ocr_recognized",
            issue_type=issue_type,
            title=f"识别到的问题: {primary_category.replace('_', ' ')}",
            description=ocr_result.text[:500] if ocr_result.text else "未能识别图片内容",
            severity=self._estimate_severity(ocr_result),
            detection_method="ocr_image_recognition",
            suggestion="\n".join(ocr_result.suggested_actions) if ocr_result.suggested_actions else "请查看识别到的文字内容",
            affected_component=primary_category,
            raw_data={
                "image_path": image_path,
                "ocr_confidence": ocr_result.confidence,
                "all_categories": ocr_result.categories,
                "keywords": ocr_result.keywords,
                "full_text": ocr_result.text
            }
        )

    def _estimate_severity(self, ocr_result: OcrResult) -> str:
        """估算问题严重程度"""
        text = ocr_result.text.lower()

        # 基于关键词判断严重程度
        critical_keywords = ["fatal", "critical", "failed", "error"]
        high_keywords = ["warning", "cannot", "unable", "refused"]
        medium_keywords = ["deprecated", "notice", "info"]

        for keyword in critical_keywords:
            if keyword in text:
                return "critical"

        for keyword in high_keywords:
            if keyword in text:
                return "high"

        for keyword in medium_keywords:
            if keyword in text:
                return "medium"

        return "medium"

    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """分析图片并生成结果

        Args:
            image_path: 图片文件路径

        Returns:
            包含分析结果的字典
        """
        # 执行 OCR
        result = self.ocr_service.analyze_screenshot(image_path)

        if result["success"]:
            # 创建 Issue
            ocr_result = OcrResult(
                success=True,
                text=result["recognized_text"],
                confidence=result["confidence"],
                categories=result["error_categories"],
                keywords=result["keywords"],
                suggested_actions=result["suggested_actions"]
            )
            issue = self.create_issue_from_ocr(ocr_result, image_path)

            return {
                "success": True,
                "analysis": {
                    "issue": issue.to_dict(),
                    "ocr_result": {
                        "text": result["recognized_text"],
                        "confidence": result["confidence"],
                        "categories": result["error_categories"],
                        "keywords": result["keywords"]
                    }
                }
            }
        else:
            return {
                "success": False,
                "error": result.get("error_details", "OCR 识别失败"),
                "suggestions": result.get("suggested_actions", [])
            }

    async def analyze_base64_image(self, base64_data: str) -> Dict[str, Any]:
        """分析 Base64 编码的图片

        Args:
            base64_data: Base64 编码的图片数据

        Returns:
            包含分析结果的字典
        """
        ocr_result = self.ocr_service.recognize_base64(base64_data)

        if ocr_result.success:
            issue = self.create_issue_from_ocr(ocr_result, "[base64]")

            return {
                "success": True,
                "analysis": {
                    "issue": issue.to_dict(),
                    "ocr_result": {
                        "text": ocr_result.text,
                        "confidence": ocr_result.confidence,
                        "categories": ocr_result.categories,
                        "keywords": ocr_result.keywords
                    }
                }
            }
        else:
            return {
                "success": False,
                "error": ocr_result.error or "OCR 识别失败",
                "suggestions": ocr_result.suggested_actions
            }

    def get_usage_info(self) -> str:
        """获取使用说明"""
        return """
## OCR 图片识别 Skill 使用说明

### 功能
识别图片中的错误信息，自动分类问题类型并提供解决建议。

### 使用方式

#### 1. 识别图片文件
```bash
# 识别本地图片
/claude ocr --file <图片路径>

# 示例
/claude ocr --file ./error_screenshot.png
```

#### 2. 识别截图（粘贴图片）
直接在对话中粘贴图片，系统会自动识别。

#### 3. Base64 编码
```json
{
  "command": "ocr",
  "data": "<base64编码的图片数据>"
}
```

### 识别的问题类型
- **SYNTAX_ERROR**: 语法错误
- **RUNTIME_ERROR**: 运行时错误
- **CONNECTION_ERROR**: 连接错误
- **CONFIGURATION_ERROR**: 配置错误
- **PERMISSION_ERROR**: 权限错误
- **MEMORY_ERROR**: 内存错误
- **DISK_ERROR**: 磁盘错误
- **TIMEOUT_ERROR**: 超时错误
- **IMPORT_ERROR**: 导入错误
- **DEPENDENCY_ERROR**: 依赖错误
- **SERVICE_ERROR**: 服务错误
- **DATABASE_ERROR**: 数据库错误
"""


# 便捷函数
async def analyze_image(image_path: str) -> Dict[str, Any]:
    """分析图片（便捷函数）"""
    skill = OcrSkill()
    return await skill.analyze_image(image_path)


async def analyze_base64(data: str) -> Dict[str, Any]:
    """分析 Base64 图片（便捷函数）"""
    skill = OcrSkill()
    return await skill.analyze_base64_image(data)
