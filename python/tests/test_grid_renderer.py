"""
Grid renderer layout tests.
"""
from PIL import Image, ImageDraw

from app.core.grid import GridRenderer


def test_coordinate_separator_is_centered_on_grid_intersection():
    renderer = GridRenderer(number_size=18)
    image = Image.new("RGBA", (240, 160), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = renderer._load_font(18)
    separator_font = renderer._load_font(9)
    anchor_x = 100
    anchor_y = 80

    layout = renderer._coordinate_text_layout(
        draw, anchor_x, anchor_y, "55", "x", "65", font, separator_font
    )
    sep_bbox = draw.textbbox(layout["sep"], "x", font=separator_font)

    assert round((sep_bbox[0] + sep_bbox[2]) / 2) == anchor_x
    assert round((sep_bbox[1] + sep_bbox[3]) / 2) == anchor_y


def test_coordinate_digits_sit_one_pixel_above_horizontal_line():
    renderer = GridRenderer(number_size=18)
    image = Image.new("RGBA", (240, 160), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = renderer._load_font(18)
    separator_font = renderer._load_font(9)
    anchor_x = 100
    anchor_y = 80

    layout = renderer._coordinate_text_layout(
        draw, anchor_x, anchor_y, "55", "x", "65", font, separator_font
    )
    left_bbox = draw.textbbox(layout["left"], "55", font=font)
    right_bbox = draw.textbbox(layout["right"], "65", font=font)

    assert left_bbox[3] == anchor_y - 1
    assert right_bbox[3] == anchor_y - 1
