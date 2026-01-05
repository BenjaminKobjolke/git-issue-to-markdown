"""Settings module for loading configuration."""

import json
from dataclasses import dataclass
from pathlib import Path

from .constants import Constants


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from config file."""

    gitea_url: str
    token: str
    verify_ssl: bool = False

    @classmethod
    def load(cls, config_path: Path | None = None) -> "Settings":
        """Load settings from config file.

        Args:
            config_path: Path to config file. If None, uses default location.

        Returns:
            Settings instance with loaded configuration.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            ValueError: If config file is invalid.
        """
        if config_path is None:
            # Default to config.json in the project root
            config_path = Path(__file__).parent.parent.parent.parent / Constants.CONFIG_FILE

        if not config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {config_path}\n"
                f"Please create a config.json file with gitea_url and token."
            )

        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)

        required_fields = ["gitea_url", "token"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field in config: {field}")

        return cls(
            gitea_url=data["gitea_url"],
            token=data["token"],
            verify_ssl=data.get("verify_ssl", False),
        )
