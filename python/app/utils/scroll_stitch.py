"""
滚动长截图拼接算法工具

从测试脚本迁移的核心算法，用于滚动截图的智能拼接。
包含：固定区域检测、内容边界检测、四重验证重叠检测、垂直拼接。
"""

import numpy as np
from PIL import Image
from typing import Tuple, List, Optional


# ============== 算法参数 ==============

# 固定区域检测参数
FIXED_REGION_THRESHOLD = 0.98  # 相似度阈值
FIXED_REGION_MAX_CHECK_HEADER = 300  # 头部最大检查高度
FIXED_REGION_MAX_CHECK_FOOTER = 200  # 底部最大检查高度
FIXED_REGION_MAX_RATIO = 0.25  # 最大检查比例（图片高度的25%）

# 重叠检测参数（四重验证）
PIXEL_TOLERANCE = 3  # ±3 灰度误差
MIN_MATCH_RATIO = 0.60  # 单行匹配率阈值 60%
MIN_CONSECUTIVE_ROWS = 50  # 至少50行连续高匹配
MIN_UNIFORM_COVERAGE = 0.70  # 至少70%的重叠区域应该是高匹配行
MAX_CONTENT_CHANGE_RATIO = 0.08  # 内容变化率阈值：真实重叠应该<8%

# 内容边界检测参数
CONTENT_BOUND_MARGIN = 5  # 边界留白
CONTENT_COLUMN_DIFF_THRESHOLD = 10  # 列差异阈值


# ============== 1. 固定区域检测 ==============

def detect_fixed_header(img1: Image.Image, img2: Image.Image,
                       threshold: float = FIXED_REGION_THRESHOLD) -> int:
    """检测固定头部高度（不随滚动变化的区域）

    原理：从顶部逐行比较两张图，找到第一个不同的行。

    Args:
        img1: 第一张截图
        img2: 第二张截图
        threshold: 相似度阈值（0-1），默认0.98

    Returns:
        fixed_header_height: 固定头部高度（像素）
    """
    arr1 = np.array(img1)
    arr2 = np.array(img2)
    h = min(arr1.shape[0], arr2.shape[0])

    max_check = min(int(h * FIXED_REGION_MAX_RATIO), FIXED_REGION_MAX_CHECK_HEADER)

    fixed_end = 0
    for y in range(max_check):
        row1 = arr1[y]
        row2 = arr2[y]
        diff = np.abs(row1.astype(int) - row2.astype(int))
        sim = 1.0 - (np.mean(diff) / 255.0)
        if sim < threshold:
            fixed_end = y
            break

    if fixed_end == 0:
        fixed_end = max_check

    return fixed_end


def detect_fixed_footer(img1: Image.Image, img2: Image.Image,
                       threshold: float = FIXED_REGION_THRESHOLD) -> int:
    """检测固定底部高度（不随滚动变化的区域）

    Args:
        img1: 第一张截图
        img2: 第二张截图
        threshold: 相似度阈值（0-1），默认0.98

    Returns:
        fixed_footer_height: 固定底部高度（像素）
    """
    arr1 = np.array(img1)
    arr2 = np.array(img2)
    h = min(arr1.shape[0], arr2.shape[0])

    max_check = min(int(h * FIXED_REGION_MAX_RATIO), FIXED_REGION_MAX_CHECK_FOOTER)

    fixed_end = 0
    for y in range(1, max_check + 1):
        row1 = arr1[-y]
        row2 = arr2[-y]
        diff = np.abs(row1.astype(int) - row2.astype(int))
        sim = 1.0 - (np.mean(diff) / 255.0)
        if sim < threshold:
            fixed_end = y - 1
            break

    return fixed_end


# ============== 2. 内容区域检测 ==============

