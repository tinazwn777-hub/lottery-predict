"""
OCR Service - 图片文字识别服务

用于识别图片中的错误信息、日志内容等。
"""

import base64
import io
import os
import re
import subprocess
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ErrorCategory(Enum):
    """错误类别枚举"""
    SYNTAX_ERROR = auto()         # 语法错误
    RUNTIME_ERROR = auto()         # 运行时错误
    CONNECTION_ERROR = auto()      # 连接错误
    CONFIGURATION_ERROR = auto()  # 配置错误
    PERMISSION_ERROR = auto()      # 权限错误
    MEMORY_ERROR = auto()          # 内存错误
    DISK_ERROR = auto()            # 磁盘错误
    TIMEOUT_ERROR = auto()         # 超时错误
    IMPORT_ERROR = auto()          # 导入错误
    DEPENDENCY_ERROR = auto()      # 依赖错误
    SERVICE_ERROR = auto()         # 服务错误
    DATABASE_ERROR = auto()         # 数据库错误
    UNKNOWN = auto()               # 未知错误


@dataclass
class OcrResult:
    """OCR 识别结果"""
    success: bool
    text: str
    confidence: float
    error: Optional[str] = None
    categories: List[str] = None
    keywords: List[str] = None
    suggested_actions: List[str] = None

    def __post_init__(self):
        if self.categories is None:
            self.categories = []
        if self.keywords is None:
            self.keywords = []


