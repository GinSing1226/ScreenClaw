"""
Screenshot adaptive parameter tests.
"""
from app.models.config import AppConfig
from app.models.request import GridParams, ScreenshotRequest
from app.services.screenshot_params_service import screenshot_params_service


def test_adaptive_grid_defaults_target_about_50px_cells():
    config = AppConfig()
    request = ScreenshotRequest(ai_app_type="test", session_id="s1", window_id=1)

    result = screenshot_params_service.build_from_request(
        request,
        config,
        image_size=(1920, 1080),
    )

    assert result.grid["density_x"] == 2.6
    assert result.grid["density_y"] == 4.6
    assert result.coordinate["number_size"] == 18
    assert result.coordinate["number_density"] == 2
    assert "grid.density_x auto=2.6" in result.adaptive_adjustments


def test_explicit_grid_density_is_preserved():
    config = AppConfig()
    request = ScreenshotRequest(
        ai_app_type="test",
        session_id="s1",
        window_id=1,
        grid=GridParams(density_x=5),
    )

    result = screenshot_params_service.build_from_request(
        request,
        config,
        image_size=(1920, 1080),
    )

    assert result.grid["density_x"] == 5
    assert result.grid["density_y"] == 4.6


def test_number_density_is_forced_when_labels_would_overlap():
    config = AppConfig()
    result = screenshot_params_service.build_from_dict(
        {
            "grid": {"density_x": 20, "density_y": 20},
            "coordinate": {"number_density": 1, "number_size": 18},
        },
        config,
        image_size=(300, 200),
    )

    assert result.coordinate["number_density"] > 1
    assert any("coordinate.number_density adjusted" in item for item in result.adaptive_adjustments)
