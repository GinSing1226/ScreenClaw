"""
滚动长截图服务

核心业务逻辑：自适应滚动、固定区域检测、智能拼接
"""

import time
import os
from pathlib import Path
from typing import Tuple, List, Optional
from PIL import Image
from dataclasses import dataclass

from app.models.request import ScrollScreenshotRequest
from app.models.response import ScrollScreenshotData, ScrollScreenshotResponse
from app.models.config import ScrollScreenshotConfig
from app.platform.windows.capture import windows_capture
from app.platform.windows.input import windows_input
from app.utils.scroll_stitch import (
    detect_fixed_header,
    detect_fixed_footer,
    find_content_bounds,
    find_overlap_by_rows,
    calculate_content_change_ratio,
    stitch_images_vertical
)


@dataclass
class ScrollScreenshotResult:
    """滚动长截图内部结果（包含 PIL Image，不用于序列化）"""
    success: bool
    message: str
    image: Optional[Image.Image] = None
    scroll_count: int = 0
    actual_scroll_percent: float = 0.0
    fixed_header: int = 0
    fixed_footer: int = 0


class ScrollScreenshotService:
    """滚动长截图服务"""

    def __init__(self, config: ScrollScreenshotConfig):
        """初始化服务

        Args:
            config: 滚动长截图配置
        """
        self.config = config

    def execute(self, request: ScrollScreenshotRequest, hwnd: int,
                virtual_x: int, virtual_y: int) -> ScrollScreenshotResult:
        """执行滚动长截图

        Args:
            request: 请求参数
            hwnd: 目标窗口句柄
            virtual_x: 滚动位置虚拟坐标 X
            virtual_y: 滚动位置虚拟坐标 Y

        Returns:
            ScrollScreenshotResult: 内部结果（包含 PIL Image）
        """
        start_time = time.time()

        # 参数限制（安全边界）
        max_scrolls = min(request.max_scrolls, self.config.max_scrolls)
        scroll_wait = min(request.scroll_wait, self.config.max_scroll_wait)

        # 计算超时时间
        timeout = self._calculate_timeout(request)

        print(f"\n--- 滚动长截图开始 ---")
        print(f"  hwnd: {hwnd}")
        print(f"  max_scrolls: {max_scrolls} (请求: {request.max_scrolls})")
        print(f"  scroll_wait: {scroll_wait}s (请求: {request.scroll_wait}s)")
        print(f"  initial_scroll_percent: {request.scroll_percent * 100:.0f}%")
        print(f"  timeout: {timeout}s")

        try:
            # 执行滚动截图（内部硬编码 hijack 模式）
            screenshots, fixed_header, first_overlap, actual_scroll_percent = self._scroll_screenshot(
                hwnd, max_scrolls, request.scroll_percent, scroll_wait,
                request.max_adjust_retries,
                request.target_overlap_min, request.target_overlap_max,
                request.stop_threshold, timeout, start_time,
                virtual_x, virtual_y, request.session_id
            )

            if not screenshots:
                return ScrollScreenshotResult(
                    success=False,
                    message="Failed to capture screenshots"
                )

            # 拼接
            if len(screenshots) == 1:
                print("\n只有一张截图，无需拼接")
                result = screenshots[0]
            else:
                print(f"\n开始拼接 {len(screenshots)} 张截图...")
                stitch_start = time.time()
                result = stitch_images_vertical(
                    screenshots,
                    scroll_percent=actual_scroll_percent,
                    reference_overlap=first_overlap,
                    verbose=True
                )
                elapsed = time.time() - stitch_start
                print(f"拼接完成，耗时 {elapsed:.2f}秒")

            # 获取固定区域信息
            fixed_footer = 0
            if len(screenshots) >= 2:
                fixed_footer = detect_fixed_footer(screenshots[0], screenshots[1])

            duration_ms = int((time.time() - start_time) * 1000)

            print(f"\n--- 滚动长截图完成 ---")
            print(f"  截图数量: {len(screenshots)}")
            print(f"  最终图片尺寸: {result.size}")
            print(f"  耗时: {duration_ms}ms")

            return ScrollScreenshotResult(
                success=True,
                message="Command sent.",
                image=result,
                scroll_count=len(screenshots),
                actual_scroll_percent=actual_scroll_percent,
                fixed_header=fixed_header,
                fixed_footer=fixed_footer
            )

        except TimeoutError as e:
            return ScrollScreenshotResult(
                success=False,
                message=f"Operation timeout: {str(e)}"
            )
        except Exception as e:
            return ScrollScreenshotResult(
                success=False,
                message=f"Internal error: {str(e)}"
            )

    def _calculate_timeout(self, request: ScrollScreenshotRequest) -> int:
        """计算超时时间（方案C：双重限制）

        超时 = min(参数计算值, 全局上限)
        """
        calculated_timeout = int(
            min(request.max_scrolls, self.config.max_scrolls) *
            min(request.scroll_wait, self.config.max_scroll_wait) * 2 + 60
        )
        return min(calculated_timeout, self.config.max_timeout)

    def _check_timeout(self, start_time: float, timeout: int):
        """检查是否超时"""
        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise TimeoutError(f"Scroll screenshot timeout after {timeout}s")

    def _scroll_screenshot(
        self,
        hwnd: int,
        max_scrolls: int,
        scroll_percent: float,
        scroll_wait: float,
        max_adjust_retries: int,
        target_overlap_min: float,
        target_overlap_max: float,
        stop_threshold: float,
        timeout: int,
        start_time: float,
        virtual_x: int,
        virtual_y: int,
        session_id: str
    ) -> Tuple[List[Image.Image], int, Optional[int], float]:
        """执行滚动截图（自适应 scroll_percent）

        Returns:
            (screenshots, fixed_header, first_overlap, actual_scroll_percent):
                - screenshots: 裁剪后的图片列表
                - fixed_header: 固定头部高度
                - first_overlap: 第一对的重叠量（用于后续拼接约束）
                - actual_scroll_percent: 实际使用的滚动幅度
        """
        cropped_images = []  # 直接存储裁剪后的图片

        # 截取第一屏
        print(f"\n--- 阶段1: 初始截图 ---")
        print(f"  [1/{max_scrolls}] 截取初始屏幕...")
        capture_result = windows_capture.capture(hwnd)
        if not capture_result.success or capture_result.image is None:
            print(f"  初始截图失败: {capture_result.error}")
            return ([], 0, None, scroll_percent)
        img1 = capture_result.image
        print(f"  已截图: {img1.size}")

        # ========== 自适应阶段：截取 3 张图片检测最佳滚动参数 ==========
        print(f"\n--- 阶段2: 自适应滚动检测 ---")

        # 自适应参数
        MIN_OVERLAP_RATIO = 0.15
        MAX_OVERLAP_RATIO = 0.50
        INCREASE_SCROLL_FACTOR = 1.3
        DECREASE_SCROLL_FACTOR = 0.7

        actual_scroll_percent = scroll_percent
        first_overlap = None
        last_scroll_percent = scroll_percent  # 上次滚动使用的幅度（用于回滚）

        # 吸顶检测阈值（像素）：小于此值可能是滚动幅度不够，需要继续检测
        STICKY_HEADER_THRESHOLD = 30

        print(f"  目标重叠区间: [{target_overlap_min*100:.0f}%, {target_overlap_max*100:.0f}%]")
        print(f"  可接受范围: [{MIN_OVERLAP_RATIO*100:.0f}%, {MAX_OVERLAP_RATIO*100:.0f}%]")
        print(f"  最大调整次数: {max_adjust_retries}")

        for retry in range(max_adjust_retries + 1):
            self._check_timeout(start_time, timeout)

            print(f"\n  [重试 {retry + 1}/{max_adjust_retries + 1}] 滚动幅度={actual_scroll_percent*100:.0f}%")

            # 保存本次要使用的幅度（用于下次回滚）
            used_scroll_percent = actual_scroll_percent

            # 回滚到 img1 位置（retry=0 时不需要回滚）
            if retry > 0:
                print(f"  回滚 2 次到 img1 位置（使用上次滚动幅度 {last_scroll_percent*100:.0f}%）...")
                self._scroll_up(hwnd, last_scroll_percent, "hijack", virtual_x, virtual_y)
                time.sleep(scroll_wait)
                self._scroll_up(hwnd, last_scroll_percent, "hijack", virtual_x, virtual_y)
                time.sleep(scroll_wait)

            # 截取 img2
            self._scroll_down(hwnd, used_scroll_percent, "hijack", virtual_x, virtual_y)
            time.sleep(scroll_wait)

            print(f"  [2/{max_scrolls}] 截图中...")
            capture_result = windows_capture.capture(hwnd)
            if not capture_result.success or capture_result.image is None:
                print(f"  截图失败，停止")
                return ([], 0, None, scroll_percent)
            img2 = capture_result.image

            # 截取 img3
            self._scroll_down(hwnd, used_scroll_percent, "hijack", virtual_x, virtual_y)
            time.sleep(scroll_wait)

            print(f"  [3/{max_scrolls}] 截图中...")
            capture_result = windows_capture.capture(hwnd)
            if not capture_result.success or capture_result.image is None:
                print(f"  截图失败，仅用 img2")
                img3 = None
            else:
                img3 = capture_result.image

            # ====== Step 1: 检测固定区域（用原始图） ======
            w1, h1 = img1.size
            w2, h2 = img2.size

            # [1对2] 检测固定头部和固定底部
            header_12 = detect_fixed_header(img1, img2)
            footer_12 = detect_fixed_footer(img1, img2)
            print(f"    [1对2] 固定头部={header_12}px, 固定底部={footer_12}px")

            # [2对3] 检测吸顶头部和悬浮底部
            header_23 = header_12  # 默认值
            footer_23 = footer_12  # 默认值
            sticky_header = 0
            floating_footer = 0
            img4 = None

            if img3:
                header_23 = detect_fixed_header(img2, img3)
                footer_23 = detect_fixed_footer(img2, img3)
                print(f"    [2对3] 固定头部={header_23}px, 固定底部={footer_23}px")

                # 计算差异，判断吸顶是否可能存在但滚动幅度不够
                header_diff = header_23 - header_12
                footer_diff = footer_23 - footer_12

                if header_diff < STICKY_HEADER_THRESHOLD and header_23 < h1 * 0.15:
                    # 差异太小，可能是滚动幅度不够，吸顶还没出现
                    # 继续滚动到 img4 检测
                    print(f"    [2对3] 差异={header_diff}px < {STICKY_HEADER_THRESHOLD}px，吸顶可能未出现，继续滚动到 img4...")
                    self._scroll_down(hwnd, used_scroll_percent, "hijack", virtual_x, virtual_y)
                    time.sleep(scroll_wait)

                    print(f"  [4/{max_scrolls}] 截图中...")
                    capture_result = windows_capture.capture(hwnd)
                    if capture_result.success and capture_result.image:
                        img4 = capture_result.image
                        header_34 = detect_fixed_header(img3, img4)
                        footer_34 = detect_fixed_footer(img3, img4)
                        print(f"    [3对4] 固定头部={header_34}px, 固定底部={footer_34}px")

                        # 用 [3对4] 重新计算吸顶
                        header_23 = max(header_23, header_34)
                        footer_23 = max(footer_23, footer_34)
                        print(f"    更新 [2对3] 为 max([2对3], [3对4]) = {header_23}px")

                # 重新计算吸顶头部和悬浮底部
                if header_23 > header_12:
                    sticky_header = header_23 - header_12
                if footer_23 > footer_12:
                    floating_footer = footer_23 - footer_12

            print(f"    固定头部={header_12}px, 吸顶头部={sticky_header}px, "
                  f"固定底部={footer_12}px, 悬浮底部={floating_footer}px")

            # ====== Step 2: 裁剪成纯内容 ======
            # img1: 裁掉固定底部
            # img2/img3/img4: 裁掉(固定头部+吸顶头部) + 裁掉(固定底部+悬浮底部)
            crop_header = header_12 + sticky_header  # img2/img3 需要裁掉的头部
            crop_footer = footer_12 + floating_footer  # img2/img3 需要裁掉的底部

            img1_cropped = img1.crop((0, 0, w1, h1 - footer_12))
            img2_cropped = img2.crop((0, crop_header, w2, h2 - crop_footer))
            print(f"    [裁剪] img1: 保留头部，裁底部{footer_12}px → {img1_cropped.size}")
            print(f"    [裁剪] img2: 裁头部{crop_header}px + 底部{crop_footer}px → {img2_cropped.size}")

            # 裁剪 img3 和 img4
            img3_cropped = None
            img4_cropped = None
            if img3:
                w3, h3 = img3.size
                img3_cropped = img3.crop((0, crop_header, w3, h3 - crop_footer))
                print(f"    [裁剪] img3: 裁头部{crop_header}px + 底部{crop_footer}px → {img3_cropped.size}")
            if img4:
                w4, h4 = img4.size
                img4_cropped = img4.crop((0, crop_header, w4, h4 - crop_footer))
                print(f"    [裁剪] img4: 裁头部{crop_header}px + 底部{crop_footer}px → {img4_cropped.size}")

            # ====== Step 3: 计算重叠（在纯内容图上） ======
            # 优先用 img2/img3 检测重叠（更准确的滚动参数）
            # 如果 img3 不存在，才用 img1/img2
            temp_bounds = find_content_bounds(img2_cropped)
            print(f"    [内容区] 左右边界: [{temp_bounds[0]}:{temp_bounds[1]}]")

            expect_ratio = 1.0 - actual_scroll_percent

            if img3_cropped:
                # 用 img2/img3 检测重叠
                overlap_23 = find_overlap_by_rows(
                    img2_cropped, img3_cropped, expect_ratio, temp_bounds, verbose=True
                )
                ratio_23 = overlap_23 / img3_cropped.height if img3_cropped.height > 0 else 0
                print(f"    [2对3] 重叠={overlap_23}px / {img3_cropped.height}px = {ratio_23*100:.1f}%")
                overlap_for_adjust = overlap_23
                ratio_for_adjust = ratio_23
            else:
                # 用 img1/img2 检测重叠
                overlap_12 = find_overlap_by_rows(
                    img1_cropped, img2_cropped, expect_ratio, temp_bounds, verbose=True
                )
                ratio_12 = overlap_12 / img2_cropped.height if img2_cropped.height > 0 else 0
                print(f"    [1对2] 重叠={overlap_12}px / {img2_cropped.height}px = {ratio_12*100:.1f}%")
                overlap_for_adjust = overlap_12
                ratio_for_adjust = ratio_12

            # 判断是否需要调整
            if target_overlap_min <= ratio_for_adjust <= target_overlap_max:
                # 在目标区间内 → 接受
                first_overlap = overlap_for_adjust
                print(f"    ✓ 重叠完美 [{ratio_for_adjust*100:.1f}% ∈ [{target_overlap_min*100:.0f}%, {target_overlap_max*100:.0f}%]]")
                # 保存裁剪参数（用于后续裁剪）
                final_crop_header = crop_header
                final_crop_footer = crop_footer
                final_footer_12 = footer_12
                # 保存裁剪后的图片
                cropped_images.append(img1_cropped)
                cropped_images.append(img2_cropped)
                if img3_cropped:
                    cropped_images.append(img3_cropped)
                if img4_cropped:
                    cropped_images.append(img4_cropped)
                break
            elif MIN_OVERLAP_RATIO <= ratio_for_adjust <= MAX_OVERLAP_RATIO:
                # 在可接受范围但不在目标区间
                if retry < max_adjust_retries:
                    if ratio_for_adjust < target_overlap_min:
                        new_percent = actual_scroll_percent * DECREASE_SCROLL_FACTOR
                        print(f"    ⚠ 重叠偏低 ({ratio_for_adjust*100:.1f}% < {target_overlap_min*100:.0f}%)，尝试优化...")
                    else:
                        new_percent = actual_scroll_percent * INCREASE_SCROLL_FACTOR
                        print(f"    ⚠ 重叠偏高 ({ratio_for_adjust*100:.1f}% > {target_overlap_max*100:.0f}%)，尝试优化...")
                    actual_scroll_percent = min(new_percent, 0.95)
                    last_scroll_percent = used_scroll_percent  # 保存本次使用的幅度用于下次回滚
                    continue
                # 最后一次重试，接受当前结果
                first_overlap = overlap_for_adjust
                print(f"    ✓ 重叠可接受 [{ratio_for_adjust*100:.1f}% ∈ [{MIN_OVERLAP_RATIO*100:.0f}%, {MAX_OVERLAP_RATIO*100:.0f}%]]")
                # 保存裁剪参数（用于后续裁剪）
                final_crop_header = crop_header
                final_crop_footer = crop_footer
                final_footer_12 = footer_12
                # 保存裁剪后的图片
                cropped_images.append(img1_cropped)
                cropped_images.append(img2_cropped)
                if img3_cropped:
                    cropped_images.append(img3_cropped)
                if img4_cropped:
                    cropped_images.append(img4_cropped)
                break
            elif retry < max_adjust_retries:
                # 需要调整
                if ratio_for_adjust > MAX_OVERLAP_RATIO:
                    new_percent = actual_scroll_percent * INCREASE_SCROLL_FACTOR
                    print(f"    ✗ 重叠太大 ({ratio_for_adjust*100:.1f}% > {MAX_OVERLAP_RATIO*100:.0f}%) → 需要滚更多")
                else:
                    new_percent = actual_scroll_percent * DECREASE_SCROLL_FACTOR
                    print(f"    ✗ 重叠太小 ({ratio_for_adjust*100:.1f}% < {MIN_OVERLAP_RATIO*100:.0f}%) → 需要滚更少")
                actual_scroll_percent = min(new_percent, 0.95)
                last_scroll_percent = used_scroll_percent  # 保存本次使用的幅度用于下次回滚
            else:
                print(f"    达到最大重试次数，使用当前重叠")
                first_overlap = overlap_for_adjust
                # 保存裁剪参数（用于后续裁剪）
                final_crop_header = crop_header
                final_crop_footer = crop_footer
                final_footer_12 = footer_12
                # 保存裁剪后的图片
                cropped_images.append(img1_cropped)
                cropped_images.append(img2_cropped)
                if img3_cropped:
                    cropped_images.append(img3_cropped)
                if img4_cropped:
                    cropped_images.append(img4_cropped)
                break

        print(f"\n  【自适应】最终滚动幅度: {actual_scroll_percent*100:.0f}%")
        print(f"  【裁剪参数】头部={final_crop_header}px (固定+吸顶), 底部={final_crop_footer}px (固定+悬浮)")

        # ========== 继续后续滚动 ==========
        print(f"\n--- 阶段3: 继续滚动 ---")
        # 根据已截图数量确定起始索引
        start_index = len(cropped_images) + 1
        for i in range(start_index, max_scrolls + 1):
            self._check_timeout(start_time, timeout)

            self._scroll_down(hwnd, actual_scroll_percent, "hijack", virtual_x, virtual_y)
            time.sleep(scroll_wait)

            print(f"  [{i}/{max_scrolls}] 滚动后截图中...")
            capture_result = windows_capture.capture(hwnd)
            if not capture_result.success or capture_result.image is None:
                print(f"  截图失败，停止")
                break

            curr = capture_result.image

            # 先裁剪，再判断是否到底（确保比较相同尺寸的图）
            w, h = curr.size
            curr_cropped = curr.crop((0, final_crop_header, w, h - final_crop_footer))

            # 判断是否到底（用裁剪后的图比较）
            change_ratio = calculate_content_change_ratio(cropped_images[-1], curr_cropped)
            print(f"  内容变化率: {change_ratio:.6f} (停止阈值: {stop_threshold})")

            if change_ratio < stop_threshold:
                print(f"  内容未变化，已到底部")
                break

            cropped_images.append(curr_cropped)
            print(f"  已截图并裁剪: {curr.size} → {curr_cropped.size}")

        print(f"\n--- 阶段完成: 共 {len(cropped_images)} 张裁剪后的截图 ---")

        # 返回：裁剪后的图片列表、裁剪头部（固定+吸顶）、第一对重叠量、自适应调整后的实际滚动幅度
        return (cropped_images, final_crop_header, first_overlap, actual_scroll_percent)

    def _scroll_down(self, hwnd: int, scroll_percent: float, action_method: str,
                     virtual_x: int, virtual_y: int):
        """向下滚动（百分比）

        Args:
            hwnd: 窗口句柄
            scroll_percent: 滚动幅度（百分比）
            action_method: 操作方式
            virtual_x: 滚动位置虚拟坐标 X
            virtual_y: 滚动位置虚拟坐标 Y
        """
        rect = self._get_client_rect(hwnd)
        if not rect:
            return

        client_height = rect[3] - rect[1]

        # 估算 delta
        target_pixels = int(client_height * scroll_percent)
        estimated_ticks = max(1, target_pixels // (client_height // 10))
        delta = -120 * estimated_ticks  # 负值向下

        # 调用滚动（使用传入的虚拟坐标）
        windows_input.scroll(hwnd, virtual_x, virtual_y, virtual_x, virtual_y, delta, action_method)

    def _scroll_up(self, hwnd: int, scroll_percent: float, action_method: str,
                    virtual_x: int, virtual_y: int):
        """向上滚动（百分比，回滚用）

        Args:
            hwnd: 窗口句柄
            scroll_percent: 滚动幅度（百分比）
            action_method: 操作方式
            virtual_x: 滚动位置虚拟坐标 X
            virtual_y: 滚动位置虚拟坐标 Y
        """
        rect = self._get_client_rect(hwnd)
        if not rect:
            return

        client_height = rect[3] - rect[1]

        # 估算 delta
        target_pixels = int(client_height * scroll_percent)
        estimated_ticks = max(1, target_pixels // (client_height // 10))
        delta = 120 * estimated_ticks  # 正值向上

        # 调用滚动（使用传入的虚拟坐标）
        windows_input.scroll(hwnd, virtual_x, virtual_y, virtual_x, virtual_y, delta, action_method)

    def _get_client_rect(self, hwnd: int):
        """获取窗口客户区"""
        try:
            import win32gui
            return win32gui.GetClientRect(hwnd)
        except:
            return None
