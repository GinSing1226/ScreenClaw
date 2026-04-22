#!/usr/bin/env python3
"""
	ScreenClaw 截图获取脚本（专用）

	用法：python fetch_screenshot_cli.py <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id> [参数...]

	参数说明：
	  api_url        - ScreenClaw服务地址
	  token          - 认证令牌
	  window_id      - 窗口ID
	  session_id     - 会话ID（必需）
	  ai_app_type    - AI应用类型（必需）
	  main_window_id - 主窗口ID（必需，从get_window_list获取）

	网格参数（可选）：
	  grid_density_x=<值>     - 水平网格密度百分比，值越小网格越密，默认5.0，支持小数
	  grid_density_y=<值>     - 垂直网格密度百分比，值越小网格越密，默认5.0，支持小数
	  grid_opacity=<值>       - 网格透明度(0-100)，默认50
	  grid_color=<值>         - 网格颜色，默认#ff0000

	颜色模式（可选）：
	  color_mode=<值>         - 颜色模式：grayscale（灰度）/color（原色），默认grayscale

	数字参数（可选）：
	  number_density=<值>     - 数字密度，默认2
	  number_decimal=<值>      - 小数位数(0-4)，默认0
	  number_size=<值>         - 字体大小(4-32)，默认12
	  number_color=<值>        - 数字颜色，默认#ff0000
	  number_opacity=<值>      - 数字透明度(0-100)，默认100

	标记点参数（可选，支持多个，用序号区分）：
	  marker_1_x=<值>         - 第1个标记点横坐标，marker_1_x和marker_1_y同时传才生效
	  marker_1_y=<值>         - 第1个标记点纵坐标
	  marker_1_ring_color=<值>- 第1个标记点外圈颜色，默认#FF0000
	  marker_2_x=<值>         - 第2个标记点横坐标（不同颜色区分）
	  marker_2_y=<值>         - 第2个标记点纵坐标
	  向后兼容：marker_x/marker_y 等同于 marker_1_x/marker_1_y

	说明：
	  - 远程场景的截图保存目录规则：{ai_app_type}__{session_id}__{yyyy-MM-dd}/
	  - 同一会话的所有截图都保存在同一目录下，便于追踪

	降级路径：本脚本 → fetch_screenshot_cli.ps1 → fetch_screenshot_cli.sh
"""

import sys
import json
import base64
import os
import tempfile
from pathlib import Path
try:
	import requests
except ImportError:
	print("错误：缺少 requests 模块")
	print("请安装：pip install requests")
	sys.exit(1)


def process_result(result, api_url, session_id=None, ai_app_type=None, window_id=None):
	"""处理API响应结果"""
	if not result.get("success"):
		print(f"API 错误: {result.get('message', 'Unknown error')}")
		return None

	data = result.get("data", {})
	is_local = any(indicator in api_url.lower() for indicator in ["localhost", "127.0.0.1", "::1"])

	if is_local:
		# 本地场景：服务端返回image_path，直接使用
		return data.get("image_path")
	else:
		# 远程场景：服务端只返回base64，客户端自己生成符合规则的路径
		# 目录规则：{ai_app_type}__{session_id}__{yyyy-MM-dd}
		# 文件规则：screenshot_{HHMMSS}_{rand4}.png
		image_base64 = data.get("image_base64")
		if not image_base64:
			print("API 错误: 远程响应中没有image_base64")
			return None

		from datetime import datetime
		import random
		import string

		# 如果没有提供参数，尝试从响应中推断或使用默认值
		if session_id is None:
			session_id = "default"
		if ai_app_type is None:
			ai_app_type = "claude_code"

		date_str = datetime.now().strftime("%Y-%m-%d")
		dir_name = f"{ai_app_type}__{session_id}__{date_str}"

		time_str = datetime.now().strftime("%H%M%S")
		rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
		filename = f"screenshot_{time_str}_{rand_str}.png"

		# 确定保存目录
		if os.name == 'nt':  # Windows
			base_dir = os.path.expandvars("%APPDATA%\\screenclaw\\data")
		else:  # Linux/macOS
			base_dir = os.path.expanduser("~/.local/share/screenclaw/data")

		output_dir = Path(base_dir) / dir_name
		output_dir.mkdir(parents=True, exist_ok=True)

		output_path = output_dir / filename
		with open(output_path, "wb") as f:
			f.write(base64.b64decode(image_base64))

		return str(output_path)


def parse_params(param_args):
	"""解析命令行参数为字典"""
	params = {}
	for arg in param_args:
		if '=' in arg:
			key, value = arg.split('=', 1)
			# 尝试转换为合适的类型
			if value.lower() == 'true':
				value = True
			elif value.lower() == 'false':
				value = False
			elif '.' in value:
				try:
					value = float(value)
				except ValueError:
					pass
			elif value.isdigit():
				value = int(value)
			params[key] = value
	return params


