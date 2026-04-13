"""Domain exception types for Anamnesis."""

from __future__ import annotations


class BolusNotFoundError(KeyError):
    """Raised when a bolus ID does not exist in the store."""

    def __init__(self, bolus_id: str) -> None:
        self.bolus_id = bolus_id
        super().__init__(bolus_id)

    def __str__(self) -> str:
        return f"Bolus {self.bolus_id!r} not found."


class BolusExistsError(ValueError):
    """Raised when attempting to create a bolus that already exists."""

    def __init__(self, bolus_id: str) -> None:
        self.bolus_id = bolus_id
        super().__init__(f"Bolus {bolus_id!r} already exists.")


class CircleNotConfiguredError(RuntimeError):
    """Raised when an operation requires a circle that is not configured."""

    def __init__(self, circle: int, detail: str = "") -> None:
        self.circle = circle
        msg = f"Circle {circle} is not configured."
        if detail:
            msg += f" {detail}"
        super().__init__(msg)