def find_content_bounds(img: Image.Image) -> Tuple[int, int]:
    """检测图像中实际内容的左右边界

    原理：检测左右两侧的纯色区域（背景），向内找到内容边界。
    在 4K 高分辨率下，空白侧边区域可能占宽度的大部分，
    必须排除这些区域，只在实际内容列上做行比较。

    Args:
        img: PIL Image

    Returns:
        (left, right): 内容区域的左右边界（像素坐标）
    """
    gray = np.array(img.convert('L'))
    h, w = gray.shape

    # 取左右边缘的背景色（众数）
    left_edge = gray[:, :5].flatten()
    right_edge = gray[:, -5:].flatten()
    edges = np.concatenate([left_edge, right_edge])
    bg_color = int(np.median(edges))

    # 检测左边界：从左往右找第一个与背景色不同的列
    left = 0
    for x in range(0, w // 3):
        col_diff = np.mean(np.abs(gray[:, x].astype(int) - bg_color))
        if col_diff > CONTENT_COLUMN_DIFF_THRESHOLD:
            left = x
            break

    # 检测右边界：从右往左找第一个与背景色不同的列
    right = w
    for x in range(w - 1, 2 * w // 3 - 1, -1):
        col_diff = np.mean(np.abs(gray[:, x].astype(int) - bg_color))
        if col_diff > CONTENT_COLUMN_DIFF_THRESHOLD:
            right = x + 1
            break

    # 留白
    left = max(0, left - CONTENT_BOUND_MARGIN)
    right = min(w, right + CONTENT_BOUND_MARGIN)

    return (left, right)


# ============== 3. 内容变化检测 ==============

def calculate_content_change_ratio(prev_img: Image.Image, curr_img: Image.Image) -> float:
    """计算两张截图内容区域的变化程度

    设计说明：
    1. 不缩放（保留一行文字级别的细节）
    2. 仅排除左右空白边距（find_content_bounds），不排除上下
       - 调用方传入的图片已经裁掉了固定头部/底部，无需二次排除
    3. 用"显著变化像素占比"代替MSE（更直观、更可控）

    Args:
        prev_img: 前一张截图（已裁剪固定头尾）
        curr_img: 当前截图（已裁剪固定头尾）

    Returns:
        ratio: 0~1，显著变化的像素占总像素的比例
               0 = 完全相同，1 = 完全不同
    """
    if prev_img.size != curr_img.size:
        return 1.0

    arr1 = np.array(prev_img.convert('L'), dtype=np.int32)
    arr2 = np.array(curr_img.convert('L'), dtype=np.int32)

    # 检测左右内容边界，排除空白侧边栏
    left, right = find_content_bounds(prev_img)
    left = max(0, left - CONTENT_BOUND_MARGIN)
    right = min(arr1.shape[1], right + CONTENT_BOUND_MARGIN)

    region1 = arr1[:, left:right]
    region2 = arr2[:, left:right]

    diff = np.abs(region1 - region2)

    # 显著变化 = 差异>5灰度（排除渲染抖动/ClearType的1-2灰度波动）
    significant = np.count_nonzero(diff > 5)
    total = diff.size

    return significant / total if total > 0 else 0.0


# ============== 4. 行对比法重叠检测 ==============

def find_overlap_by_rows(
    top_img: Image.Image,
    btm_img: Image.Image,
    expect_ratio: float = 0.15,
    content_bounds: Optional[Tuple[int, int]] = None,
    verbose: bool = False
) -> int:
    """精确像素匹配 + 连续性验证 + 内容一致性验证：防止结构相似的假阳性

    策略：
    1. 遍历可能的 overlap 值
    2. 对每个 overlap，逐像素比较重叠区域
    3. 统计"精确匹配像素"比例（灰度差 ≤ ±3）
    4. 统计"连续高匹配行"数量（至少30行连续单行匹配率≥60%）
    5. 统计"均匀性"（至少70%的重叠区域应该是高匹配行）
    6. 统计"内容变化率"：真实重叠应该内容几乎完全相同（变化率<8%）
    7. 四重验证通过才判定为真实重叠
    8. 返回匹配比例最高的 overlap

    Args:
        top_img: 上方图片 (PIL Image)
        btm_img: 下方图片 (PIL Image)
        expect_ratio: 预期重叠比例
        content_bounds: (left, right) 内容区域边界
        verbose: 是否输出调试信息

    Returns:
        overlap_y: 垂直重叠量（像素），若无有效匹配则返回 0
    """
    # 转灰度：uint8 范围 0-255
    top_gray = np.array(top_img.convert('L'), dtype=np.uint8)
    btm_gray = np.array(btm_img.convert('L'), dtype=np.uint8)

    h_top, w_top = top_gray.shape[:2]
    h_btm, w_btm = btm_gray.shape[:2]

    expect_overlap_px = int(h_top * expect_ratio)

    # 搜索范围
    min_overlap = max(10, int(expect_overlap_px * 0.3))
    max_overlap = min(h_top - 10, h_btm - 10, int(expect_overlap_px * 2.0))

    # 确定比较列范围
    if content_bounds and content_bounds[1] > content_bounds[0]:
        cmp_x1, cmp_x2 = content_bounds
    else:
        cmp_x1 = max(50, w_top // 10)
        cmp_x2 = min(w_top, w_btm) - cmp_x1

    cmp_x1 = max(0, cmp_x1)
    cmp_x2 = min(cmp_x2, w_top, w_btm)

    if verbose:
        print(f"    [像素匹配] 上图={h_top}x{w_top}, 下图={h_btm}x{w_btm}")
        print(f"    [像素匹配] 预期={expect_overlap_px}px, 范围=[{min_overlap}:{max_overlap}]")
        print(f"    [像素匹配] 比较列=[{cmp_x1}:{cmp_x2}]")

    best_overlap = 0
    best_match_ratio = 0.0
    best_consecutive = 0
    best_uniformity = 0.0
    best_content_change = 1.0

    # 逐个测试 overlap 值
    for overlap in range(min_overlap, max_overlap + 1, 2):
        total_pixels = 0
        exact_match_pixels = 0
        consecutive_good_rows = 0
        max_consecutive = 0
        high_match_rows = 0
        significant_change_pixels = 0

        # 逐行比较
        for row_offset in range(0, overlap, 1):
            top_row = top_gray[h_top - overlap + row_offset, cmp_x1:cmp_x2]
            btm_row = btm_gray[row_offset, cmp_x1:cmp_x2]

            # 像素级比较
            diff = np.abs(top_row.astype(int) - btm_row.astype(int))
            exact_matches = diff <= PIXEL_TOLERANCE

            row_match_pixels = np.sum(exact_matches)
            row_total = len(diff)
            row_ratio = row_match_pixels / row_total if row_total > 0 else 0.0

            exact_match_pixels += row_match_pixels
            total_pixels += row_total

            # 统计显著内容变化（灰度差>10）
            significant_changes = diff > 10
            significant_change_pixels += np.sum(significant_changes)

            # 连续性验证
            if row_ratio >= MIN_MATCH_RATIO:
                consecutive_good_rows += 1
                max_consecutive = max(max_consecutive, consecutive_good_rows)
                high_match_rows += 1
            else:
                consecutive_good_rows = 0

        if total_pixels == 0:
            continue

        match_ratio = exact_match_pixels / total_pixels
        uniformity = high_match_rows / overlap if overlap > 0 else 0.0
        content_change_ratio = significant_change_pixels / total_pixels

        # 四重验证
        if (match_ratio >= MIN_MATCH_RATIO and
            max_consecutive >= MIN_CONSECUTIVE_ROWS and
            uniformity >= MIN_UNIFORM_COVERAGE and
            content_change_ratio <= MAX_CONTENT_CHANGE_RATIO):

            # 优先选择内容变化率更小的
            if content_change_ratio < best_content_change or (
                content_change_ratio == best_content_change and match_ratio > best_match_ratio
            ):
                best_match_ratio = match_ratio
                best_consecutive = max_consecutive
                best_uniformity = uniformity
                best_content_change = content_change_ratio
                best_overlap = overlap

    if best_overlap > 0 and verbose:
        ratio_pct = best_match_ratio * 100
        uniformity_pct = best_uniformity * 100
        content_change_pct = best_content_change * 100
        print(f"    [像素匹配] ✓ 找到真实重叠={best_overlap}px, "
              f"匹配率={ratio_pct:.1f}%, 连续行={best_consecutive}, "
              f"均匀性={uniformity_pct:.1f}%, 内容变化={content_change_pct:.1f}%")
    elif verbose:
        uniformity_pct = best_uniformity * 100 if best_uniformity > 0 else 0
        content_change_pct = best_content_change * 100 if best_content_change > 0 else 100
        print(f"    [像素匹配] ✗ 未找到有效重叠 "
              f"(最高匹配率={best_match_ratio*100:.1f}% < {MIN_MATCH_RATIO*100:.0f}% "
              f"或连续行<{MIN_CONSECUTIVE_ROWS} "
              f"或均匀性={uniformity_pct:.1f}% < {MIN_UNIFORM_COVERAGE*100:.0f}% "
              f"或内容变化={content_change_pct:.1f}% > {MAX_CONTENT_CHANGE_RATIO*100:.0f}%)")

    return best_overlap


# ============== 5. 垂直拼接 ==============

def stitch_images_vertical(
    images: List[Image.Image],
    scroll_percent: float = 0.85,
    reference_overlap: Optional[int] = None,
    verbose: bool = False
) -> Image.Image:
    """垂直拼接多张截图

    逻辑：
    1. 检测内容区域（排除4K空白侧边）
    2. 逐对 find_overlap_by_rows 找重叠量
    3. 用 reference_overlap 或中位数约束一致性
    4. 粘贴：result 完整保留 + curr 从 y_start 粘贴（覆盖重叠区域，保留一份）

    Args:
        images: PIL Image 列表
        scroll_percent: 滚动占窗口高度的比例
        reference_overlap: 参考重叠量（来自第一对的检测），用于约束后续对
        verbose: 是否输出调试信息

    Returns:
        拼接后的 PIL Image
    """
    if not images:
        return None

    if len(images) == 1:
        return images[0]

    expect_ratio = 1.0 - scroll_percent
    if verbose:
        print(f"  [拼接] 预期重叠比例: {expect_ratio:.2f}")
        if reference_overlap:
            print(f"  [拼接] 参考重叠量: {reference_overlap}px")

    # 检测所有图片的公共内容区域（排除空白侧边）
    all_bounds = [find_content_bounds(img) for img in images]
    common_left = max(b[0] for b in all_bounds)
    common_right = min(b[1] for b in all_bounds)
    content_bounds = (common_left, common_right)
    if verbose:
        print(f"  [拼接] 内容区域: [{common_left}:{common_right}]")

    # 计算每对之间的重叠量
    overlaps = []
    for i in range(1, len(images)):
        if verbose:
            print(f"  [拼接] 匹配第 {i}/{len(images) - 1} 对:")
        overlap = find_overlap_by_rows(
            images[i - 1], images[i], expect_ratio, content_bounds, verbose=verbose
        )
        # 上限：不能超过前一张图的高度
        prev_height = images[i - 1].height
        if overlap > prev_height:
            if verbose:
                print(f"    [拼接] 警告: overlap={overlap} > prev_height={prev_height}, 限制最大值")
            overlap = prev_height
        overlaps.append(overlap)

    if verbose:
        print(f"  [拼接] 检测到的重叠量: {overlaps}")

    # 对检测失败的重叠应用参考值
    if reference_overlap:
        final_overlaps = []
        for i, ov in enumerate(overlaps):
            if ov == 0:
                # 检测失败，用参考值
                final_overlaps.append(reference_overlap)
                if verbose:
                    print(f"  [拼接] 第{i+1}对: 检测失败({ov}px) → 使用参考值 {reference_overlap}px")
            else:
                # 检测成功，保持原值
                final_overlaps.append(ov)
        overlaps = final_overlaps
        if verbose:
            print(f"  [拼接] 最终重叠量: {overlaps}")

    # 拼接
    result = images[0]

    for i in range(1, len(images)):
        curr = images[i]
        overlap = overlaps[i - 1]

        y_start = result.height - overlap

        new_h = y_start + curr.height
        new_w = max(result.width, curr.width)
        canvas = Image.new('RGB', (new_w, new_h))

        # 粘贴上半部分（完整保留）
        canvas.paste(result, (0, 0))

        # 粘贴下半部分（完整 curr，overlap 区域覆盖 result 的同名区域，保留一份）
        canvas.paste(curr, (0, y_start))

        if verbose:
            print(f"    [合并] overlap={overlap}, y_start={y_start}, new_height={new_h}")

        result = canvas

    return result
