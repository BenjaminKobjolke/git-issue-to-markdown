"""Tests for gitea_client module."""

import pytest

from git_issue_to_markdown.gitea_client import parse_repo_url


class TestParseRepoUrl:
    """Tests for parse_repo_url function."""

    def test_parses_standard_url(self) -> None:
        """Should parse standard repository URL."""
        url = "https://xida.me:3030/Intern/turbo-habits-app"
        owner, repo = parse_repo_url(url)
        assert owner == "Intern"
        assert repo == "turbo-habits-app"

    def test_parses_url_with_git_suffix(self) -> None:
        """Should parse URL with .git suffix."""
        url = "https://xida.me:3030/Intern/turbo-habits-app.git"
        owner, repo = parse_repo_url(url)
        assert owner == "Intern"
        assert repo == "turbo-habits-app"

    def test_parses_url_with_trailing_slash(self) -> None:
        """Should parse URL with trailing slash."""
        url = "https://gitea.example.com/org/repo/"
        owner, repo = parse_repo_url(url)
        assert owner == "org"
        assert repo == "repo"

    def test_raises_for_invalid_url(self) -> None:
        """Should raise ValueError for invalid URL."""
        with pytest.raises(ValueError, match="Invalid repository URL"):
            parse_repo_url("https://gitea.example.com/only-one-part")

    def test_parses_url_without_port(self) -> None:
        """Should parse URL without port."""
        url = "https://gitea.example.com/user/project"
        owner, repo = parse_repo_url(url)
        assert owner == "user"
        assert repo == "project"
