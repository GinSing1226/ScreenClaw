"""
图片处理单元测试
"""
import pytest
import os
import tempfile
from PIL import Image

from app.utils.image import (
    compress_image,
    image_to_base64,
    base64_to_image,
    save_image,
    generate_screenshot_filename,
    generate_scroll_screenshot_filename,
    generate_crop_zoom_filename,
    generate_data_dir
)


class TestImageProcessing:
    """图片处理测试"""

    def test_compress_image_no_resize(self):
        """测试图片压缩 - 不需要缩放"""
        # 创建小图片
        image = Image.new("RGB", (800, 600), color="red")
        result = compress_image(image, quality=85, max_width=1920)

        # 尺寸不变
        assert result.size == (800, 600)

    def test_compress_image_with_resize(self):
        """测试图片压缩 - 需要缩放"""
        # 创建大图片
        image = Image.new("RGB", (3000, 2000), color="blue")
        result = compress_image(image, quality=85, max_width=1920)

        # 宽度被限制
        assert result.size[0] == 1920
        # 高度按比例缩放
        assert result.size[1] == int(2000 * 1920 / 3000)

    def test_image_to_base64_and_back(self):
        """测试base64转换往返"""
        image = Image.new("RGB", (100, 100), color="green")

        # 转base64
        base64_str = image_to_base64(image)
        assert len(base64_str) > 0

        # 转回来
        restored = base64_to_image(base64_str)
        assert restored.size == (100, 100)

    def test_save_image_png(self, tmp_path):
        """测试保存PNG图片"""
        image = Image.new("RGBA", (100, 100), color="red")
        filepath = os.path.join(tmp_path, "test.png")

        result = save_image(image, filepath)
        assert os.path.exists(filepath)
        assert result == filepath

    def test_save_image_jpeg(self, tmp_path):
        """测试保存JPEG图片"""
        image = Image.new("RGB", (100, 100), color="blue")
        filepath = os.path.join(tmp_path, "test.jpg")

        result = save_image(image, filepath, quality=85)
        assert os.path.exists(filepath)

    def test_generate_screenshot_filename(self):
        """测试生成截图文件名"""
        filename = generate_screenshot_filename()

        # 格式检查: screenshot_hhmmss_rand4.png
        assert filename.startswith("screenshot_")
        assert filename.endswith(".png")

        # 提取时间部分
        parts = filename.replace("screenshot_", "").replace(".png", "").split("_")
        assert len(parts) == 2
        assert len(parts[0]) == 6  # hhmmss
        assert len(parts[1]) == 4  # rand4

    def test_generate_data_dir(self, tmp_path, monkeypatch):
        """测试生成数据目录"""
        # Mock get_project_root 来返回 tmp_path
        from app.utils import image
        monkeypatch.setattr(image, "get_project_root", lambda: tmp_path)

        data_dir = generate_data_dir(
            "data",  # base_dir 现在只用于命名，实际路径由 get_project_root 决定
            "claude_code",
            "session_001"
        )

        assert os.path.exists(data_dir)
        assert "claude_code__session_001" in data_dir

        # 包含日期
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        assert date_str in data_dir

    def test_rgba_to_jpeg_conversion(self, tmp_path):
        """测试RGBA转JPEG"""
        # RGBA图片
        image = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        filepath = os.path.join(tmp_path, "test.jpg")

        # 保存为JPEG（应该自动转换）
        save_image(image, filepath, quality=85)
        assert os.path.exists(filepath)

        # 验证保存的图片是RGB模式
        loaded = Image.open(filepath)
        assert loaded.mode == "RGB"

    def test_generate_scroll_screenshot_filename(self):
        """测试生成滚动截图文件名"""
        filename = generate_scroll_screenshot_filename()

        assert filename.startswith("scroll_screenshot_")
        assert filename.endswith(".png")

        parts = filename.replace("scroll_screenshot_", "").replace(".png", "").split("_")
        assert len(parts) == 2
        assert len(parts[0]) == 6
        assert len(parts[1]) == 4

    def test_generate_crop_zoom_filename(self):
        """测试生成裁剪放大文件名"""
        filename = generate_crop_zoom_filename()

        assert filename.startswith("crop_zoom_")
        assert filename.endswith(".png")

        parts = filename.replace("crop_zoom_", "").replace(".png", "").split("_")
        assert len(parts) == 2
        assert len(parts[0]) == 6
        assert len(parts[1]) == 4
