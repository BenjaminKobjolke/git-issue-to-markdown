"""String constants for the application."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Constants:
    """Application constants."""

    CONFIG_FILE: str = "config.json"
    ISSUE_MARKER_PATTERN: str = r"<!-- GITEA_ISSUE:(\d+) -->"
    ISSUE_MARKER_TEMPLATE: str = "<!-- GITEA_ISSUE:{issue_id} -->"
