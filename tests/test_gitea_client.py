"""Tests for gitea_client module."""

from unittest.mock import MagicMock, Mock

import pytest

from git_issue_to_markdown.gitea_client import (
    add_comment,
    close_issue,
    parse_repo_url,
    reopen_issue,
)


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


class TestAddComment:
    """Tests for add_comment function."""

    def test_add_comment_success(self) -> None:
        """Should return True when comment is added successfully."""
        mock_gitea = MagicMock()
        mock_gitea.url = "https://gitea.example.com"
        mock_response = Mock()
        mock_response.status_code = 201
        mock_gitea.requests.post.return_value = mock_response

        result = add_comment(mock_gitea, "owner", "repo", 123, "Test comment", "test_token")

        assert result is True
        mock_gitea.requests.post.assert_called_once_with(
            "https://gitea.example.com/api/v1/repos/owner/repo/issues/123/comments",
            json={"body": "Test comment"},
            headers={"Authorization": "token test_token"},
        )

    def test_add_comment_failure(self) -> None:
        """Should return False when comment fails to add."""
        mock_gitea = MagicMock()
        mock_gitea.url = "https://gitea.example.com"
        mock_response = Mock()
        mock_response.status_code = 404
        mock_gitea.requests.post.return_value = mock_response

        result = add_comment(mock_gitea, "owner", "repo", 999, "Test comment", "test_token")

        assert result is False

    def test_add_comment_exception(self) -> None:
        """Should return False and handle exception gracefully."""
        mock_gitea = MagicMock()
        mock_gitea.url = "https://gitea.example.com"
        mock_gitea.requests.post.side_effect = Exception("Network error")

        result = add_comment(mock_gitea, "owner", "repo", 123, "Test comment", "test_token")

        assert result is False


class TestCloseIssue:
    """Tests for close_issue function."""

    def test_close_issue_success(self) -> None:
        """Should return True when issue is closed successfully."""
        mock_gitea = MagicMock()
        mock_gitea.url = "https://gitea.example.com"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_gitea.requests.patch.return_value = mock_response

        result = close_issue(mock_gitea, "owner", "repo", 123, "test_token")

        assert result is True
        mock_gitea.requests.patch.assert_called_once_with(
            "https://gitea.example.com/api/v1/repos/owner/repo/issues/123",
            json={"state": "closed"},
            headers={"Authorization": "token test_token"},
        )

    def test_close_issue_failure(self) -> None:
        """Should return False when issue fails to close."""
        mock_gitea = MagicMock()
        mock_gitea.url = "https://gitea.example.com"
        mock_response = Mock()
        mock_response.status_code = 404
        mock_gitea.requests.patch.return_value = mock_response

        result = close_issue(mock_gitea, "owner", "repo", 999, "test_token")

        assert result is False

    def test_close_issue_exception(self) -> None:
        """Should return False and handle exception gracefully."""
        mock_gitea = MagicMock()
        mock_gitea.url = "https://gitea.example.com"
        mock_gitea.requests.patch.side_effect = Exception("Network error")

        result = close_issue(mock_gitea, "owner", "repo", 123, "test_token")

        assert result is False


class TestReopenIssue:
    """Tests for reopen_issue function."""

    def test_reopen_issue_success(self) -> None:
        """Should return True when issue is reopened successfully."""
        mock_gitea = MagicMock()
        mock_gitea.url = "https://gitea.example.com"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_gitea.requests.patch.return_value = mock_response

        result = reopen_issue(mock_gitea, "owner", "repo", 123, "test_token")

        assert result is True
        mock_gitea.requests.patch.assert_called_once_with(
            "https://gitea.example.com/api/v1/repos/owner/repo/issues/123",
            json={"state": "open"},
            headers={"Authorization": "token test_token"},
        )

    def test_reopen_issue_failure(self) -> None:
        """Should return False when issue fails to reopen."""
        mock_gitea = MagicMock()
        mock_gitea.url = "https://gitea.example.com"
        mock_response = Mock()
        mock_response.status_code = 404
        mock_gitea.requests.patch.return_value = mock_response

        result = reopen_issue(mock_gitea, "owner", "repo", 999, "test_token")

        assert result is False

    def test_reopen_issue_exception(self) -> None:
        """Should return False and handle exception gracefully."""
        mock_gitea = MagicMock()
        mock_gitea.url = "https://gitea.example.com"
        mock_gitea.requests.patch.side_effect = Exception("Network error")

        result = reopen_issue(mock_gitea, "owner", "repo", 123, "test_token")

        assert result is False
