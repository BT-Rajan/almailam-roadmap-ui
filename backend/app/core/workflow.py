"""One shared implementation of the transition-checking logic every
status-bearing module would otherwise hand-roll itself:

    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise ConflictError(f"Cannot move X from '{current_status}' to '{new_status}'.")

This does NOT force a single universal status enum across modules --
each module's ALLOWED_TRANSITIONS table (see status_transitions.py)
still encodes its own genuinely different states. What's shared is the
mechanism for checking a transition against whichever table a module
defines, not the states themselves.
"""

from app.core.exceptions import ConflictError, ValidationAppError


def assert_transition_allowed(
    allowed_transitions: dict[str, set[str]],
    current_status: str,
    new_status: str,
    entity_label: str,
) -> None:
    if current_status == new_status:
        return
    allowed = allowed_transitions.get(current_status, set())
    if new_status not in allowed:
        raise ConflictError(
            f"Cannot move {entity_label} from '{current_status}' to '{new_status}'."
        )


def assert_reason_given(reason: str | None, message: str) -> None:
    if not (reason and reason.strip()):
        raise ValidationAppError(message)
