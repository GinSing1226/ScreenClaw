"""
截图参数解析和自适应计算
"""
import math
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set, Tuple

from PIL import Image, ImageDraw

from app.core.grid import GridRenderer
from app.models.config import AppConfig


@dataclass
class ScreenshotParamsResult:
    grid: Dict[str, Any]
    coordinate: Dict[str, Any]
    color_mode: str
    adaptive_adjustments: list[str] = field(default_factory=list)


class ScreenshotParamsService:
    """根据最终输出图片尺寸生成实际生效截图参数"""

    TARGET_STEP_PX = 50

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        return max(min_value, min(max_value, value))

    @staticmethod
    def _explicit_fields(model: Any) -> Set[str]:
        if model is None:
            return set()
        return set(getattr(model, "model_fields_set", set()))

    @staticmethod
    def _dict_explicit_fields(value: Optional[Dict[str, Any]]) -> Set[str]:
        return set(value.keys()) if isinstance(value, dict) else set()

    def build_from_request(self, request: Any, config: AppConfig, image_size: Tuple[int, int]) -> ScreenshotParamsResult:
        """处理 Pydantic ScreenshotRequest"""
        grid_obj = getattr(request, "grid", None)
        coord_obj = getattr(request, "coordinate", None)
        return self._build(
            config=config,
            image_size=image_size,
            color_mode=getattr(request, "color_mode", None),
            grid_values=grid_obj.model_dump() if grid_obj else {},
            coordinate_values=coord_obj.model_dump() if coord_obj else {},
            explicit_grid=self._explicit_fields(grid_obj),
            explicit_coordinate=self._explicit_fields(coord_obj),
        )

    def build_from_dict(self, params: Dict[str, Any], config: AppConfig, image_size: Tuple[int, int]) -> ScreenshotParamsResult:
        """处理 batch screenshot 原始 dict 参数"""
        grid_values = params.get("grid") or {}
        coordinate_values = params.get("coordinate") or {}
        return self._build(
            config=config,
            image_size=image_size,
            color_mode=params.get("color_mode"),
            grid_values=grid_values,
            coordinate_values=coordinate_values,
            explicit_grid=self._dict_explicit_fields(grid_values),
            explicit_coordinate=self._dict_explicit_fields(coordinate_values),
        )

    def _build(
        self,
        config: AppConfig,
        image_size: Tuple[int, int],
        color_mode: Optional[str],
        grid_values: Dict[str, Any],
        coordinate_values: Dict[str, Any],
        explicit_grid: Set[str],
        explicit_coordinate: Set[str],
    ) -> ScreenshotParamsResult:
        width, height = image_size
        adjustments: list[str] = []

        auto_density_x = round(self._clamp(self.TARGET_STEP_PX / max(width, 1) * 100, 1.0, 12.0), 1)
        auto_density_y = round(self._clamp(self.TARGET_STEP_PX / max(height, 1) * 100, 1.0, 12.0), 1)

        density_x = grid_values.get("density_x") if "density_x" in explicit_grid else auto_density_x
        density_y = grid_values.get("density_y") if "density_y" in explicit_grid else auto_density_y
        if "density_x" not in explicit_grid:
            adjustments.append(f"grid.density_x auto={density_x}")
        if "density_y" not in explicit_grid:
            adjustments.append(f"grid.density_y auto={density_y}")

        grid = {
            "density_x": density_x,
            "density_y": density_y,
            "opacity": grid_values.get("opacity") if "opacity" in explicit_grid else config.screenshot.default_grid_opacity,
            "color": grid_values.get("color") if "color" in explicit_grid else config.screenshot.default_grid_color,
        }

        step_x = max(width * float(density_x) / 100, 1)
        step_y = max(height * float(density_y) / 100, 1)
        cell_short = min(step_x, step_y)
        auto_number_size = int(round(self._clamp(round(cell_short * 0.5), 12, 18)))

        number_size = (
            coordinate_values.get("number_size")
            if "number_size" in explicit_coordinate
            else auto_number_size
        )
        if "number_size" not in explicit_coordinate:
            adjustments.append(f"coordinate.number_size auto={number_size}")

        coordinate = {
            "number_density": coordinate_values.get("number_density")
            if "number_density" in explicit_coordinate
            else 1,
            "number_decimal": coordinate_values.get("number_decimal")
            if "number_decimal" in explicit_coordinate
            else config.screenshot.default_number_decimal,
            "number_size": number_size,
            "number_color": coordinate_values.get("number_color")
            if "number_color" in explicit_coordinate
            else config.screenshot.default_number_color,
            "number_opacity": coordinate_values.get("number_opacity")
            if "number_opacity" in explicit_coordinate
            else config.screenshot.default_number_opacity,
            "number_stroke_width": coordinate_values.get("number_stroke_width")
            if "number_stroke_width" in explicit_coordinate
            else config.screenshot.default_number_stroke_width,
            "number_stroke_color": coordinate_values.get("number_stroke_color")
            if "number_stroke_color" in explicit_coordinate
            else config.screenshot.default_number_stroke_color,
        }

        required_density = self._calculate_required_number_density(
            image_size=image_size,
            density_x=float(density_x),
            density_y=float(density_y),
            number_size=int(number_size),
        )
        current_density = int(coordinate["number_density"])
        if current_density < required_density:
            coordinate["number_density"] = required_density
            adjustments.append(
                f"coordinate.number_density adjusted from {current_density} to {required_density} because labels would overlap"
            )
        elif "number_density" not in explicit_coordinate:
            coordinate["number_density"] = max(1, current_density)

        return ScreenshotParamsResult(
            grid=grid,
            coordinate=coordinate,
            color_mode=color_mode or config.screenshot.default_color_mode,
            adaptive_adjustments=adjustments,
        )

    def _calculate_required_number_density(
        self,
        image_size: Tuple[int, int],
        density_x: float,
        density_y: float,
        number_size: int,
    ) -> int:
        width, height = image_size
        step_x = max(width * density_x / 100, 1)
        step_y = max(height * density_y / 100, 1)

        probe = Image.new("RGBA", (320, 120), (0, 0, 0, 0))
        draw = ImageDraw.Draw(probe)
        renderer = GridRenderer(number_size=number_size)
        font = renderer._load_font(number_size)
        separator_font = renderer._load_font(max(4, int(round(number_size * 0.5))))
        label_width, label_height = GridRenderer.measure_coordinate_text(
            draw, "100", "x", "100", font, separator_font
        )

        density_by_width = math.ceil(label_width / max(step_x * 0.95, 1))
        density_by_height = math.ceil(label_height / max(step_y * 0.65, 1))
        return max(1, min(4, max(density_by_width, density_by_height)))


screenshot_params_service = ScreenshotParamsService()
