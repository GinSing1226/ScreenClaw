#!/usr/bin/env python3
"""Adapt ScreenClaw template percent coordinates to a current coordinate space."""
import json
import math
import sys

from _common import parse_key_values, unflatten


THRESHOLDS = {
    "large": {"direct": 6.0, "verify": 20.0},
    "normal": {"direct": 3.0, "verify": 15.0},
    "small": {"direct": 2.0, "verify": 8.0},
    "danger": {"direct": 0.0, "verify": 6.0},
}


def require_number(root, path):
    value = root
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"{path} is required")
        value = value[part]
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{path} must be a number") from None


def main() -> int:
    try:
        params = unflatten(parse_key_values(sys.argv[1:]))
        source_width = require_number(params, "source.width")
        source_height = require_number(params, "source.height")
        source_scale = require_number(params, "source.scale_factor")
        current_width = require_number(params, "current.width")
        current_height = require_number(params, "current.height")
        current_scale = require_number(params, "current.scale_factor")
        point_x = require_number(params, "point.x")
        point_y = require_number(params, "point.y")
        risk = str(params.get("risk", "normal")).lower()
        if risk not in THRESHOLDS:
            raise ValueError(f"risk must be one of: {', '.join(sorted(THRESHOLDS))}")
        if min(source_width, source_height, source_scale, current_width, current_height, current_scale) <= 0:
            raise ValueError("width, height, and scale_factor must be greater than 0")
    except ValueError as exc:
        print(f"Script Error: {exc}")
        return 1

    source_x_px = source_width * point_x / 100.0
    source_y_px = source_height * point_y / 100.0
    logical_x = source_x_px / source_scale
    logical_y = source_y_px / source_scale
    candidate_x_px = logical_x * current_scale
    candidate_y_px = logical_y * current_scale
    candidate_x = candidate_x_px / current_width * 100.0
    candidate_y = candidate_y_px / current_height * 100.0

    shift_x_px = (candidate_x - point_x) / 100.0 * current_width
    shift_y_px = (candidate_y - point_y) / 100.0 * current_height
    distance_px = math.hypot(shift_x_px, shift_y_px)

    thresholds = THRESHOLDS[risk]
    max_axis_shift = max(abs(shift_x_px), abs(shift_y_px))
    out_of_bounds = not (0.0 <= candidate_x <= 100.0 and 0.0 <= candidate_y <= 100.0)
    if out_of_bounds:
        decision = "relocate"
        reason = "candidate is outside 0-100 percent bounds"
    elif max_axis_shift <= thresholds["direct"]:
        decision = "direct"
        reason = "axis shift is within direct threshold"
    elif max_axis_shift <= thresholds["verify"]:
        decision = "verify"
        reason = "axis shift requires marker verification"
    else:
        decision = "relocate"
        reason = "axis shift exceeds verification threshold"

    result = {
        "decision": decision,
        "risk": risk,
        "candidate": {"x": round(candidate_x, 4), "y": round(candidate_y, 4)},
        "template": {"x": point_x, "y": point_y},
        "shift_px": {
            "x": round(shift_x_px, 4),
            "y": round(shift_y_px, 4),
            "distance": round(distance_px, 4),
            "max_axis": round(max_axis_shift, 4),
        },
        "thresholds_px": thresholds,
        "source": {"width": source_width, "height": source_height, "scale_factor": source_scale},
        "current": {"width": current_width, "height": current_height, "scale_factor": current_scale},
        "reason": reason,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