def build_grid_params(params):
	"""从参数字典构建grid、coordinate和marker对象"""
	grid = {}
	coordinate = {}
	markers = []

	# 网格参数
	if 'grid_density_x' in params:
		grid['density_x'] = params['grid_density_x']
	if 'grid_density_y' in params:
		grid['density_y'] = params['grid_density_y']
	if 'grid_opacity' in params:
		grid['opacity'] = params['grid_opacity']
	if 'grid_color' in params:
		grid['color'] = params['grid_color']

	# 数字参数
	if 'number_density' in params:
		coordinate['number_density'] = params['number_density']
	if 'number_decimal' in params:
		coordinate['number_decimal'] = params['number_decimal']
	if 'number_size' in params:
		coordinate['number_size'] = params['number_size']
	if 'number_color' in params:
		coordinate['number_color'] = params['number_color']
	if 'number_opacity' in params:
		coordinate['number_opacity'] = params['number_opacity']

	# 标记点参数：收集 marker_N_x/marker_N_y 索引，向后兼容 marker_x/marker_y
	marker_fields = ['x', 'y', 'ring_radius', 'ring_line_width', 'ring_color', 'dot_radius', 'dot_color']
	marker_indices = set()
	for key in params:
		if key.startswith('marker_') and key.endswith('_x'):
			idx = key[len('marker_'):-len('_x')]
			marker_indices.add(idx)
	# 向后兼容：marker_x → 索引 "1"
	if 'marker_x' in params and 'marker_y' in params and '1' not in marker_indices:
		marker_indices.add('1')

	for idx in sorted(marker_indices, key=lambda i: int(i) if i.isdigit() else 999):
		m = {}
		# 带 idx 前缀的参数
		for f in marker_fields:
			key = f'marker_{idx}_{f}'
			if key in params:
				m[f] = params[key]
		# 向后兼容：marker_x → marker_1_x
		if idx == '1' and 'x' not in m:
			for f in marker_fields:
				key = f'marker_{f}'
				if key in params:
					m[f] = params[key]
		if 'x' in m and 'y' in m:
			markers.append(m)

	return grid if grid else None, coordinate if coordinate else None, markers if markers else None


def main():
	# 用法二：处理已保存的JSON文件
	if len(sys.argv) == 3 and sys.argv[1].endswith('.json'):
		json_path = sys.argv[1]
		api_url = sys.argv[2]

		try:
			with open(json_path, 'r', encoding='utf-8') as f:
				result = json.load(f)
		except Exception as e:
			print(f"读取JSON文件失败: {e}")
			sys.exit(1)

		# 处理结果（JSON文件场景无法获取原始参数，使用默认值）
		output_path = process_result(result, api_url)
		if output_path:
			print(output_path)
			print("Screenshot successful. If result is unsatisfactory, refer to skill.md for parameter tuning.")
		sys.exit(0)

	# 用法一：直接调用API
	if len(sys.argv) < 7:
		print(__doc__)
		sys.exit(1)

	api_url = sys.argv[1]
	token = sys.argv[2]
	window_id = int(sys.argv[3])
	session_id = sys.argv[4]
	ai_app_type = sys.argv[5]
	main_window_id = int(sys.argv[6])
	param_args = sys.argv[7:]

	# 解析参数
	params = parse_params(param_args)
	coordinate_type = str(params.pop('coordinate_type', 'grid'))
	color_mode = str(params.pop('color_mode', 'grayscale'))
	grid, coordinate, markers = build_grid_params(params)

	# 调用 API
	screenshot_url = f"{api_url.rstrip('/')}/api/screenshot"

	headers = {
		"Authorization": f"Bearer {token}",
		"Content-Type": "application/json"
	}

	body = {
		"ai_app_type": ai_app_type,
		"session_id": session_id,
		"window_id": window_id,
		"main_window_id": main_window_id,
		"coordinate_type": coordinate_type,
		"color_mode": color_mode
	}

	# 添加网格和数字参数（如果有）
	if grid:
		body["grid"] = grid
	if coordinate:
		body["coordinate"] = coordinate
	if markers:
		body["marker"] = markers

	try:
		response = requests.post(screenshot_url, headers=headers, json=body, timeout=30)
		response.raise_for_status()
		result = response.json()
	except Exception as e:
		print(f"API 调用失败: {e}")
		sys.exit(1)

	output_path = process_result(result, api_url, session_id, ai_app_type, window_id)
	if output_path:
		print(output_path)
		if markers:
			print("Screenshot successful. Marker indicates the position of your input coordinates on the image. If result is unsatisfactory, refer to skill.md for parameter tuning.")
		else:
			print("Screenshot successful. If result is unsatisfactory, refer to skill.md for parameter tuning.")


if __name__ == "__main__":
	main()
