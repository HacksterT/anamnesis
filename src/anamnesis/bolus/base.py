"""Abstract base class for bolus storage backends."""

from abc import ABC, abstractmethod


class BolusStore(ABC):
    """Pluggable storage interface for Circle 2 knowledge boluses.

    Implementations handle persistence (markdown files, SQLite, etc.).
    The framework interacts with boluses exclusively through this interface.
    """

    @abstractmethod
    def read(self, bolus_id: str) -> str:
        """Return the content of a bolus by ID.

        Raises KeyError if the bolus does not exist.
        """
        ...

    @abstractmethod
    def write(self, bolus_id: str, content: str, metadata: dict) -> None:
        """Create or overwrite a bolus with the given content and metadata."""
        ...

    @abstractmethod
    def delete(self, bolus_id: str) -> bool:
        """Delete a bolus. Returns True if it existed, False otherwise."""
        ...

    @abstractmethod
    def list(self, active_only: bool = True) -> list[dict]:
        """Return metadata dicts for all boluses.

        If active_only is True, only return boluses with active=True.
        """
        ...

    @abstractmethod
    def exists(self, bolus_id: str) -> bool:
        """Return True if a bolus with this ID exists."""
        ...

    @abstractmethod
    def get_metadata(self, bolus_id: str) -> dict:
        """Return the metadata dict for a bolus.

        Raises KeyError if the bolus does not exist.
        """
        ...

    @abstractmethod
    def set_active(self, bolus_id: str, active: bool) -> None:
        """Toggle the active state of a bolus.

        Raises KeyError if the bolus does not exist.
        """
        ...
