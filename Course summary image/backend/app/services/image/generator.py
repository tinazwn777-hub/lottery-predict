import os
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from app.core.config import settings
from app.models.schemas import ParsedContent, ImageConfig, ThemeType


class GradientType:
    """渐变类型枚举"""
    SUNSET = "sunset"     # 橙→黄渐变 (ref2)
    NATURE = "nature"     # 绿→青渐变 (ref3/ref5)
    OCEAN = "ocean"       # 蓝→青渐变 (ref4)
    PURPLE = "purple"     # 紫→粉渐变
    FIRE = "fire"         # 红→橙渐变
    AURORA = "aurora"     # 多彩极光


class ThemePreset:
    """主题预设配置"""

    # 预定义渐变主题（对应编号 1-6）
    GRADIENT_THEMES = {
        1: {
            "name": "Sunset",
            "gradient": (GradientType.SUNSET,),
            "bg_colors": ("#1a1a2e", "#16213e"),  # 深蓝背景
            "text_colors": ("#ffffff", "#e0e0e0"),
        },
        2: {
            "name": "Nature",
            "gradient": (GradientType.NATURE,),
            "bg_colors": ("#0d1b2a", "#1b263b"),
            "text_colors": ("#e0fbfc", "#dee2e6"),
        },
        3: {
            "name": "Ocean",
            "gradient": (GradientType.OCEAN,),
            "bg_colors": ("#0a0a0a", "#1a1a2e"),
            "text_colors": ("#ffffff", "#b0b0b0"),
        },
        4: {
            "name": "Purple Dream",
            "gradient": (GradientType.PURPLE,),
            "bg_colors":("#1a0a2e", "#2d1b4e"),
            "text_colors": ("#ffffff", "#e0b0ff"),
        },
        5: {
            "name": "Forest",
            "gradient": (GradientType.NATURE,),
            "bg_colors": ("#0f2027", "#203a43"),
            "text_colors": ("#c8e6c9", "#a5d6a7"),
        },
        6: {
            "name": "Aurora",
            "gradient": (GradientType.AURORA,),
            "bg_colors": ("#0c0c1e", "#1a1a3e"),
            "text_colors": ("#ffffff", "#b0b0ff"),
        },
    }

    # 简洁主题（无渐变编号）
    SIMPLE_THEMES = {
        ThemeType.LIGHT: {
            "bg_color": "#ffffff",
            "text_color": "#1a1a1a",
            "secondary_text": "#666666",
            "line_color": "#e0e0e0",
            "accent_colors": ["#ef4444", "#3b82f6", "#22c55e", "#f97316", "#8b5cf6", "#06b6d4"],
        },
        ThemeType.DARK: {
            "bg_color": "#0f172a",
            "text_color": "#f1f5f9",
            "secondary_text": "#94a3b8",
            "line_color": "#334155",
            "accent_colors": ["#f87171", "#60a5fa", "#4ade80", "#fb923c", "#a78bfa", "#22d3ee"],
        },
    }