class OcrService:
    """OCR 图片识别服务"""

    # 错误模式匹配规则
    ERROR_PATTERNS = {
        ErrorCategory.SYNTAX_ERROR: [
            r"SyntaxError",
            r"IndentationError",
            r"TabError",
            r"unexpected indent",
            r"invalid syntax",
        ],
        ErrorCategory.RUNTIME_ERROR: [
            r"RuntimeError",
            r"TypeError",
            r"ValueError",
            r"NameError",
            r"AttributeError",
            r"KeyError",
            r"IndexError",
        ],
        ErrorCategory.CONNECTION_ERROR: [
            r"ConnectionRefused",
            r"ConnectionReset",
            r"ConnectionError",
            r"NetworkUnreachable",
            r"SocketError",
            r"Could not resolve",
        ],
        ErrorCategory.CONFIGURATION_ERROR: [
            r"ConfigurationError",
            r"ConfigError",
            r"Invalid.*config",
            r"Config.*not.*found",
        ],
        ErrorCategory.PERMISSION_ERROR: [
            r"PermissionError",
            r"Access.*Denied",
            r"Not.*permitted",
            r"EACCES",
            r"EPERM",
        ],
        ErrorCategory.MEMORY_ERROR: [
            r"MemoryError",
            r"OutOfMemory",
            r"Killed.*process",
            r"OOM",
        ],
        ErrorCategory.DISK_ERROR: [
            r"DiskFull",
            r"NoSpaceLeft",
            r"IOError",
            r"OSError.*28",
            r"ENOSPC",
        ],
        ErrorCategory.TIMEOUT_ERROR: [
            r"TimeoutError",
            r"Connection.*timed.*out",
            r"Read.*timed.*out",
            r"TIMEOUT",
        ],
        ErrorCategory.IMPORT_ERROR: [
            r"ImportError",
            r"ModuleNotFoundError",
            r"NoModuleNamed",
            r"Import.*Error",
        ],
        ErrorCategory.DEPENDENCY_ERROR: [
            r"DependencyError",
            r"Package.*not.*found",
            r"pip.*install.*failed",
            r"requirement.*not.*satisfied",
        ],
        ErrorCategory.SERVICE_ERROR: [
            r"Service.*Error",
            r"Service.*Failed",
            r"Failed.*to.*start",
            r"Unit.*not.*found",
        ],
        ErrorCategory.DATABASE_ERROR: [
            r"DatabaseError",
            r"SQL.*Error",
            r"Connection.*refused.*database",
            r"MySQL.*Error",
            r"PostgreSQL.*Error",
        ],
    }

    # 常见问题关键词
    COMMON_KEYWORDS = {
        "error": "错误",
        "failed": "失败",
        "exception": "异常",
        "traceback": "回溯",
        "warning": "警告",
        "deprecated": "已弃用",
        "cannot": "无法",
        "unable": "不能",
        "invalid": "无效",
        "missing": "缺失",
        "not found": "未找到",
        "already exists": "已存在",
        "permission denied": "权限被拒",
    }

    # 建议操作模板
    SUGGESTED_ACTIONS = {
        ErrorCategory.SYNTAX_ERROR: [
            "检查代码缩进是否正确",
            "确认语法格式符合 Python 规范",
            "查看具体报错位置的代码"
        ],
        ErrorCategory.IMPORT_ERROR: [
            "确认模块已安装: pip install <module_name>",
            "检查 Python 环境是否正确",
            "确认 __init__.py 文件存在"
        ],
        ErrorCategory.CONFIGURATION_ERROR: [
            "检查配置文件路径是否正确",
            "验证配置文件格式（JSON/YAML）",
            "确认必要的配置项已填写"
        ],
        ErrorCategory.PERMISSION_ERROR: [
            "使用管理员权限运行",
            "检查文件/目录权限设置",
            "修改文件所有者"
        ],
        ErrorCategory.SERVICE_ERROR: [
            "检查服务是否已安装",
            "确认服务配置文件正确",
            "重启相关服务"
        ],
        ErrorCategory.DATABASE_ERROR: [
            "检查数据库连接信息",
            "确认数据库服务正在运行",
            "验证数据库凭据"
        ],
    }

    def __init__(self, tesseract_path: Optional[str] = None):
        """初始化 OCR 服务

        Args:
            tesseract_path: Tesseract 可执行文件路径
        """
        self.tesseract_path = tesseract_path or self._find_tesseract()
        self._check_tesseract()

    def _find_tesseract(self) -> Optional[str]:
        """查找 Tesseract 可执行文件"""
        # 检查常见路径
        common_paths = [
            # Windows
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            # Linux
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
            # macOS
            "/usr/local/bin/tesseract",
        ]

        for path in common_paths:
            if Path(path).exists():
                return path

        # 尝试系统 PATH
        try:
            result = subprocess.run(
                ["where", "tesseract"] if os.name == "nt" else ["which", "tesseract"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.decode().strip().split('\n')[0]
        except Exception:
            pass

        return None

    def _check_tesseract(self) -> bool:
        """检查 Tesseract 是否可用"""
        if not self.tesseract_path:
            self.available = False
            return False

        try:
            result = subprocess.run(
                [self.tesseract_path, "--version"],
                capture_output=True,
                timeout=10
            )
            self.available = result.returncode == 0
            if self.available:
                self.version = result.stdout.decode().strip()
            return self.available
        except Exception:
            self.available = False
            return False

    def recognize_text(self, image_path: str) -> OcrResult:
        """识别图片中的文字

        Args:
            image_path: 图片文件路径

        Returns:
            OcrResult 识别结果
        """
        if not self.available:
            return OcrResult(
                success=False,
                text="",
                confidence=0.0,
                error="Tesseract OCR 未安装或未配置",
                categories=["需要安装 Tesseract"],
                suggested_actions=[
                    "Windows: 下载安装 https://github.com/UB-Mannheim/tesseract/wiki",
                    "Linux: sudo apt-get install tesseract-ocr",
                    "macOS: brew install tesseract"
                ]
            )

        try:
            from PIL import Image
            import pytesseract

            # 打开并处理图片
            img = Image.open(image_path)

            # 尝试提高识别率的预处理
            img = self._preprocess_image(img)

            # 执行 OCR
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')

            # 计算置信度（简单估算）
            confidence = self._estimate_confidence(text)

            # 分析错误类别
            categories = self._analyze_categories(text)
            keywords = self._extract_keywords(text)
            actions = self._suggest_actions(categories)

            return OcrResult(
                success=True,
                text=text.strip(),
                confidence=confidence,
                categories=categories,
                keywords=keywords,
                suggested_actions=actions
            )

        except ImportError as e:
            return OcrResult(
                success=False,
                text="",
                confidence=0.0,
                error=f"缺少依赖库: {str(e)}",
                suggested_actions=[
                    "安装必要依赖: pip install Pillow pytesseract"
                ]
            )
        except Exception as e:
            return OcrResult(
                success=False,
                text="",
                confidence=0.0,
                error=str(e)
            )

    def recognize_base64(self, base64_image: str) -> OcrResult:
        """识别 Base64 编码的图片

        Args:
            base64_image: Base64 编码的图片字符串

        Returns:
            OcrResult 识别结果
        """
        try:
            # 解码 Base64
            image_data = base64.b64decode(base64_image)
            img = Image.open(io.BytesIO(image_data))
            temp_path = self._save_temp_image(img)
            result = self.recognize_text(temp_path)
            # 清理临时文件
            try:
                os.remove(temp_path)
            except Exception:
                pass
            return result
        except Exception as e:
            return OcrResult(
                success=False,
                text="",
                confidence=0.0,
                error=f"解析 Base64 图片失败: {str(e)}"
            )

    def _preprocess_image(self, img) -> Image.Image:
        """预处理图片以提高识别率"""
        from PIL import ImageFilter

        # 转换为灰度图
        if img.mode != 'L':
            img = img.convert('L')

        # 尝试锐化
        img = img.filter(ImageFilter.SHARPEN)

        return img

    def _save_temp_image(self, img) -> str:
        """保存临时图片"""
        temp_dir = Path.home() / ".cache" / "auto_fix"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f"ocr_temp_{os.getpid()}.png"
        img.save(temp_path)
        return str(temp_path)

    def _estimate_confidence(self, text: str) -> float:
        """估算识别置信度"""
        if not text:
            return 0.0

        # 基础置信度
        confidence = 0.7

        # 如果有中文字符，提高置信度
        if re.search(r'[\u4e00-\u9fff]', text):
            confidence += 0.1

        # 如果识别到常见错误词，提高置信度
        error_words = ["Error", "Exception", "Traceback", "Failed", "Warning"]
        if any(word in text for word in error_words):
            confidence += 0.1

        # 限制在 0-1 范围内
        return min(0.99, confidence)

    def _analyze_categories(self, text: str) -> List[str]:
        """分析错误类别"""
        categories = []
        text_lower = text.lower()

        for category, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    categories.append(category.name)
                    break

        if not categories:
            categories.append(ErrorCategory.UNKNOWN.name)

        return categories

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = []

        # 提取大写的英文错误类型
        error_types = re.findall(r'\b([A-Z][A-Z]+Error|[A-Z][A-Z]+Exception)\b', text)
        keywords.extend(error_types)

        # 提取常见关键词
        for keyword in self.COMMON_KEYWORDS:
            if keyword.lower() in text.lower():
                keywords.append(keyword)

        return list(set(keywords))

    def _suggest_actions(self, categories: List[str]) -> List[str]:
        """生成建议操作"""
        actions = []
        seen = set()

        for category_name in categories:
            if category_name == ErrorCategory.UNKNOWN.name:
                # 通用建议
                actions.append("请提供更多错误信息以便分析")
                actions.append("尝试搜索错误信息获取解决方案")
                continue

            try:
                category = ErrorCategory[category_name]
            except KeyError:
                continue

            # 获取该类别的建议操作
            category_actions = self.SUGGESTED_ACTIONS.get(category, [])
            for action in category_actions:
                if action not in seen:
                    actions.append(action)
                    seen.add(action)

        # 如果没有建议，添加通用建议
        if not actions:
            actions.append("请查看详细错误信息后重试")

        return actions

    def analyze_screenshot(self, image_path: str) -> Dict[str, Any]:
        """综合分析截图

        Args:
            image_path: 图片路径

        Returns:
            包含分析结果的字典
        """
        ocr_result = self.recognize_text(image_path)

        return {
            "success": ocr_result.success,
            "recognized_text": ocr_result.text,
            "confidence": ocr_result.confidence,
            "error_categories": ocr_result.categories,
            "keywords": ocr_result.keywords,
            "suggested_actions": ocr_result.suggested_actions,
            "error_details": ocr_result.error if not ocr_result.success else None,
            "recommendations": self._generate_recommendations(ocr_result)
        }

    def _generate_recommendations(self, ocr_result: OcrResult) -> List[str]:
        """生成具体建议"""
        recommendations = []

        if not ocr_result.success:
            return ocr_result.suggested_actions or ["请检查 OCR 配置"]

        # 根据识别到的类别生成建议
        for category_name in ocr_result.categories:
            if category_name == ErrorCategory.UNKNOWN.name:
                continue

            recommendations.extend(ocr_result.suggested_actions)

        return recommendations


# 便捷函数
def recognize_error(image_path: str) -> Dict[str, Any]:
    """识别图片中的错误信息（便捷函数）"""
    service = OcrService()
    return service.analyze_screenshot(image_path)


def recognize_base64_error(base64_image: str) -> Dict[str, Any]:
    """识别 Base64 编码的错误截图（便捷函数）"""
    service = OcrService()
    result = service.recognize_base64(base64_image)

    return {
        "success": result.success,
        "text": result.text,
        "categories": result.categories,
        "keywords": result.keywords,
        "actions": result.suggested_actions,
        "error": result.error
    }
