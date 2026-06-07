"""
网格绘制功能
"""
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont


class GridRenderer:
    """网格绘制器"""

    def __init__(
        self,
        density: float = 5.0,
        grid_opacity: int = 50,
        grid_color: str = "#ff0000",
        number_density: int = 2,
        number_decimal: int = 0,
        number_size: int = 12,
        number_color: str = "#ff0000",
        number_opacity: int = 100,
        color_mode: str = "grayscale"
    ):
        self.density = density
        self.grid_opacity = grid_opacity
        self.grid_color = grid_color
        self.number_density = number_density
        self.number_decimal = number_decimal
        self.number_size = number_size
        self.number_color = number_color
        self.number_opacity = number_opacity
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

        # 加载字体
        font = self._load_font(self.number_size)

        # 计算网格间距（像素）
        grid_step_x = int(width * self.density / 100)
        grid_step_y = int(height * self.density / 100)

        if grid_step_x == 0 or grid_step_y == 0:
            # 密度太小，不绘制网格
            return image

        # 绘制网格线
        self._draw_grid_lines(draw, width, height, grid_step_x, grid_step_y, grid_rgba)

        # 绘制坐标数字
        self._draw_coordinates(
            draw, width, height, grid_step_x, grid_step_y, font, number_rgba
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
            percent_x += self.density

        # 水平线（从0到100%）
        percent_y = 0.0
        while percent_y <= 100.0:
            y = int(height * percent_y / 100)
            draw.line([(0, y), (width, y)], fill=color, width=1)
            percent_y += self.density

    def _draw_coordinates(
        self,
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        step_x: int,
        step_y: int,
        font: ImageFont.FreeTypeFont,
        color: Tuple[int, int, int, int]
    ):
        """绘制坐标数字"""
        text_step_x = step_x * self.number_density
        text_step_y = step_y * self.number_density

        # 使用百分比作为循环变量（0-100），避免累加误差
        percent_step = self.density * self.number_density

        percent_x = 0.0
        while percent_x <= 100.0:
            x = int(width * percent_x / 100)

            percent_y = 0.0
            while percent_y <= 100.0:
                y = int(height * percent_y / 100)

                # 格式化坐标文本
                text = self._format_coordinate(percent_x, percent_y)

                # 计算文本位置（交叉点上方）
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                pos_x = x - text_width // 2
                pos_y = y - text_height - 2  # 上方偏移

                # 确保不超出边界
                if pos_x < 0:
                    pos_x = 0
                if pos_y < 0:
                    pos_y = 0

                # 绘制文本
                draw.text((pos_x, pos_y), text, fill=color, font=font)

                percent_y += percent_step

            percent_x += percent_step

    def _format_coordinate(self, x_percent: float, y_percent: float) -> str:
        """格式化坐标文本，使用x作为分隔符"""
        if self.number_decimal == 0:
            return f"{int(round(x_percent))}x{int(round(y_percent))}"
        else:
            format_str = f"{{:.{self.number_decimal}f}}"
            return f"{format_str.format(x_percent)}x{format_str.format(y_percent)}"

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
