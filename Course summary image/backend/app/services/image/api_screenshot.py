"""HTML 转图片 API 服务 - 支持多种渲染后端"""
import os
import base64
import json
from typing import Optional
from pathlib import Path
from abc import ABC, abstractmethod
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings
from app.models.schemas import ParsedContent, ImageConfig


class BaseScreenshotAPI(ABC):
    """截图 API 基类"""

    @abstractmethod
    def generate(self, html: str, output_path: str) -> str:
        """生成图片"""
        pass


class HtmlCssToImageAPI(BaseScreenshotAPI):
    """htmlcsstoimage.com / hcti.io 服务"""

    API_URL = "https://hcti.io/v1/image"

    def __init__(self, api_key: str = None, api_id: str = None):
        self.api_key = api_key or os.getenv("HCTI_API_KEY", "")
        self.api_id = api_id or os.getenv("HCTI_API_ID", "")

    def generate(self, html: str, output_path: str) -> str:
        """使用 hcti.io API 生成图片"""
        import requests

        if not self.api_key or not self.api_id:
            raise ValueError("HCTI_API_KEY and HCTI_API_ID required")

        data = {
            "html": html,
            "css": """
                body {
                    width: 1200px;
                    height: 800px;
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                }
            """,
            "format": "png",
            "viewport_width": 1200,
            "viewport_height": 800,
        }

        response = requests.post(
            self.API_URL,
            data=data,
            auth=(self.api_id, self.api_key)
        )

        if response.status_code == 200:
            image_url = response.json().get("url")
            # 下载图片
            image_data = requests.get(image_url).content
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_data)
            return output_path
        else:
            raise Exception(f"API error: {response.text}")


class ApiFlashAPI(BaseScreenshotAPI):
    """APIFlash - 网页截图 API"""

    API_URL = "https://api.apiflash.com/v1/urltoimage"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("APIFLASH_API_KEY", "")

    def generate(self, html: str, output_path: str) -> str:
        """使用 APIFlash 生成图片"""
        import requests
        import time

        if not self.api_key:
            raise ValueError("APIFLASH_API_KEY required")

        # 将 HTML 上传到临时服务或使用 data URI
        # 由于 APIFlash 需要 URL，我们使用 base64 data URI
        b64_html = base64.b64encode(html.encode()).decode()

        data = {
            "access_key": self.api_key,
            "url": f"data:text/html;base64,{b64_html}",
            "output": "png",
            "width": 1200,
            "height": 800,
            "format": "png",
            "quality": 100,
            "no_ads": True,
            "no_cookie_banners": True,
        }

        # 提交任务
        response = requests.post(self.API_URL, data=data)
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("id")

            # 轮询获取结果
            for _ in range(30):
                time.sleep(2)
                status_response = requests.get(
                    f"https://api.apiflash.com/v1/urltoimage/{task_id}",
                    params={"access_key": self.api_key}
                )
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data.get("status") == "success":
                        image_url = status_data.get("url")
                        image_data = requests.get(image_url).content
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        with open(output_path, "wb") as f:
                            f.write(image_data)
                        return output_path
            raise Exception("Timeout waiting for image generation")
        else:
            raise Exception(f"API error: {response.text}")


class ScreenshotAPIService:
    """截图服务 - 支持多种后端"""

    # 支持的后端
    BACKENDS = {
        "hcti": HtmlCssToImageAPI,
        "apiflash": ApiFlashAPI,
    }

    def __init__(self, backend: str = "hcti"):
        self.backend_name = backend
        backend_class = self.BACKENDS.get(backend)
        if backend_class:
            self.backend = backend_class()
        else:
            raise ValueError(f"Unknown backend: {backend}")

        self.template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

    def _get_theme_class(self, gradient_theme: Optional[int] = None, simple_theme: str = "dark") -> tuple:
        """获取主题样式类名"""
        if gradient_theme:
            theme_name = ["sunset", "nature", "ocean", "purple", "forest", "aurora"][gradient_theme - 1]
            number_class = "gradient"
            footer_class = f"gradient-{gradient_theme}"
        else:
            theme_name = simple_theme
            number_class = simple_theme
            footer_class = f"solid-{simple_theme}"

        return theme_name, number_class, footer_class

    def _render_html(self, content: ParsedContent, config: ImageConfig) -> str:
        """渲染 HTML 模板"""
        template = self.env.get_template("summary_card.html")

        if config.gradient_theme:
            theme_name, number_class, footer_class = self._get_theme_class(config.gradient_theme)
        else:
            theme_name, number_class, footer_class = self._get_theme_class(
                None, simple_theme=config.theme.value if config.theme else "dark"
            )

        html = template.render(
            title=content.title,
            items=[{
                "title": item.title,
                "points": item.points
            } for item in content.items[:6]],
            source_url=content.source_url,
            theme=theme_name,
            number_class=number_class,
            footer_class=footer_class
        )
        return html

    def generate(self, content: ParsedContent, config: ImageConfig, output_path: str) -> str:
        """生成图片"""
        html = self._render_html(content, config)
        return self.backend.generate(html, output_path)

    def generate_local(self, content: ParsedContent, config: ImageConfig, output_path: str) -> str:
        """本地渲染（备用方案）"""
        from html2image import Html2Image

        html = self._render_html(content, config)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        hti = Html2Image(output_path=os.path.dirname(output_path))
        hti.screenshot(html_str=html, save_as=os.path.basename(output_path))

        return output_path

    def preview_themes(self, content: ParsedContent) -> dict:
        """预览所有主题"""
        outputs = {}

        for theme in ["light", "dark"]:
            config = ImageConfig(theme=theme)
            output_path = f"/tmp/preview_{theme}.png"
            try:
                self.generate(content, config, output_path)
                outputs[theme] = output_path
            except Exception as e:
                outputs[theme] = f"Error: {e}"

        for i in range(1, 7):
            config = ImageConfig(gradient_theme=i)
            output_path = f"/tmp/preview_gradient_{i}.png"
            try:
                self.generate(content, config, output_path)
                outputs[f"gradient_{i}"] = output_path
            except Exception as e:
                outputs[f"gradient_{i}"] = f"Error: {e}"

        return outputs
