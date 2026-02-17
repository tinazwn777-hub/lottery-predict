"""HTML + html2image 截图服务 - 生成高质量图片"""
import os
from typing import Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings
from app.models.schemas import ParsedContent, ImageConfig


class HTMLImageGenerator:
    """使用 HTML + html2image 生成高质量图片"""

    def __init__(self):
        self.template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        self._browser = None

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

        # 获取主题样式
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
        from html2image import Html2Image

        html = self._render_html(content, config)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 使用 html2image 生成图片
        hti = Html2Image(
            output_path=os.path.dirname(output_path),
            size=(1200, 800)
        )

        # 生成截图
        hti.screenshot(
            html_str=html,
            save_as=os.path.basename(output_path)
        )

        return output_path

    def preview_themes(self, content: ParsedContent) -> dict:
        """预览所有主题"""
        outputs = {}

        for theme in ["light", "dark"]:
            config = ImageConfig(theme=theme)
            output_path = f"/tmp/preview_{theme}.png"
            self.generate(content, config, output_path)
            outputs[theme] = output_path

        for i in range(1, 7):
            config = ImageConfig(gradient_theme=i)
            output_path = f"/tmp/preview_gradient_{i}.png"
            self.generate(content, config, output_path)
            outputs[f"gradient_{i}"] = output_path

        return outputs
