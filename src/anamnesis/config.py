"""Anamnesis configuration."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class KnowledgeConfig:
    """Per-application configuration for the Anamnesis knowledge framework.

    Only circle1_path and circle2_root are required. All other fields
    have sensible defaults for local single-user operation.
    """

    # Required — Circle 1 (injection file) and Circle 2 (bolus storage root)
    circle1_path: Path
    circle2_root: Path

    # Token budget for Circle 1 injection
    circle1_max_tokens: int = 4000

    # Storage backend discriminator (kept as string for serialization)
    bolus_store: Literal["markdown"] = "markdown"

    # Circle 4 (episode capture)
    circle4_root: Path | None = None
    circle4_retention_days: int | None = None

    # Recency pipeline
    recency_budget: int = 0

    # Completion provider (for compilation pipeline)
    completion_provider_type: str | None = None   # "openai_compatible" | None
    completion_provider_base_url: str | None = None
    completion_provider_model: str | None = None
    completion_provider_api_key: str | None = None

    # API server settings
    api_host: str = "127.0.0.1"
    api_port: int = 8741
    api_key: str | None = None

    def __post_init__(self) -> None:
        # Coerce strings to Path for convenience
        if isinstance(self.circle1_path, str):
            self.circle1_path = Path(self.circle1_path)
        if isinstance(self.circle2_root, str):
            self.circle2_root = Path(self.circle2_root)
        if isinstance(self.circle4_root, str):
            self.circle4_root = Path(self.circle4_root)

        if self.circle1_max_tokens < 500:
            raise ValueError(
                f"circle1_max_tokens must be >= 500, got {self.circle1_max_tokens}"
            )

        valid_stores = {"markdown"}
        if self.bolus_store not in valid_stores:
            raise ValueError(
                f"bolus_store must be one of {valid_stores}, got {self.bolus_store!r}"
            )
