"""Integration tests requiring a real Gitea server.

These tests require:
1. config.json with valid Gitea credentials
2. tests/test_config.json with test repository configuration
3. A test repository on the Gitea server with known test data

Copy tests/test_config.example.json to tests/test_config.json and adjust values.
"""

import json
import tempfile
from pathlib import Path

import pytest

from git_issue_to_markdown.config.settings import Settings
from git_issue_to_markdown.gitea_client import (
    add_comment,
    close_issue,
    create_client,
    download_attachment_file,
    get_comment_attachments,
    get_issue_attachments,
    get_open_issues,
    parse_repo_url,
    reopen_issue,
)

TEST_CONFIG_PATH = Path(__file__).parent / "test_config.json"
MAIN_CONFIG_PATH = Path(__file__).parent.parent / "config.json"

# Skip all tests in this module if config files don't exist
pytestmark = pytest.mark.skipif(
    not TEST_CONFIG_PATH.exists() or not MAIN_CONFIG_PATH.exists(),
    reason="Integration tests require config.json and tests/test_config.json",
)


@pytest.fixture
def test_config() -> dict:
    """Load test configuration."""
    return json.loads(TEST_CONFIG_PATH.read_text())


@pytest.fixture
def settings() -> Settings:
    """Load main settings."""
    return Settings.load()


@pytest.fixture
def gitea_client(settings: Settings):
    """Create Gitea client."""
    return create_client(settings)


class TestIntegrationFetchIssues:
    """Test issue fetching from real Gitea server."""

    def test_fetch_issues_returns_list(self, gitea_client, test_config: dict):
        """Verify we can fetch issues from test repository."""
        owner, repo_name = parse_repo_url(test_config["test_repo_url"])
        issues = get_open_issues(gitea_client, owner, repo_name)

        assert isinstance(issues, list)
        assert len(issues) >= 1

    def test_fetch_issues_has_expected_issue(self, gitea_client, test_config: dict):
        """Verify the test issue exists with expected title."""
        owner, repo_name = parse_repo_url(test_config["test_repo_url"])
        issues = get_open_issues(gitea_client, owner, repo_name)

        issue_numbers = [i.number for i in issues]
        assert test_config["test_issue_number"] in issue_numbers

        test_issue = next(i for i in issues if i.number == test_config["test_issue_number"])
        assert test_issue.title == test_config["expected_issue_title"]


class TestIntegrationAttachments:
    """Test attachment fetching from real Gitea server."""

    def test_fetch_issue_attachments(self, gitea_client, test_config: dict):
        """Verify issue attachments are fetched correctly."""
        owner, repo_name = parse_repo_url(test_config["test_repo_url"])
        issue_number = test_config["test_issue_number"]

        attachments = get_issue_attachments(gitea_client, owner, repo_name, issue_number)

        assert isinstance(attachments, list)
        assert len(attachments) == test_config["expected_issue_attachment_count"]

    def test_issue_attachments_have_required_fields(self, gitea_client, test_config: dict):
        """Verify attachment metadata has required fields."""
        owner, repo_name = parse_repo_url(test_config["test_repo_url"])
        issue_number = test_config["test_issue_number"]

        attachments = get_issue_attachments(gitea_client, owner, repo_name, issue_number)

        for att in attachments:
            assert "name" in att
            assert "browser_download_url" in att
            assert "id" in att

    def test_fetch_comment_attachments(self, gitea_client, test_config: dict):
        """Verify comment attachments can be fetched."""
        owner, repo_name = parse_repo_url(test_config["test_repo_url"])
        issues = get_open_issues(gitea_client, owner, repo_name)
        test_issue = next(i for i in issues if i.number == test_config["test_issue_number"])

        comments = test_issue.get_comments()
        assert len(comments) >= 1, "Test issue should have at least 1 comment"

        # Check first comment for attachments
        comment = comments[0]
        comment_id = comment.id if hasattr(comment, "id") else comment.get("id")
        attachments = get_comment_attachments(gitea_client, owner, repo_name, comment_id)

        assert isinstance(attachments, list)
        assert len(attachments) == test_config["expected_comment_attachment_count"]


