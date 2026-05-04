"""
网格绘制功能
"""
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont


class GridRenderer:
    """网格绘制器"""

    def __init__(
        self,
        density_x: float = 5.0,
        density_y: float = 5.0,
        grid_opacity: int = 50,
        grid_color: str = "#ff0000",
        number_density: int = 2,
        number_decimal: int = 1,
        number_size: int = 12,
        number_color: str = "#ff0000",
        number_opacity: int = 100,
        number_stroke_width: int = 1,
        number_stroke_color: str = "#ffffff",
        color_mode: str = "grayscale"
    ):
        self.density_x = density_x
        self.density_y = density_y
        self.grid_opacity = grid_opacity
        self.grid_color = grid_color
        self.number_density = number_density
        self.number_decimal = number_decimal
        self.number_size = number_size
        self.number_color = number_color
        self.number_opacity = number_opacity
        self.number_stroke_width = number_stroke_width
        self.number_stroke_color = number_stroke_color
        self.color_mode = color_mode

    def draw_grid(self, image: Image.Image) -> Image.Image:
        """
        在图片上绘制网格

        Args:
            image: 原始截图

        Returns:
            带网格的图片
        """
        width, height = image.size

        # 灰度模式：转为灰度图后再绘制彩色网格，使坐标更醒目
        if self.color_mode == "grayscale":
            image = image.convert("L").convert("RGBA")
        elif image.mode != "RGBA":
            image = image.convert("RGBA")

        # 创建透明图层
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 解析颜色
        grid_rgba = self._hex_to_rgba(self.grid_color, self.grid_opacity)
        number_rgba = self._hex_to_rgba(self.number_color, self.number_opacity)
        stroke_rgba = self._hex_to_rgba(self.number_stroke_color, 100)

        # 加载字体
        font = self._load_font(self.number_size)
        separator_font = self._load_font(max(4, int(round(self.number_size * 0.5))))

        # 计算网格间距（像素）
        grid_step_x = int(width * self.density_x / 100)
        grid_step_y = int(height * self.density_y / 100)

        if grid_step_x == 0 or grid_step_y == 0:
            # 密度太小，不绘制网格
            return image

        # 绘制网格线
        self._draw_grid_lines(draw, width, height, grid_step_x, grid_step_y, grid_rgba)

        # 绘制坐标数字
        self._draw_coordinates(
            draw, width, height, grid_step_x, grid_step_y, font, separator_font, number_rgba, stroke_rgba
        )

        # 合并图层
        result = Image.alpha_composite(image, overlay)

        return result

    def _draw_grid_lines(
        self,
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        step_x: int,
        step_y: int,
        color: Tuple[int, int, int, int]
    ):
        """绘制网格线"""
        # 垂直线（从0到100%）
        percent_x = 0.0
        while percent_x <= 100.0:
            x = int(width * percent_x / 100)
            draw.line([(x, 0), (x, height)], fill=color, width=1)
            percent_x += self.density_x

        # 水平线（从0到100%）
        percent_y = 0.0
        while percent_y <= 100.0:
            y = int(height * percent_y / 100)
            draw.line([(0, y), (width, y)], fill=color, width=1)
            percent_y += self.density_y

    def _draw_coordinates(
        self,
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        step_x: int,
        step_y: int,
        font: ImageFont.FreeTypeFont,
        separator_font: ImageFont.FreeTypeFont,
        color: Tuple[int, int, int, int],
        stroke_color: Tuple[int, int, int, int]
    ):
        """绘制坐标数字"""
        # 使用百分比作为循环变量（0-100），避免累加误差
        percent_step_x = self.density_x * self.number_density
        percent_step_y = self.density_y * self.number_density

        percent_x = 0.0
        while percent_x <= 100.0:
            x = int(width * percent_x / 100)

            percent_y = 0.0
            while percent_y <= 100.0:
                y = int(height * percent_y / 100)

                # 格式化坐标文本
                left, sep, right = self._format_coordinate_parts(percent_x, percent_y)

                # 绘制文本：分隔符 x 对齐交叉点，数字悬停在横线上方 1px
                self._draw_coordinate_text(
                    draw, x, y, left, sep, right,
                    font, separator_font, color, stroke_color
                )

                percent_y += percent_step_y

            percent_x += percent_step_x

    def _format_coordinate(self, x_percent: float, y_percent: float) -> str:
        """格式化坐标文本，使用x作为分隔符"""
        left, sep, right = self._format_coordinate_parts(x_percent, y_percent)
        return f"{left}{sep}{right}"

    def _format_coordinate_parts(self, x_percent: float, y_percent: float) -> Tuple[str, str, str]:
        """格式化坐标文本组件，分隔符使用半字号绘制"""
        if self.number_decimal == 0:
            return (str(int(round(x_percent))), "x", str(int(round(y_percent))))
        else:
            format_str = f"{{:.{self.number_decimal}f}}"
            return (format_str.format(x_percent), "x", format_str.format(y_percent))

    @staticmethod
    def measure_coordinate_text(
        draw: ImageDraw.ImageDraw,
        left: str,
        sep: str,
        right: str,
        font: ImageFont.FreeTypeFont,
        separator_font: ImageFont.FreeTypeFont
    ) -> Tuple[int, int]:
        """测量混合字号坐标文本尺寸"""
        left_bbox = draw.textbbox((0, 0), left, font=font)
        sep_bbox = draw.textbbox((0, 0), sep, font=separator_font)
        right_bbox = draw.textbbox((0, 0), right, font=font)
        width = (left_bbox[2] - left_bbox[0]) + (sep_bbox[2] - sep_bbox[0]) + (right_bbox[2] - right_bbox[0])
        height = max(
            left_bbox[3] - left_bbox[1],
            sep_bbox[3] - sep_bbox[1],
            right_bbox[3] - right_bbox[1],
        )
        return width, height

    def _draw_coordinate_text(
        self,
        draw: ImageDraw.ImageDraw,
        anchor_x: int,
        anchor_y: int,
        left: str,
        sep: str,
        right: str,
        font: ImageFont.FreeTypeFont,
        separator_font: ImageFont.FreeTypeFont,
        color: Tuple[int, int, int, int],
        stroke_color: Tuple[int, int, int, int]
    ):
        """绘制混合字号坐标文本。

        分隔符 x 的可见区域中心对齐网格交叉点；左右数字的可见区域
        底部贴在横线正上方 1px，减少数字笔画和横线重叠。
        """
        stroke_width = self.number_stroke_width
        layout = self._coordinate_text_layout(
            draw, anchor_x, anchor_y, left, sep, right, font, separator_font
        )
        for text, current_font, position in (
            (left, font, layout["left"]),
            (sep, separator_font, layout["sep"]),
            (right, font, layout["right"]),
        ):
            draw.text(
                position,
                text,
                fill=color,
                font=current_font,
                stroke_width=stroke_width,
                stroke_fill=stroke_color if stroke_width > 0 else None
            )

    @staticmethod
    def _coordinate_text_layout(
        draw: ImageDraw.ImageDraw,
        anchor_x: int,
        anchor_y: int,
        left: str,
        sep: str,
        right: str,
        font: ImageFont.FreeTypeFont,
        separator_font: ImageFont.FreeTypeFont
    ) -> dict:
        """计算坐标文本三段绘制位置。"""
        left_bbox = draw.textbbox((0, 0), left, font=font)
        sep_bbox = draw.textbbox((0, 0), sep, font=separator_font)
        right_bbox = draw.textbbox((0, 0), right, font=font)

        def width(bbox):
            return bbox[2] - bbox[0]

        def height(bbox):
            return bbox[3] - bbox[1]

        left_w = width(left_bbox)
        left_h = height(left_bbox)
        sep_w = width(sep_bbox)
        sep_h = height(sep_bbox)
        right_h = height(right_bbox)

        sep_left = anchor_x - sep_w / 2
        digit_bottom = anchor_y - 1

        left_pos = (
            int(round(sep_left - left_w - left_bbox[0])),
            int(round(digit_bottom - left_h - left_bbox[1])),
        )
        sep_pos = (
            int(round(anchor_x - sep_w / 2 - sep_bbox[0])),
            int(round(anchor_y - sep_h / 2 - sep_bbox[1])),
        )
        right_pos = (
            int(round(sep_left + sep_w - right_bbox[0])),
            int(round(digit_bottom - right_h - right_bbox[1])),
        )

        return {"left": left_pos, "sep": sep_pos, "right": right_pos}

    def _hex_to_rgba(self, hex_color: str, opacity: int) -> Tuple[int, int, int, int]:
        """HEX颜色转RGBA"""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        a = int(255 * opacity / 100)
        return (r, g, b, a)

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """加载系统默认字体"""
        # 尝试加载常用字体
        fonts_to_try = [
            "arial.ttf",
            "Arial.ttf",
            "msyh.ttc",  # 微软雅黑
            "simsun.ttc",  # 宋体
        ]

        for font_name in fonts_to_try:
            try:
                return ImageFont.truetype(font_name, size)
            except Exception:
                continue

        # 回退到默认字体
        return ImageFont.load_default()

    def draw_marker(
        self,
        image: Image.Image,
        x: float,
        y: float,
        ring_radius: int = 12,
        ring_line_width: int = 2,
        ring_color: str = "#FF0000",
        dot_radius: int = 3,
        dot_color: str = "#FF0000"
    ) -> Image.Image:
        """在图片上绘制标记（外圈空心圆 + 中心实心点）

        Args:
            image: 带网格的截图
            x: 标记点横坐标百分比 (0-100)
            y: 标记点纵坐标百分比 (0-100)
            ring_radius: 外圈空心圆半径(像素)
            ring_line_width: 外圈线宽(像素)
            ring_color: 外圈颜色(HEX)
            dot_radius: 中心实心圆半径(像素)
            dot_color: 中心实心圆颜色(HEX)

        Returns:
            带标记的图片
        """
        width, height = image.size

        if image.mode != "RGBA":
            image = image.convert("RGBA")

        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        px = int(width * x / 100)
        py = int(height * y / 100)

        ring_rgba = self._hex_to_rgba(ring_color, 100)
        dot_rgba = self._hex_to_rgba(dot_color, 100)

        # 外圈空心圆
        bbox = (
            px - ring_radius, py - ring_radius,
            px + ring_radius, py + ring_radius
        )
        draw.ellipse(bbox, outline=ring_rgba, width=ring_line_width)

        # 中心实心圆
        dot_bbox = (
            px - dot_radius, py - dot_radius,
            px + dot_radius, py + dot_radius
        )
        draw.ellipse(dot_bbox, fill=dot_rgba)

        result = Image.alpha_composite(image, overlay)
        return result
