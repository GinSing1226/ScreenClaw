#!/usr/bin/env python3
"""
	ScreenClaw 裁剪放大截图脚本（专用）

	用法：python crop_zoom_screenshot_cli.py <api_url> <token> <source_image_path> <session_id> <ai_app_type> center_x=<值> center_y=<值> crop_width=<值> crop_height=<值> [zoom_scale=<值>]

	参数说明：
	  api_url            - ScreenClaw服务地址
	  token              - 认证令牌
	  source_image_path  - 原始图片路径（screenshot或scroll_screenshot返回的路径）
	  session_id         - 会话ID（必需）
	  ai_app_type        - AI应用类型（必需）

	裁剪参数（必需）：
	  center_x=<值>      - 裁剪区域中心点横坐标百分比(0-100)
	  center_y=<值>      - 裁剪区域中心点纵坐标百分比(0-100)
	  crop_width=<值>    - 裁剪区域总宽度百分比(0-100)
	  crop_height=<值>   - 裁剪区域总高度百分比(0-100)

	可选参数：
	  zoom_scale=<值>    - 放大倍数(1.0-10.0)，默认2.0

	说明：
	  - 本地请求返回image_path，远程请求返回image_base64（脚本自动保存）
	  - 远程场景的保存目录与原始截图相同，便于管理

	降级路径：本脚本 → crop_zoom_screenshot_cli.ps1 → crop_zoom_screenshot_cli.sh
"""

import sys
import json
import base64
import os
from pathlib import Path
try:
	import requests
except ImportError:
	print("错误：缺少 requests 模块")
	print("请安装：pip install requests")
	sys.exit(1)


def parse_params(param_args):
	"""解析命令行参数为字典"""
	params = {}
	for arg in param_args:
		if '=' in arg:
			key, value = arg.split('=', 1)
			if '.' in value:
				try:
					value = float(value)
				except ValueError:
					pass
			elif value.isdigit():
				value = int(value)
			params[key] = value
	return params


def process_result(result, api_url, source_image_path, session_id=None, ai_app_type=None):
	"""处理API响应结果"""
	if not result.get("success"):
		print(f"API 错误: {result.get('message', 'Unknown error')}")
		return None

	data = result.get("data", {})
	is_local = any(indicator in api_url.lower() for indicator in ["localhost", "127.0.0.1", "::1"])

	if is_local:
		return data.get("image_path")
	else:
		image_base64 = data.get("image_base64")
		if not image_base64:
			print("API 错误: 远程响应中没有image_base64")
			return None

		from datetime import datetime
		import random
		import string

		if session_id is None:
			session_id = "default"
		if ai_app_type is None:
			ai_app_type = "claude_code"

		date_str = datetime.now().strftime("%Y-%m-%d")
		dir_name = f"{ai_app_type}__{session_id}__{date_str}"

		time_str = datetime.now().strftime("%H%M%S")
		rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
		filename = f"crop_zoom_{time_str}_{rand_str}.png"

		if os.name == 'nt':
			base_dir = os.path.expandvars("%APPDATA%\\screenclaw\\data")
		else:
			base_dir = os.path.expanduser("~/.local/share/screenclaw/data")

		output_dir = Path(base_dir) / dir_name
		output_dir.mkdir(parents=True, exist_ok=True)

		output_path = output_dir / filename
		with open(output_path, "wb") as f:
			f.write(base64.b64decode(image_base64))

		return str(output_path)


def main():
	if len(sys.argv) < 5:
		print(__doc__)
		sys.exit(1)

	api_url = sys.argv[1]
	token = sys.argv[2]
	source_image_path = sys.argv[3]
	session_id = sys.argv[4]
	ai_app_type = sys.argv[5]
	param_args = sys.argv[6:]

	params = parse_params(param_args)

	# 必填检查
	for required in ['center_x', 'center_y', 'crop_width', 'crop_height']:
		if required not in params:
			print(f"错误：缺少必需参数 {required}")
			sys.exit(1)

	# 构建body
	body = {
		"ai_app_type": ai_app_type,
		"session_id": session_id,
		"source_image_path": source_image_path,
		"center_x": params.pop('center_x'),
		"center_y": params.pop('center_y'),
		"crop_width": params.pop('crop_width'),
		"crop_height": params.pop('crop_height'),
	}
	# 可选参数
	if 'zoom_scale' in params:
		body['zoom_scale'] = params['zoom_scale']

	url = f"{api_url.rstrip('/')}/api/crop_zoom_screenshot"
	headers = {
		"Authorization": f"Bearer {token}",
		"Content-Type": "application/json"
	}

	try:
		response = requests.post(url, headers=headers, json=body, timeout=30)
		response.raise_for_status()
		result = response.json()
	except Exception as e:
		print(f"API 调用失败: {e}")
		sys.exit(1)

	output_path = process_result(result, api_url, source_image_path, session_id, ai_app_type)
	if output_path:
		print(output_path)
		print("Crop zoom successful. If details are still unclear, adjust parameters and process the same source image again.")


if __name__ == "__main__":
	main()
