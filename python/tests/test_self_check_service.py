"""
Screenshot self-check service tests.
"""
from app.models.config import SelfCheckConfig
from app.services.self_check_service import SelfCheckService


def test_counter_requires_self_check_after_interval():
    service = SelfCheckService()
    config = SelfCheckConfig(enabled=True, interval=2, min_chars=10, keywords=[])

    first = service.record_screenshot_success("s1", config)
    second = service.record_screenshot_success("s1", config)

    assert first.next_required is False
    assert second.next_required is True
    result = service.validate_before_screenshot("s1", None, config)
    assert result.ok is False
    assert result.response.error_code == "SELF_CHECK_REQUIRED"
    assert "prevent context decay" in result.response.message
    assert "execute the self-check procedure" in result.response.message
    assert "frustrate the user" in result.response.message


def test_self_check_not_allowed_before_required():
    service = SelfCheckService()
    config = SelfCheckConfig(enabled=True, interval=2, min_chars=10, keywords=[])

    result = service.validate_before_screenshot(
        "s1",
        "I am sending self check too early.",
        config,
    )

    assert result.ok is False
    assert result.response.error_code == "SELF_CHECK_NOT_ALLOWED"


def test_self_check_not_allowed_when_disabled():
    service = SelfCheckService()
    config = SelfCheckConfig(enabled=False, interval=2, min_chars=10, keywords=[])

    result = service.validate_before_screenshot(
        "s1",
        "I am sending self check while disabled.",
        config,
    )

    assert result.ok is False
    assert result.response.error_code == "SELF_CHECK_NOT_ALLOWED"


def test_self_check_accepts_keyword_group_and_rejects_duplicate():
    service = SelfCheckService()
    config = SelfCheckConfig(
        enabled=True,
        interval=1,
        min_chars=10,
        keywords=[["grid", "coordinate"], ["crop"]],
    )

    service.record_screenshot_success("s1", config)
    accepted = service.validate_before_screenshot(
        "s1",
        "I re-read the grid coordinate checklist and will use visible grid intersections.",
        config,
    )
    assert accepted.ok is True
    assert accepted.accepted is True

    service.record_screenshot_success("s1", config)
    duplicate = service.validate_before_screenshot(
        "s1",
        "I re-read the grid coordinate checklist and will use visible grid intersections.",
        config,
    )
    assert duplicate.ok is False


def test_self_check_keyword_groups_are_or_and():
    service = SelfCheckService()
    config = SelfCheckConfig(
        enabled=True,
        interval=1,
        min_chars=8,
        keywords=[["grid", "coordinate"], ["crop", "zoom"]],
    )

    service.record_screenshot_success("s1", config)
    missing = service.validate_before_screenshot("s1", "grid only has one keyword", config)
    assert missing.ok is False

    accepted = service.validate_before_screenshot("s1", "crop zoom checklist is loaded", config)
    assert accepted.ok is True
