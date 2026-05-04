"""
截图轮数自检服务
"""
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from app.models.response import create_error_response, BaseResponse


@dataclass
class SelfCheckState:
    screenshot_count: int = 0
    self_check_required: bool = False
    last_self_check_normalized: Optional[str] = None


@dataclass
class SelfCheckValidationResult:
    ok: bool
    accepted: bool = False
    response: Optional[BaseResponse] = None


@dataclass
class SelfCheckNotice:
    accepted: bool = False
    next_required: bool = False


class SelfCheckService:
    """按 session 维护截图自检状态"""

    def __init__(self):
        self._states: Dict[str, SelfCheckState] = {}

    def reset_all(self):
        self._states.clear()

    def validate_before_screenshot(self, session_id: str, self_check: Optional[str], config) -> SelfCheckValidationResult:
        if not config.enabled:
            if self_check is not None:
                return SelfCheckValidationResult(
                    ok=False,
                    response=create_error_response(
                        "SELF_CHECK_NOT_ALLOWED",
                        "Self-check is not expected now. Next: retry without self_check. See references/api/screenshot.md."
                    )
                )
            return SelfCheckValidationResult(ok=True)

        state = self._states.setdefault(session_id, SelfCheckState())
        if not state.self_check_required:
            if self_check is not None:
                return SelfCheckValidationResult(
                    ok=False,
                    response=create_error_response(
                        "SELF_CHECK_NOT_ALLOWED",
                        "Self-check is not expected now. Next: retry without self_check. See references/api/screenshot.md."
                    )
                )
            return SelfCheckValidationResult(ok=True)

        failed = self._validate_self_check(self_check, state, config)
        if failed:
            message = self._build_error_message(config, failed, required=not self_check)
            return SelfCheckValidationResult(
                ok=False,
                response=create_error_response("SELF_CHECK_REQUIRED", message)
            )

        state.self_check_required = False
        state.screenshot_count = 0
        state.last_self_check_normalized = self._normalize(self_check or "")
        return SelfCheckValidationResult(ok=True, accepted=True)

    def record_screenshot_success(self, session_id: str, config, units: int = 1) -> SelfCheckNotice:
        if not config.enabled or units <= 0:
            return SelfCheckNotice()

        state = self._states.setdefault(session_id, SelfCheckState())
        state.screenshot_count += units
        if state.screenshot_count >= config.interval:
            state.self_check_required = True
            return SelfCheckNotice(next_required=True)
        return SelfCheckNotice()

    def _validate_self_check(self, self_check: Optional[str], state: SelfCheckState, config) -> List[str]:
        failed: List[str] = []
        if not isinstance(self_check, str) or not self_check.strip():
            return ["missing self_check"]

        normalized = self._normalize(self_check)
        if len(normalized) < config.min_chars:
            failed.append("self_check is too short")

        if state.last_self_check_normalized and normalized == state.last_self_check_normalized:
            failed.append("self_check is identical to previous self_check")

        if not self._matches_keywords(self_check, config.keywords):
            failed.append("self_check missing required keyword group")

        return failed

    def _matches_keywords(self, text: str, keyword_groups: List[List[str]]) -> bool:
        if not keyword_groups:
            return True
        lowered = text.lower()
        for group in keyword_groups:
            if all(keyword.lower() in lowered for keyword in group):
                return True
        return False

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", "", text).lower()

    def _format_keyword_groups(self, keyword_groups: List[List[str]]) -> str:
        return " OR ".join(
            "[" + " AND ".join(group) + "]"
            for group in keyword_groups
        )

    def _build_error_message(self, config, failed_reasons: List[str], required: bool = False) -> str:
        prefix = "Self-check required." if required else "Self-check invalid."
        return (
            f"{prefix} Reason: {'; '.join(failed_reasons)}. "
            f"To keep the task moving and prevent context decay, you must read {config.doc_path}, "
            f"execute the self-check procedure as required by that document, and reload the critical context. "
            f"Do not output self_check text without executing the self-check procedure first. "
            f"Doing so will frustrate the user, allow key information to be lost, and gradually push the task off track until it fails. "
            f"Requirements: execute the self-check procedure; min_chars={config.min_chars} after removing whitespace; "
            f"self_check must not be identical to the previous one; "
            f"keywords must satisfy one group: {self._format_keyword_groups(config.keywords)}."
        )


self_check_service = SelfCheckService()
