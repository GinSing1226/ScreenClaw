#!/usr/bin/env python3
"""
ScreenClaw Batch 结果处理脚本

用于处理 batch API 的响应，特别是处理包含截图指令的结果。
"""

import json
import base64
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


def is_localhost(api_url: str) -> bool:
    """判断 API 地址是否为本地地址"""
    localhost_indicators = ["localhost", "127.0.0.1", "::1"]
    return any(indicator in api_url.lower() for indicator in localhost_indicators)


def process_batch_results_local(results: List[Dict[str, Any]]) -> List[str]:
    """
    本地调用场景：直接使用 image_path

    Args:
        results: batch API 返回的 results 数组

    Returns:
        处理后的输出列表
    """
    output = []

    for item in results:
        if item.get("data", {}).get("image_path"):
            # 截图指令，直接使用本地路径
            image_path = item["data"]["image_path"]
            output.append(f"![screenshot](file:///{image_path})")
        else:
            output.append(item.get("message", ""))

    return output


def process_batch_results_lan(
    results: List[Dict[str, Any]]
) -> List[str]:
    """
    局域网调用场景：解码 image_base64 并保存

    从 API 返回的 image_path 中提取目录名和文件名，保持与 ScreenClaw 本地相同的结构。

    Args:
        results: batch API 返回的 results 数组

    Returns:
        处理后的输出列表（图片为本地路径）
    """
    output = []

    # 确定保存路径
    if os.name == 'nt':  # Windows
        base_dir = os.path.expandvars("%APPDATA%\\screenclaw\\data")
    else:  # Linux/macOS
        base_dir = os.path.expanduser("~/.local/share/screenclaw/data")

    for item in results:
        if item.get("data", {}).get("image_base64"):
            # 截图指令 - 局域网场景
            data = item["data"]
            image_base64 = data["image_base64"]
            original_path = Path(data["image_path"])

            # 提取目录名和文件名
            # 原路径格式：D:/screenClaw/data/{dir_name}/{filename}
            dir_name = original_path.parent.name
            filename = original_path.name

            output_dir = Path(base_dir) / dir_name
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / filename

            # 保存图片
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(image_base64))

            output.append(f"![screenshot]({output_path})")
        else:
            output.append(item.get("message", ""))

    return output


def process_batch_results(
    results: List[Dict[str, Any]],
    api_url: str
) -> List[str]:
    """
    自动判断场景并处理 batch 结果

    Args:
        results: batch API 返回的 results 数组
        api_url: API URL（用于判断本地/局域网）

    Returns:
        处理后的输出列表
    """
    if is_localhost(api_url):
        return process_batch_results_local(results)
    else:
        return process_batch_results_lan(results)


def build_batch_instructions(scenario_template: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从场景模板构建 batch instructions

    Args:
        scenario_template: 场景模板（包含操作步骤）

    Returns:
        batch instructions 数组
    """
    instructions = []

    for step in scenario_template.get("steps", []):
        action = step["action"]
        params = step.get("params", {})

        instruction = {"action": action, "params": params}

        # 如果有等待时间，添加 wait 指令
        if "wait_ms" in step:
            instructions.append(instruction)
            instructions.append({
                "action": "wait",
                "params": {"duration_ms": step["wait_ms"]}
            })
        else:
            instructions.append(instruction)

    return instructions


# CLI 使用示例
if __name__ == "__main__":
    import sys

    # 示例：从文件读取 batch 结果并处理
    if len(sys.argv) >= 2:
        result_file = sys.argv[1]

        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = data.get("data", {}).get("results", [])
        api_url = data.get("api_url", "http://localhost:12261")

        output = process_batch_results(results, api_url)

        print("\n".join(output))
    else:
        print("Usage: python batch_results_processor.py <result_json_file>")
