#!/usr/bin/env python3
"""Summarize ScreenClaw recording window groups from step.json."""
import json
import sys
from pathlib import Path

from _common import parse_key_values


SYSTEM_TITLES = {"打开", "另存为", "选择文件", "打开(&O)"}


def load_args(argv):
    params = parse_key_values(argv)
    path = params.get("path") or params.get("record") or params.get("step_json")
    if not path:
        raise ValueError("path=<record_dir_or_step.json> is required")
    fmt = str(params.get("format", "markdown")).lower()
    if fmt not in {"markdown", "json"}:
        raise ValueError("format must be markdown or json")
    return Path(path), fmt


def step_json_path(path: Path) -> Path:
    if path.is_dir():
        return path / "step.json"
    return path


def window_info_for(step):
    params = step.get("params") or {}
    return step.get("window_info") or params.get("window_info") or {}


def classify(step):
    action = step.get("action") or ""
    process = step.get("process")
    if process is None or action.startswith("desktop_"):
        return "桌面级"
    window_id = process.get("window_id")
    main_window_id = process.get("main_window_id")
    title = process.get("window_title") or ""
    main_title = process.get("main_window_title") or ""
    if window_id != main_window_id:
        if main_title in SYSTEM_TITLES or title in SYSTEM_TITLES:
            return "系统弹窗子窗口"
        return "子窗口"
    if title in SYSTEM_TITLES or main_title in SYSTEM_TITLES:
        return "系统弹窗主窗口"
    return "主窗口"


def base_group_key(step, kind):
    action = step.get("action") or ""
    process = step.get("process")
    if kind == "桌面级":
        monitor = (step.get("params") or {}).get("monitor_index", "unknown")
        return f"desktop_monitor_{monitor}"
    title = (process or {}).get("window_title") or ""
    main_title = (process or {}).get("main_window_title") or ""
    process_name = (process or {}).get("process_name") or "unknown"
    if "系统弹窗" in kind:
        stem = title or main_title or "dialog"
        return f"dialog_{slug(stem)}"
    if kind == "子窗口":
        stem = title or "child"
        return f"{slug(process_name)}_{slug(stem)}_child"
    return f"{slug(process_name)}_main"


def slug(text):
    out = []
    for ch in str(text).lower():
        if ch.isascii() and ch.isalnum():
            out.append(ch)
        elif ch in {" ", "-", "_"}:
            out.append("_")
    result = "".join(out).strip("_")
    while "__" in result:
        result = result.replace("__", "_")
    return result or "window"


def make_var_names(group):
    key = group["group_key"]
    if group["type"] == "桌面级":
        return [f"{{{key}_monitor_index}}"]
    return [f"{{{key}_window_id}}", f"{{{key}_main_window_id}}"]


def summarize(data):
    groups = {}
    for step in data.get("steps", []):
        kind = classify(step)
        key = base_group_key(step, kind)
        process = step.get("process") or {}
        wi = window_info_for(step)
        if key not in groups:
            groups[key] = {
                "group_key": key,
                "type": kind,
                "process_name": process.get("process_name"),
                "window_title": process.get("window_title"),
                "main_window_title": process.get("main_window_title"),
                "window_id": process.get("window_id"),
                "main_window_id": process.get("main_window_id"),
                "window_info": wi,
                "steps": [],
                "actions": [],
                "warnings": [],
            }
        group = groups[key]
        group["steps"].append(step.get("step_index"))
        action = step.get("action")
        if action and action not in group["actions"]:
            group["actions"].append(action)
        if wi and wi != group.get("window_info"):
            group["warnings"].append("window_info differs within group; recheck before fixed-coordinate reuse")
        if kind == "子窗口" and (process.get("window_title") == "Chrome Legacy Window"):
            group["warnings"].append("Chrome Legacy Window is a content child window; do not write it as main window")
        if (process.get("process_name") or "").lower().startswith("screenclaw"):
            group["warnings"].append("ScreenClaw self window; usually exclude from scenario template")
    for group in groups.values():
        group["variables"] = make_var_names(group)
        group["steps"] = [s for s in group["steps"] if s is not None]
        group["warnings"] = sorted(set(group["warnings"]))
    return list(groups.values())


def fmt_window_info(wi):
    if not wi:
        return ""
    return ", ".join(f"{k}={wi.get(k)}" for k in ("source_width", "source_height", "scale_factor") if k in wi)


def print_markdown(groups):
    print("| group_key | 类型 | process_name | window_title | main_window_title | 录制步骤 | window_info | 变量名建议 | warnings |")
    print("|-----------|------|--------------|--------------|-------------------|----------|-------------|------------|----------|")
    for g in groups:
        row = [
            g["group_key"],
            g["type"],
            g.get("process_name") or "",
            g.get("window_title") or "",
            g.get("main_window_title") or "",
            ",".join(str(s) for s in g["steps"]),
            fmt_window_info(g.get("window_info") or {}),
            "<br>".join(g.get("variables") or []),
            "<br>".join(g.get("warnings") or []),
        ]
        print("| " + " | ".join(str(v).replace("|", "\\|") for v in row) + " |")


def main() -> int:
    try:
        path, fmt = load_args(sys.argv[1:])
        sj = step_json_path(path)
        data = json.loads(sj.read_text(encoding="utf-8"))
        groups = summarize(data)
    except Exception as exc:
        print(f"Script Error: {exc}")
        return 1
    if fmt == "json":
        print(json.dumps({"groups": groups}, ensure_ascii=False, indent=2))
    else:
        print_markdown(groups)
    return 0


if __name__ == "__main__":
    sys.exit(main())