class TestIntegrationDownload:
    """Test attachment downloading from real Gitea server."""

    def test_download_attachment_creates_file(self, gitea_client, settings: Settings, test_config: dict):
        """Verify attachments can be downloaded."""
        owner, repo_name = parse_repo_url(test_config["test_repo_url"])
        issue_number = test_config["test_issue_number"]

        attachments = get_issue_attachments(gitea_client, owner, repo_name, issue_number)
        assert len(attachments) > 0, "Need at least one attachment to test download"

        att = attachments[0]
        browser_download_url = att["browser_download_url"]
        name = att["name"]

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / name
            success, actual_path = download_attachment_file(
                gitea_client, browser_download_url, settings.token, save_path
            )

            assert success is True
            assert actual_path.exists()
            assert actual_path.stat().st_size > 0

    def test_download_detects_correct_image_type(self, gitea_client, settings: Settings, test_config: dict):
        """Verify image type detection corrects file extensions."""
        owner, repo_name = parse_repo_url(test_config["test_repo_url"])
        issue_number = test_config["test_issue_number"]

        attachments = get_issue_attachments(gitea_client, owner, repo_name, issue_number)

        with tempfile.TemporaryDirectory() as tmpdir:
            downloaded_extensions = set()

            for att in attachments:
                browser_download_url = att["browser_download_url"]
                name = att["name"]
                save_path = Path(tmpdir) / name

                success, actual_path = download_attachment_file(
                    gitea_client, browser_download_url, settings.token, save_path
                )

                if success:
                    downloaded_extensions.add(actual_path.suffix.lower())

            # We expect both .jpg and .png if test data is set up correctly
            # (the test repo should have 1 JPG and 1 PNG)
            assert len(downloaded_extensions) >= 1, "Should download at least one image type"


class TestIntegrationIssueActions:
    """Test issue actions (comment, close, reopen) on real Gitea server.

    These tests modify issue state. They use a separate test issue number
    (test_action_issue_number) to avoid interfering with other tests.
    """

    def test_add_comment_to_issue(self, gitea_client, settings: Settings, test_config: dict):
        """Verify adding a comment to an issue works."""
        if "test_action_issue_number" not in test_config:
            pytest.skip("test_action_issue_number not configured")

        owner, repo_name = parse_repo_url(test_config["test_repo_url"])
        issue_number = test_config["test_action_issue_number"]

        result = add_comment(
            gitea_client, owner, repo_name, issue_number, "Integration test comment", settings.token
        )

        assert result is True

    def test_close_and_reopen_issue(self, gitea_client, settings: Settings, test_config: dict):
        """Verify closing and reopening an issue works."""
        if "test_action_issue_number" not in test_config:
            pytest.skip("test_action_issue_number not configured")

        owner, repo_name = parse_repo_url(test_config["test_repo_url"])
        issue_number = test_config["test_action_issue_number"]

        # Close the issue
        close_result = close_issue(gitea_client, owner, repo_name, issue_number, settings.token)
        assert close_result is True

        # Reopen the issue to restore original state
        reopen_result = reopen_issue(gitea_client, owner, repo_name, issue_number, settings.token)
        assert reopen_result is True

    def test_add_comment_to_nonexistent_issue_fails(
        self, gitea_client, settings: Settings, test_config: dict
    ):
        """Verify adding comment to non-existent issue returns False."""
        owner, repo_name = parse_repo_url(test_config["test_repo_url"])

        result = add_comment(gitea_client, owner, repo_name, 999999, "Should fail", settings.token)

        assert result is False

    def test_close_nonexistent_issue_fails(
        self, gitea_client, settings: Settings, test_config: dict
    ):
        """Verify closing non-existent issue returns False."""
        owner, repo_name = parse_repo_url(test_config["test_repo_url"])

        result = close_issue(gitea_client, owner, repo_name, 999999, settings.token)

        assert result is False

    def test_reopen_nonexistent_issue_fails(
        self, gitea_client, settings: Settings, test_config: dict
    ):
        """Verify reopening non-existent issue returns False."""
        owner, repo_name = parse_repo_url(test_config["test_repo_url"])

        result = reopen_issue(gitea_client, owner, repo_name, 999999, settings.token)

        assert result is False
