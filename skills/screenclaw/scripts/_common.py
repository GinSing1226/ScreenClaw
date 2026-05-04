#!/usr/bin/env python3
"""ScreenClaw unified script common helpers."""
import base64
import json
import random
import string
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


STRING_KEYS = {"text", "key", "keyword", "action", "newline_key", "api_url", "token", "ai_app_type", "session_id", "source_image_path", "self_check"}

COMMON_KEYS = {"ai_app_type", "session_id", "window_id", "main_window_id"}
ACTION_KEYS = {"x", "y", "action_method"}
ENDPOINT_PARAM_SCHEMAS: Dict[str, Any] = {
    "health": set(),
    "get_window_list": {"keyword", "include_children", "children_filter"},
    "delegated": {"action"},
    "screenshot": {
        "coordinate_type": None,
        "color_mode": None,
        "grid": {"density_x", "density_y", "opacity", "color"},
        "coordinate": {
            "number_density",
            "number_decimal",
            "number_size",
            "number_color",
            "number_opacity",
            "number_stroke_width",
            "number_stroke_color",
        },
        "marker": {
            "x",
            "y",
            "ring_radius",
            "ring_line_width",
            "ring_color",
            "dot_radius",
            "dot_color",
        },
        "self_check": None,
    },
    "crop_zoom_screenshot": {
        "source_image_path",
        "source_image_base64",
        "center_x",
        "center_y",
        "crop_width",
        "crop_height",
        "zoom_scale",
    },
    "scroll_screenshot": {
        "action_method",
        "max_scrolls",
        "scroll_percent",
        "scroll_wait",
        "x",
        "y",
        "max_adjust_retries",
        "target_overlap_min",
        "target_overlap_max",
        "stop_threshold",
    },
    "click": ACTION_KEYS,
    "right_click": ACTION_KEYS,
    "long_press": ACTION_KEYS | {"duration_ms"},
    "hover": ACTION_KEYS | {"duration_ms"},
    "swipe": {"start_x", "start_y", "end_x", "end_y", "action_method"},
    "drag": {"start_x", "start_y", "end_x", "end_y", "duration_ms", "action_method", "target_window_id", "target_main_window_id"},
    "scroll": {"x", "y", "delta", "action_method"},
    "mouse_move": {"delta_x", "delta_y", "duration_ms", "action_method"},
    "input_text": {"x", "y", "text", "newline_key", "action_method"},
    "press_key": {"key", "x", "y", "duration_ms", "action_method"},
    "wait": {"duration_ms", "random_range"},
    "batch": {"instructions": {"action", "params"}, "step": None},
}
VALID_ENDPOINTS = set(ENDPOINT_PARAM_SCHEMAS)
IMAGE_FIELD_KEYS = {"image_base64", "source_image_base64"}