class ImageGenerator:
    """Image generator for course summary cards - 参考 ref1~ref6 设计"""

    def __init__(self):
        self.font_path = self._get_font_path()
        self.default_font_size = 20
        self.title_font_size = 28
        # 横向 A4 比例尺寸
        self.default_width = 1200
        self.default_height = 800

        # 渐变色定义 (起始色, 结束色)
        self.gradient_colors = {
            GradientType.SUNSET: [("#ff6b35", "#f7c59f"), ("#ff6b35", "#ffd166"), ("#f25f4c", "#faa307")],
            GradientType.NATURE: [("#2ecc71", "#a8e6cf"), ("#27ae60", "#82e0aa"), ("#1abc9c", "#76d7c4")],
            GradientType.OCEAN: [("#3498db", "#85c1e9"), ("#2980b9", "#aed6f1"), ("#00bcd4", "#80deea")],
            GradientType.PURPLE: [("#9b59b6", "#d7bde2"), ("#8e44ad", "#c39bd3"), ("#e91e63", "#f48fb1")],
            GradientType.FIRE: [("#e74c3c", "#f1948a"), ("#c0392b", "#ec7063"), ("#d35400", "#e59866")],
            GradientType.AURORA: [("#00d4ff", "#7b2cbf"), ("#4facfe", "#00f2fe"), ("#43e97b", "#38f9d7")],
        }

    def _get_font_path(self) -> str:
        """Get path to Chinese font"""
        font_candidates = [
            "fonts/SimSun.ttf",
            "fonts/simsun.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/msyh.ttc",
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
                # 尝试加载粗体版本
                if bold:
                    bold_path = self.font_path.replace(".ttc", "bd.ttc").replace(".ttf", "bd.ttf")
                    if os.path.exists(bold_path):
                        return ImageFont.truetype(bold_path, size)
                return ImageFont.truetype(self.font_path, size)
            else:
                return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()

    def _create_gradient(self, width: int, height: int, colors: List[str]) -> Image.Image:
        """Create a vertical gradient image"""
        base = Image.new('RGB', (width, height), colors[0])
        top = Image.new('RGB', (width, height), colors[1] if len(colors) > 1 else colors[0])
        mask = Image.new('L', (width, height))
        mask_data = []

        for y in range(height):
            # 线性渐变
            ratio = y / height
            mask_data.extend([int(255 * ratio)] * width)

        mask.putdata(mask_data)
        base.paste(top, (0, 0), mask)
        return base

    def _create_linear_gradient(self, width: int, height: int, start_color: str, end_color: str,
                                 direction: str = "vertical") -> Image.Image:
        """Create a linear gradient between two colors"""
        # 解析颜色
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        start_rgb = hex_to_rgb(start_color)
        end_rgb = hex_to_rgb(end_color)

        base = Image.new('RGB', (width, height), start_rgb)

        if direction == "vertical":
            for y in range(height):
                ratio = y / height
                r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
                g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
                b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
                for x in range(width):
                    base.putpixel((x, y), (r, g, b))
        else:  # horizontal
            for x in range(width):
                ratio = x / width
                r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
                g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
                b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
                for y in range(height):
                    base.putpixel((x, y), (r, g, b))

        return base

    def _create_number_gradient_mask(self, number_text: str, font: ImageFont.FreeTypeFont,
                                      start_color: str, end_color: str) -> Image.Image:
        """Create gradient text for number using mask technique"""
        # 获取文字边界框
        bbox = font.getbbox(number_text)
        width = bbox[2] - bbox[0] + 20  # 添加一些边距
        height = bbox[3] - bbox[1] + 20

        # 创建渐变底图
        gradient = self._create_linear_gradient(width, height, start_color, end_color, "vertical")

        # 创建文字 mask
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)

        # 绘制白色文字作为 mask
        try:
            # PIL 16.x 使用 textbbox
            bbox = mask_draw.textbbox((10, 10), number_text, font=font)
            mask_draw.text((10, 10), number_text, fill=255, font=font)
        except:
            mask_draw.text((10, 10), number_text, fill=255, font=font)

        return gradient, mask

    def generate(self, content: ParsedContent, config: ImageConfig, output_path: str) -> str:
        """Generate summary image"""
        width = config.width if config.width else self.default_width
        height = config.height if config.height else self.default_height

        # 使用渐变主题
        if config.gradient_theme:
            img = self._generate_gradient_theme(content, config)
        elif config.theme == ThemeType.DARK:
            img = self._generate_modern_theme(content, config, is_dark=True)
        else:
            img = self._generate_modern_theme(content, config, is_dark=False)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, "PNG", quality=95)
        return output_path

    def _generate_gradient_theme(self, content: ParsedContent, config: ImageConfig) -> Image.Image:
        """Generate image with gradient styling (参考 ref1~ref6 样式)"""
        width = config.width if config.width else self.default_width
        height = config.height if config.height else self.default_height

        # 获取主题预设
        theme_idx = config.gradient_theme if isinstance(config.gradient_theme, int) else 1
        theme_preset = ThemePreset.GRADIENT_THEMES.get(theme_idx, ThemePreset.GRADIENT_THEMES[1])

        # 创建渐变背景
        bg_colors = theme_preset["bg_colors"]
        img = self._create_linear_gradient(width, height, bg_colors[0], bg_colors[1], "vertical")

        # 添加微妙的噪点纹理（可选）
        # img = self._add_noise(img, intensity=10)

        draw = ImageDraw.Draw(img)

        # 颜色配置
        text_color = theme_preset["text_colors"][0]
        secondary_text = theme_preset["text_colors"][1]
        line_color = "#40ffffff"  # 半透明白色 (hex with alpha workaround)

        # 布局参数 - 参考 ref1~ref6
        padding = 50
        number_zone_width = 180
        content_x = padding + number_zone_width + 30
        content_width = width - content_x - padding

        # 加载字体
        title_font = self._load_font(self.title_font_size, bold=True)
        number_font = self._load_font(140, bold=True)
        content_font = self._load_font(config.font_size)
        small_font = self._load_font(config.font_size - 2)

        current_y = padding + 20

        # ========== 顶部标题 ==========
        if content.title:
            title_text = content.title
            if len(title_text) > 30:
                title_text = title_text[:28] + "..."
            draw.text((width // 2 - 200, current_y), title_text, font=title_font, fill=text_color)
            title_bbox = title_font.getbbox(title_text)
            current_y += (title_bbox[3] - title_bbox[1]) + 40

        # ========== 内容列表 ==========
        gradient_type = theme_preset["gradient"][0]
        gradient_list = self.gradient_colors.get(gradient_type, self.gradient_colors[GradientType.SUNSET])

        items = content.items[:6]
        for i, item in enumerate(items):
            gradient_pair = gradient_list[i % len(gradient_list)]

            # 左侧渐变编号
            number_text = str(i + 1)
            number_bbox = number_font.getbbox(number_text)
            number_width = number_bbox[2] - number_bbox[0]
            number_height = number_bbox[3] - number_bbox[1]
            number_x = padding + 20
            number_y = current_y - 10

            # 创建渐变编号
            gradient_img, mask = self._create_number_gradient_mask(
                number_text, number_font, gradient_pair[0], gradient_pair[1]
            )

            # 将渐变编号粘贴到主图
            img.paste(gradient_img, (number_x, number_y), mask)

            # 右侧内容
            right_x = content_x
            right_y = current_y

            # 标题
            if item.title:
                max_title_len = 20
                title_text = item.title[:max_title_len] + "..." if len(item.title) > max_title_len else item.title
                draw.text((right_x, right_y), title_text, font=title_font, fill=text_color)
                title_bbox = title_font.getbbox(title_text)
                right_y += (title_bbox[3] - title_bbox[1]) + 12

            # 要点列表
            for j, point in enumerate(item.points[:4]):
                max_point_len = 35
                point_text = point[:max_point_len] + "..." if len(point) > max_point_len else point

                # 圆点
                dot_bbox = small_font.getbbox("·")
                draw.text((right_x, right_y), "·", font=small_font, fill=secondary_text)
                draw.text((right_x + dot_bbox[2] + 6, right_y), point_text, font=content_font, fill=text_color)

                point_bbox = content_font.getbbox(point_text)
                right_y += (point_bbox[3] - point_bbox[1]) + 10

            # 更新位置
            item_height = right_y - current_y + 10
            current_y += item_height + 25

            # 绘制分隔线（半透明）
            if i < len(items) - 1:
                separator_y = current_y - 12
                draw.line(
                    [(content_x, separator_y), (width - padding, separator_y)],
                    fill=line_color,
                    width=1
                )

        # ========== 底部装饰 ==========
        # 底部渐变条
        gradient_bar_height = 4
        gradient_bar = self._create_linear_gradient(
            width, gradient_bar_height,
            gradient_list[0][0], gradient_list[-1][1], "horizontal"
        )
        img.paste(gradient_bar, (0, height - gradient_bar_height))

        # 底部来源
        if content.source_url:
            source_text = content.source_url[:60] + "..." if len(content.source_url) > 60 else content.source_url
            source_bbox = small_font.getbbox(source_text)
            source_width = source_bbox[2] - source_bbox[0]
            draw.text(((width - source_width) // 2, height - 28), source_text,
                     font=small_font, fill=secondary_text)

        return img

    def _generate_modern_theme(self, content: ParsedContent, config: ImageConfig, is_dark: bool = False) -> Image.Image:
        """Generate minimalist styled image"""
        width = config.width if config.width else self.default_width
        height = config.height if config.height else self.default_height

        # 纯色背景
        theme_config = ThemePreset.SIMPLE_THEMES[ThemeType.DARK if is_dark else ThemeType.LIGHT]
        bg_color = theme_config["bg_color"]
        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        # 颜色配置
        text_color = theme_config["text_color"]
        secondary_text = theme_config["secondary_text"]
        line_color = theme_config["line_color"]

        # 布局参数
        padding = 50
        number_zone_width = 160
        content_x = padding + number_zone_width + 25
        content_width = width - content_x - padding

        # 加载字体
        title_font = self._load_font(self.title_font_size, bold=True)
        number_font = self._load_font(120, bold=True)
        content_font = self._load_font(config.font_size)
        small_font = self._load_font(config.font_size - 2)

        current_y = padding + 20

        # 顶部标题
        if content.title:
            title_text = content.title
            if len(title_text) > 35:
                title_text = title_text[:33] + "..."
            draw.text((width // 2 - 200, current_y), title_text, font=title_font, fill=text_color)
            title_bbox = title_font.getbbox(title_text)
            current_y += (title_bbox[3] - title_bbox[1]) + 35

        # 内容列表
        accent_colors = theme_config["accent_colors"]
        items = content.items[:6]

        for i, item in enumerate(items):
            color = accent_colors[i % len(accent_colors)]

            # 左侧编号
            number_text = str(i + 1)
            number_bbox = number_font.getbbox(number_text)
            number_width = number_bbox[2] - number_bbox[0]
            number_height = number_bbox[3] - number_bbox[1]
            number_x = padding + 25
            number_y = current_y

            draw.text((number_x, number_y), number_text, font=number_font, fill=color)

            # 右侧内容
            right_x = content_x
            right_y = current_y + 5

            # 标题
            if item.title:
                max_title_len = 18
                title_text = item.title[:max_title_len] + "..." if len(item.title) > max_title_len else item.title
                draw.text((right_x, right_y), title_text, font=title_font, fill=text_color)
                title_bbox = title_font.getbbox(title_text)
                right_y += (title_bbox[3] - title_bbox[1]) + 10

            # 要点
            for j, point in enumerate(item.points[:4]):
                max_point_len = 40
                point_text = point[:max_point_len] + "..." if len(point) > max_point_len else point

                dot_bbox = small_font.getbbox("·")
                draw.text((right_x, right_y), "·", font=small_font, fill=secondary_text)
                draw.text((right_x + dot_bbox[2] + 6, right_y), point_text, font=content_font, fill=text_color)

                point_bbox = content_font.getbbox(point_text)
                right_y += (point_bbox[3] - point_bbox[1]) + 8

            # 更新位置
            item_height = right_y - current_y + 10
            current_y += item_height + 20

            # 分隔线
            if i < len(items) - 1:
                separator_y = current_y - 10
                draw.line(
                    [(content_x, separator_y), (width - padding, separator_y)],
                    fill=line_color,
                    width=1
                )

        # 底部来源
        if content.source_url:
            source_text = content.source_url[:70] + "..." if len(content.source_url) > 70 else content.source_url
            source_bbox = small_font.getbbox(source_text)
            source_width = source_bbox[2] - source_bbox[0]
            draw.text(((width - source_width) // 2, height - 30), source_text,
                     font=small_font, fill=secondary_text)

        return img

    def preview_themes(self, content: ParsedContent) -> dict:
        """Generate preview images for all themes"""
        outputs = {}

        # 简洁主题
        for theme in [ThemeType.LIGHT, ThemeType.DARK]:
            config = ImageConfig(theme=theme)
            output_path = f"/tmp/preview_{theme.value}.png"
            self.generate(content, config, output_path)
            outputs[theme.value] = output_path

        # 渐变主题 1-6
        for i in range(1, 7):
            config = ImageConfig(gradient_theme=i)
            output_path = f"/tmp/preview_gradient_{i}.png"
            self.generate(content, config, output_path)
            outputs[f"gradient_{i}"] = output_path

        return outputs
