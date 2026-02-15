import os
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from app.core.config import settings
from app.models.schemas import ParsedContent, ImageConfig, ThemeType


class ImageGenerator:
    """Image generator for course summary cards - 参考 ref1~ref6 设计"""

    def __init__(self):
        self.font_path = self._get_font_path()
        self.default_font_size = 22
        self.title_font_size = 42
        self.number_font_size = 240

        # 编号颜色 - 每个编号不同颜色（参考 ref3/ref4）
        self.number_colors_light = [
            "#3b82f6",  # 蓝色
            "#10b981",  # 绿色
            "#f59e0b",  # 橙色
            "#ef4444",  # 红色
            "#8b5cf6",  # 紫色
            "#06b6d4",  # 青色
        ]
        self.number_colors_dark = [
            "#60a5fa",  # 亮蓝
            "#34d399",  # 亮绿
            "#fbbf24",  # 亮橙
            "#f87171",  # 亮红
            "#a78bfa",  # 亮紫
            "#22d3ee",  # 亮青
        ]

    def _get_font_path(self) -> str:
        """Get path to Chinese font"""
        font_candidates = [
            "fonts/SimSun.ttf",
            "fonts/simsun.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "/usr/share/fonts/truetype/simsun/SimSun.ttf",
            "/System/Library/Fonts/PingFang.ttc",
        ]
        for path in font_candidates:
            if os.path.exists(path):
                return path
        try:
            return ImageFont.load_default()
        except:
            return ""

    def _load_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Load font with specified size"""
        try:
            if self.font_path and isinstance(self.font_path, str):
                return ImageFont.truetype(self.font_path, size)
            else:
                return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()

    def generate(self, content: ParsedContent, config: ImageConfig, output_path: str) -> str:
        """Generate summary image"""
        width = config.width
        height = config.height

        if config.theme == ThemeType.DARK:
            img = self._generate_modern_theme(content, config, is_dark=True)
        else:
            img = self._generate_modern_theme(content, config, is_dark=False)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, "PNG", quality=95)
        return output_path

    def _generate_modern_theme(self, content: ParsedContent, config: ImageConfig, is_dark: bool = False) -> Image.Image:
        """Generate modern styled image (参考 ref1 设计：左侧超大编号，右侧内容)"""
        width = config.width
        height = config.height

        # 背景色
        bg_color = "#111827" if is_dark else "#ffffff"
        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        # 颜色配置
        text_color = "#f9fafb" if is_dark else "#1f2937"
        secondary_text = "#9ca3af" if is_dark else "#6b7280"
        accent_color = "#3b82f6" if is_dark else "#2563eb"
        line_color = "#374151" if is_dark else "#e5e7eb"

        # 布局参数 - 参考 ref1 布局
        padding = 50
        number_zone_width = 280  # 编号区域宽度（左侧大编号）
        content_x = padding + number_zone_width + 30  # 内容起始X位置
        content_width = width - content_x - padding

        # 加载字体
        title_font = self._load_font(self.title_font_size, bold=True)
        number_font = self._load_font(self.number_font_size + 40, bold=True)  # 更大的编号字体
        content_font = self._load_font(config.font_size + 2)
        small_font = self._load_font(config.font_size - 2)

        # ========== 顶部标题栏 ==========
        current_y = padding

        # 标题背景
        title_bg_color = accent_color if not is_dark else "#1e3a8a"
        title_bar_height = 70
        draw.rectangle(
            [(0, current_y), (width, current_y + title_bar_height)],
            fill=title_bg_color
        )

        # 标题文字
        title = content.title[:45] + "..." if len(content.title) > 45 else content.title
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_text_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_text_width) // 2
        title_y = current_y + (title_bar_height - title_font.size) // 2 + 8
        draw.text((title_x, title_y), title, font=title_font, fill="#ffffff")

        current_y += title_bar_height + 40

        # ========== 内容列表 ==========
        number_colors = self.number_colors_dark if is_dark else self.number_colors_light

        for i, item in enumerate(items := content.items[:6]):
            color = number_colors[i % len(number_colors)]

            # 计算这一项的高度
            content_lines = []
            if item.title:
                max_title_len = 25
                title_text = item.title[:max_title_len] + "..." if len(item.title) > max_title_len else item.title
                content_lines.append(("title", title_text))
            for point in item.points[:4]:
                max_point_len = 50
                point_text = point[:max_point_len] + "..." if len(point) > max_point_len else point
                content_lines.append(("point", point_text))

            # 项目高度 = 标题行高 + 要点行高
            item_height = 60 + len(content_lines) * 38

            # 每项背景
            item_bg_color = ("#1f2937" if is_dark else "#f8fafc")
            draw.rectangle(
                [(padding, current_y), (width - padding, current_y + item_height)],
                fill=item_bg_color,
                outline=line_color,
                width=1
            )

            # 左侧超大编号（参考 ref1）
            number_text = str(i + 1)
            number_bbox = draw.textbbox((0, 0), number_text, font=number_font)
            number_width = number_bbox[2] - number_bbox[0]
            number_height = number_bbox[3] - number_bbox[1]
            number_x = padding + 25
            number_y = current_y + (item_height - number_height) // 2 - 10

            # 绘制编号
            draw.text((number_x, number_y), number_text, font=number_font, fill=color)

            # 右侧内容
            right_x = content_x
            right_y = current_y + 25

            # 标题
            if item.title:
                title_text = item.title[:25] + "..." if len(item.title) > 25 else item.title
                draw.text((right_x, right_y), title_text, font=title_font, fill=color)
                right_y += config.font_size + 18

            # 要点列表
            for j, point in enumerate(item.points[:4]):
                point_text = point[:50] + "..." if len(point) > 50 else point
                bullet = "• "
                draw.text((right_x, right_y), bullet, font=small_font, fill=secondary_text)
                draw.text((right_x + 15, right_y), point_text, font=small_font, fill=text_color)
                right_y += config.font_size + 10

            current_y += item_height + 12

            # 绘制分隔线
            if i < len(items) - 1:
                separator_y = current_y - 6
                draw.line(
                    [(padding + 20, separator_y), (width - padding - 20, separator_y)],
                    fill=line_color,
                    width=1
                )

        # ========== 底部来源 ==========
        if content.source_url:
            source_y = height - 35
            source_text = f"Source: {content.source_url[:60]}..." if len(content.source_url) > 60 else content.source_url
            source_bbox = draw.textbbox((0, 0), source_text, font=small_font)
            source_width = source_bbox[2] - source_bbox[0]
            draw.text(((width - source_width) // 2, source_y), source_text, font=small_font, fill=secondary_text)

        return img

    def _wrap_text(self, draw, text: str, max_width: int, font) -> list:
        """Wrap text to fit within max_width - 不常用，保留兼容"""
        words = text.replace('\n', ' ').split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines if lines else [text[:20] + "..."]

    def preview_themes(self, content: ParsedContent) -> dict:
        """Generate preview images for both themes"""
        config = ImageConfig()
        outputs = {}

        for theme in [ThemeType.LIGHT, ThemeType.DARK]:
            config.theme = theme
            output_path = f"/tmp/preview_{theme.value}.png"
            self.generate(content, config, output_path)
            outputs[theme.value] = output_path

        return outputs