def parse_value(key: str, value: str) -> Any:
    if len(value) >= 2 and value[0] in ("'", '"') and value[-1] == value[0]:
        value = value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if key not in STRING_KEYS:
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
    if value.startswith("[") or value.startswith("{"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    return value


def parse_key_values(args: list[str]) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    for arg in args:
        if "=" not in arg:
            raise ValueError(f"invalid argument '{arg}', expected key=value")
        key, value = arg.split("=", 1)
        params[key] = parse_value(key, value)
    return params


def unflatten(params: Dict[str, Any]) -> Dict[str, Any]:
    def set_nested(obj, parts, value):
        if len(parts) == 1:
            if isinstance(obj, list):
                idx = int(parts[0])
                while len(obj) <= idx:
                    obj.append(None)
                obj[idx] = value
            else:
                obj[parts[0]] = value
            return
        key = parts[0]
        rest = parts[1:]
        if isinstance(obj, list):
            idx = int(key)
            while len(obj) <= idx:
                obj.append(None)
            if obj[idx] is None:
                obj[idx] = [] if rest[0].isdigit() else {}
            set_nested(obj[idx], rest, value)
        else:
            if key not in obj:
                obj[key] = [] if rest[0].isdigit() else {}
            set_nested(obj[key], rest, value)

    result: Dict[str, Any] = {}
    for key, value in params.items():
        if "." in key:
            set_nested(result, key.split("."), value)
        else:
            result[key] = value
    return result


def extract_connection(params: Dict[str, Any]) -> tuple[str, str, Dict[str, Any]]:
    api_url = params.pop("api_url", None)
    token = params.pop("token", None)
    if not api_url:
        raise ValueError("api_url is required")
    if not token:
        raise ValueError("token is required")
    return str(api_url).rstrip("/"), str(token), params


def find_screenclaw_root(start: Optional[Path] = None) -> Path:
    """Find the ScreenClaw workspace root for client-side image files."""
    env_root = os_environ("SCREENCLAW_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    candidates = []
    if start:
        candidates.append(start.resolve())
    candidates.append(Path.cwd().resolve())
    candidates.append(Path(__file__).resolve())

    for candidate in candidates:
        current = candidate if candidate.is_dir() else candidate.parent
        for parent in (current, *current.parents):
            if (parent / "skills" / "screenclaw").exists() or (parent / "python" / "app").exists():
                return parent
    return Path.cwd().resolve()


def os_environ(key: str) -> Optional[str]:
    import os
    return os.environ.get(key)


def data_root() -> Path:
    env_data = os_environ("SCREENCLAW_DATA_DIR")
    if env_data:
        return Path(env_data).expanduser().resolve()
    return find_screenclaw_root() / "data"


def image_prefix_for_endpoint(endpoint: str) -> str:
    if endpoint == "crop_zoom_screenshot":
        return "crop_zoom"
    if endpoint == "scroll_screenshot":
        return "scroll_screenshot"
    return "screenshot"


def path_to_base64(path: str) -> str:
    source = Path(path).expanduser()
    if not source.exists():
        raise ValueError(f"source_image_path not found: {path}")
    return base64.b64encode(source.read_bytes()).decode("ascii")


def prepare_remote_crop_input(endpoint: str, api_url: str, body: Dict[str, Any]) -> None:
    """For remote servers, send local images as base64 instead of inaccessible client paths."""
    if is_local_url(api_url):
        return
    if endpoint == "crop_zoom_screenshot" and body.get("source_image_path") and not body.get("source_image_base64"):
        body["source_image_base64"] = path_to_base64(str(body.pop("source_image_path")))
    if endpoint == "batch":
        for instruction in body.get("instructions", []):
            if instruction.get("action") != "crop_zoom_screenshot":
                continue
            params = instruction.get("params") or {}
            if params.get("source_image_path") and not params.get("source_image_base64"):
                params["source_image_base64"] = path_to_base64(str(params.pop("source_image_path")))


def normalize_batch_steps(params: Dict[str, Any]) -> Dict[str, Any]:
    steps = params.pop("step", None)
    if steps is None:
        return params
    if not isinstance(steps, list):
        raise ValueError("step must use numeric indexes, e.g. step.0.action=click")
    instructions = []
    for step in steps:
        if not step:
            continue
        action = step.get("action")
        if not action:
            raise ValueError("each batch step requires action")
        instructions.append({"action": action, "params": step.get("params", {})})
    params["instructions"] = instructions
    return params


def endpoint_doc_path(endpoint: str) -> str:
    return f"references/api/{endpoint}.md"


def format_valid_endpoints() -> str:
    return ", ".join(sorted(VALID_ENDPOINTS))


def validate_endpoint(endpoint: str) -> None:
    if endpoint not in VALID_ENDPOINTS:
        raise ValueError(
            f"unknown endpoint '{endpoint}'. Next: read skill.md and use a valid endpoint. "
            f"Valid endpoints: {format_valid_endpoints()}"
        )


def validate_request_params(endpoint: str, body: Dict[str, Any]) -> None:
    validate_endpoint(endpoint)
    schema = ENDPOINT_PARAM_SCHEMAS[endpoint]
    allowed = COMMON_KEYS | set(schema)
    _validate_mapping(endpoint, body, schema, allowed, endpoint)

    if endpoint == "batch":
        instructions = body.get("instructions") or []
        if not isinstance(instructions, list):
            raise ValueError("invalid parameter 'instructions': expected a list. Next: read references/api/batch.md.")
        for index, instruction in enumerate(instructions):
            if not isinstance(instruction, dict):
                raise ValueError(f"invalid parameter 'instructions.{index}': expected an object. Next: read references/api/batch.md.")
            action = instruction.get("action")
            if action not in VALID_ENDPOINTS or action in {"health", "batch"}:
                raise ValueError(
                    f"unknown batch action '{action}'. Next: read skill.md and references/api/batch.md. "
                    f"Valid actions: {format_valid_endpoints()}"
                )
            params = instruction.get("params") or {}
            if not isinstance(params, dict):
                raise ValueError(f"invalid parameter 'instructions.{index}.params': expected an object. Next: read references/api/batch.md.")
            step_schema = ENDPOINT_PARAM_SCHEMAS[action]
            _validate_mapping(action, params, step_schema, set(step_schema), f"step.{index}.params")


def _validate_mapping(endpoint: str, value: Dict[str, Any], schema: Any, allowed: set[str], path: str) -> None:
    for key, item in value.items():
        if key not in allowed:
            raise ValueError(
                f"unknown parameter '{path}.{key}' for endpoint '{endpoint}'. "
                f"Next: read skill.md and {endpoint_doc_path(endpoint)}."
            )
        nested_schema = schema.get(key) if isinstance(schema, dict) else None
        if isinstance(nested_schema, (dict, set)):
            _validate_nested(endpoint, item, nested_schema, f"{path}.{key}")


def _validate_nested(endpoint: str, item: Any, schema: Dict[str, Any], path: str) -> None:
    if isinstance(item, list):
        for index, child in enumerate(item):
            _validate_nested(endpoint, child, schema, f"{path}.{index}")
        return
    if not isinstance(item, dict):
        return
    for key, child in item.items():
        if key not in schema:
            raise ValueError(
                f"unknown parameter '{path}.{key}' for endpoint '{endpoint}'. "
                f"Next: read skill.md and {endpoint_doc_path(endpoint)}."
            )
        nested_schema = schema.get(key) if isinstance(schema, dict) else None
        if isinstance(nested_schema, (dict, set)):
            _validate_nested(endpoint, child, nested_schema, f"{path}.{key}")


def is_local_url(api_url: str) -> bool:
    lowered = api_url.lower()
    return "localhost" in lowered or "127.0.0.1" in lowered or "::1" in lowered


def save_remote_image(image_base64: str, ai_app_type: str, session_id: str, prefix: str = "screenshot") -> str:
    base_dir = data_root()
    session_prefix = f"{ai_app_type}__{session_id}__"
    existing_dirs = sorted(
        path for path in Path(base_dir).glob(f"{session_prefix}*")
        if path.is_dir()
    )
    if existing_dirs:
        out_dir = existing_dirs[0]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        out_dir = Path(base_dir) / f"{session_prefix}{date_str}"
    out_dir.mkdir(parents=True, exist_ok=True)
    time_str = datetime.now().strftime("%H%M%S")
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    out_path = out_dir / f"{prefix}_{time_str}_{rand}.png"
    out_path.write_bytes(base64.b64decode(image_base64))
    return str(out_path)


def materialize_image_data(endpoint: str, data: Dict[str, Any], ai_app_type: str, session_id: str) -> Optional[str]:
    path = data.get("image_path")
    if not path and data.get("image_base64"):
        path = save_remote_image(
            data["image_base64"],
            ai_app_type,
            session_id,
            prefix=image_prefix_for_endpoint(endpoint),
        )
        data["image_path"] = path
        data.pop("image_base64", None)
    return path


def process_batch_images(body: Dict[str, Any], result: Dict[str, Any]) -> list[str]:
    paths: list[str] = []
    results = ((result.get("data") or {}).get("results") or [])
    instructions = body.get("instructions") or []
    for index, item in enumerate(results):
        data = item.get("data") or {}
        action = instructions[index].get("action") if index < len(instructions) else "screenshot"
        if data.get("image_path") or data.get("image_base64"):
            path = materialize_image_data(
                action,
                data,
                body.get("ai_app_type", "unknown"),
                body.get("session_id", "unknown"),
            )
            if path:
                paths.append(path)
    return paths


def sanitize_output_data(value: Any) -> Any:
    if isinstance(value, dict):
        clean = {}
        for key, item in value.items():
            if key in IMAGE_FIELD_KEYS:
                continue
            sanitized = sanitize_output_data(item)
            if sanitized is None or sanitized == {} or sanitized == []:
                continue
            clean[key] = sanitized
        return clean
    if isinstance(value, list):
        return [
            item
            for item in (sanitize_output_data(item) for item in value)
            if item is not None and item != {} and item != []
        ]
    return value


def print_api_result(endpoint: str, api_url: str, body: Dict[str, Any], result: Dict[str, Any]) -> int:
    if not result.get("success"):
        code = result.get("error_code") or "UNKNOWN"
        print(f"API Error [{code}]: {result.get('message', 'Unknown error')}")
        return 1

    data = result.get("data") or {}
    if endpoint in {"screenshot", "scroll_screenshot", "crop_zoom_screenshot"}:
        path = materialize_image_data(
            endpoint,
            data,
            body.get("ai_app_type", "unknown"),
            body.get("session_id", "unknown"),
        )
        if path:
            print(path)

    if endpoint in {"screenshot", "scroll_screenshot", "crop_zoom_screenshot"}:
        message = result.get("message")
        if message:
            print(message)
        if data:
            print("Data:")
            print(json.dumps(sanitize_output_data(data), ensure_ascii=False, indent=2))
    elif endpoint == "batch":
        for path in process_batch_images(body, result):
            print(path)
        print(json.dumps(sanitize_output_data(result), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(sanitize_output_data(result), ensure_ascii=False, indent=2))
    return 0
