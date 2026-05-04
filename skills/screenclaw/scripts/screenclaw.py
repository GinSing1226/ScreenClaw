#!/usr/bin/env python3
"""Unified ScreenClaw API entrypoint."""
import json
import sys

try:
    import requests
except ImportError:
    print("Script Error: missing requests module. Install it with: pip install requests")
    sys.exit(1)

from _common import (
    extract_connection,
    normalize_batch_steps,
    parse_key_values,
    prepare_remote_crop_input,
    print_api_result,
    unflatten,
    validate_endpoint,
    validate_request_params,
)


GET_ENDPOINTS = {"health"}
WINDOW_EXEMPT = {"health", "get_window_list", "delegated", "crop_zoom_screenshot"}


def build_body(endpoint: str, params):
    body = unflatten(params)
    if endpoint == "batch":
        body = normalize_batch_steps(body)

    validate_request_params(endpoint, body)

    if endpoint != "health":
        required = ["ai_app_type", "session_id"]
        for key in required:
            if key not in body:
                raise ValueError(f"{key} is required")

    if endpoint not in WINDOW_EXEMPT and "window_id" not in body:
        raise ValueError("window_id is required")
    if endpoint not in WINDOW_EXEMPT and endpoint != "wait" and "main_window_id" not in body:
        raise ValueError("main_window_id is required")
    return body


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python screenclaw.py <endpoint> api_url=<url> token=<token> ai_app_type=<type> session_id=<id> [params...]")
        return 1

    endpoint = sys.argv[1]
    try:
        validate_endpoint(endpoint)
        raw_params = parse_key_values(sys.argv[2:])
        api_url, token, raw_params = extract_connection(raw_params)
        body = build_body(endpoint, raw_params)
        prepare_remote_crop_input(endpoint, api_url, body)
    except ValueError as exc:
        print(f"Script Error: {exc}")
        return 1

    url = f"{api_url}/api/{endpoint}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        if endpoint in GET_ENDPOINTS:
            response = requests.get(url, headers=headers, timeout=30)
        else:
            timeout = 240 if endpoint in {"scroll_screenshot", "batch"} else 30
            response = requests.post(url, headers=headers, json=body, timeout=timeout)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException:
        print("Script Error: API call failed. Check api_url, token, endpoint, and network. Next: read skill.md, then verify the endpoint API document.")
        return 1
    except json.JSONDecodeError as exc:
        print(f"Script Error: failed to parse API response: {exc}")
        return 1

    return print_api_result(endpoint, api_url, body, result)


if __name__ == "__main__":
    sys.exit(main())
