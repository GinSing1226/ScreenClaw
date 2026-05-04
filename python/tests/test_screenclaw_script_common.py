"""
Unified ScreenClaw script compatibility tests.
"""
import base64
import importlib.util
from pathlib import Path


def load_common():
    path = Path(__file__).parents[2] / "skills" / "screenclaw" / "scripts" / "_common.py"
    spec = importlib.util.spec_from_file_location("screenclaw_script_common", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dotted_params_are_converted_to_nested_body():
    common = load_common()
    body = common.unflatten({
        "grid.density_x": 3.3,
        "coordinate.number_size": 15,
        "marker.0.x": 10,
        "marker.0.y": 20,
        "marker.1.x": 30,
        "marker.1.y": 40,
    })

    assert body["grid"]["density_x"] == 3.3
    assert body["coordinate"]["number_size"] == 15
    assert body["marker"][0]["x"] == 10
    assert body["marker"][0]["y"] == 20
    assert body["marker"][1]["x"] == 30
    assert body["marker"][1]["y"] == 40


def test_remote_crop_converts_source_path_to_base64(tmp_path):
    common = load_common()
    source = tmp_path / "source.png"
    source.write_bytes(b"image-bytes")
    body = {"source_image_path": str(source)}

    common.prepare_remote_crop_input("crop_zoom_screenshot", "http://192.168.1.2:12261", body)

    assert "source_image_path" not in body
    assert base64.b64decode(body["source_image_base64"]) == b"image-bytes"


def test_batch_remote_crop_and_nested_images_are_processed(tmp_path, monkeypatch):
    common = load_common()
    monkeypatch.setenv("SCREENCLAW_DATA_DIR", str(tmp_path / "data"))
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    body = {
        "ai_app_type": "test",
        "session_id": "s1",
        "instructions": [
            {"action": "crop_zoom_screenshot", "params": {"source_image_path": str(source)}},
            {"action": "screenshot", "params": {}},
        ],
    }
    result = {
        "success": True,
        "data": {
            "results": [
                {"success": True, "data": {"image_base64": base64.b64encode(b"crop").decode("ascii")}},
                {"success": True, "data": {"image_base64": base64.b64encode(b"shot").decode("ascii")}},
            ]
        },
    }

    common.prepare_remote_crop_input("batch", "http://192.168.1.2:12261", body)
    paths = common.process_batch_images(body, result)

    assert "source_image_base64" in body["instructions"][0]["params"]
    assert len(paths) == 2
    assert Path(paths[0]).name.startswith("crop_zoom_")
    assert Path(paths[1]).name.startswith("screenshot_")
    assert Path(paths[0]).read_bytes() == b"crop"
    assert Path(paths[1]).read_bytes() == b"shot"


def test_remote_image_reuses_existing_session_dir(tmp_path, monkeypatch):
    common = load_common()
    data_dir = tmp_path / "data"
    existing = data_dir / "test__s1__2026-04-26"
    newer = data_dir / "test__s1__2026-04-27"
    existing.mkdir(parents=True)
    newer.mkdir(parents=True)
    monkeypatch.setenv("SCREENCLAW_DATA_DIR", str(data_dir))

    path = common.save_remote_image(
        base64.b64encode(b"image").decode("ascii"),
        "test",
        "s1",
    )

    assert Path(path).parent == existing
    assert Path(path).read_bytes() == b"image"


def test_unknown_endpoint_is_rejected():
    common = load_common()

    try:
        common.validate_endpoint("screen")
    except ValueError as exc:
        assert "unknown endpoint 'screen'" in str(exc)
        assert "read skill.md" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_unknown_parameter_is_rejected():
    common = load_common()
    body = {
        "ai_app_type": "test",
        "session_id": "s1",
        "window_id": 1,
        "main_window_id": 1,
        "coordinate_type": "grid",
        "color": True,
    }

    try:
        common.validate_request_params("screenshot", body)
    except ValueError as exc:
        assert "unknown parameter 'screenshot.color'" in str(exc)
        assert "references/api/screenshot.md" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_unknown_batch_step_parameter_is_rejected():
    common = load_common()
    body = common.normalize_batch_steps(common.unflatten({
        "ai_app_type": "test",
        "session_id": "s1",
        "window_id": 1,
        "main_window_id": 1,
        "step.0.action": "screenshot",
        "step.0.params.grid.foo": 1,
    }))

    try:
        common.validate_request_params("batch", body)
    except ValueError as exc:
        assert "unknown parameter 'step.0.params.grid.foo'" in str(exc)
        assert "references/api/screenshot.md" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_image_result_prints_sanitized_data(capsys):
    common = load_common()
    result = {
        "success": True,
        "message": "Crop zoom successful.",
        "data": {
            "image_path": "D:/tmp/crop.png",
            "image_base64": "large",
            "requested_params": {"center_x": 50, "source_image_base64": "large"},
            "effective_crop": {"zoom_scale": 2},
        },
    }

    rc = common.print_api_result(
        "crop_zoom_screenshot",
        "http://127.0.0.1:12261",
        {"ai_app_type": "test", "session_id": "s1"},
        result,
    )

    output = capsys.readouterr().out
    assert rc == 0
    assert "D:/tmp/crop.png" in output
    assert "Data:" in output
    assert "effective_crop" in output
    assert "image_base64" not in output
    assert "source_image_base64" not in output


def test_sanitize_output_data_removes_null_and_empty_values():
    common = load_common()

    sanitized = common.sanitize_output_data({
        "image_path": "D:/tmp/screenshot.png",
        "grid": None,
        "adaptive_adjustments": [],
        "requested_params": {
            "coordinate_type": "no",
            "grid": None,
            "marker": None,
            "image_quality": 85,
        },
        "effective_grid": None,
    })

    assert sanitized == {
        "image_path": "D:/tmp/screenshot.png",
        "requested_params": {
            "coordinate_type": "no",
            "image_quality": 85,
        },
    }
