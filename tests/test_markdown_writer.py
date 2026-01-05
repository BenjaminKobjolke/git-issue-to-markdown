"""Tests for markdown_writer module."""

from pathlib import Path

import pytest

from git_issue_to_markdown.markdown_writer import (
    format_issue,
    get_existing_issue_ids,
    remove_existing_issues,
    write_issues,
)


class MockIssue:
    """Mock Issue class for testing."""

    def __init__(self, number: int, title: str, body: str = "") -> None:
        self.number = number
        self.title = title
        self.body = body


class TestGetExistingIssueIds:
    """Tests for get_existing_issue_ids function."""

    def test_returns_empty_set_for_nonexistent_file(self, tmp_path: Path) -> None:
        """Should return empty set if file doesn't exist."""
        md_path = tmp_path / "nonexistent.md"
        result = get_existing_issue_ids(md_path)
        assert result == set()

    def test_returns_empty_set_for_file_without_markers(self, tmp_path: Path) -> None:
        """Should return empty set if file has no issue markers."""
        md_path = tmp_path / "test.md"
        md_path.write_text("# Some Header\n\nSome content\n")
        result = get_existing_issue_ids(md_path)
        assert result == set()

    def test_finds_single_issue_marker(self, tmp_path: Path) -> None:
        """Should find a single issue marker."""
        md_path = tmp_path / "test.md"
        md_path.write_text("## #123: Test Issue\n<!-- GITEA_ISSUE:123 -->\n")
        result = get_existing_issue_ids(md_path)
        assert result == {123}

    def test_finds_multiple_issue_markers(self, tmp_path: Path) -> None:
        """Should find multiple issue markers."""
        md_path = tmp_path / "test.md"
        content = """## #1: First Issue
<!-- GITEA_ISSUE:1 -->
Description

## #42: Second Issue
<!-- GITEA_ISSUE:42 -->
Another description

## #999: Third Issue
<!-- GITEA_ISSUE:999 -->
"""
        md_path.write_text(content)
        result = get_existing_issue_ids(md_path)
        assert result == {1, 42, 999}


class TestRemoveExistingIssues:
    """Tests for remove_existing_issues function."""

    def test_returns_empty_for_nonexistent_file(self, tmp_path: Path) -> None:
        """Should return empty string if file doesn't exist."""
        md_path = tmp_path / "nonexistent.md"
        result = remove_existing_issues(md_path, {1})
        assert result == ""

    def test_removes_single_issue(self, tmp_path: Path) -> None:
        """Should remove a single issue section."""
        md_path = tmp_path / "test.md"
        content = """# Header

## #123: Test Issue
<!-- GITEA_ISSUE:123 -->
Body content
"""
        md_path.write_text(content)
        result = remove_existing_issues(md_path, {123})
        assert "## #123:" not in result
        assert "# Header" in result

    def test_removes_multiple_issues(self, tmp_path: Path) -> None:
        """Should remove multiple issue sections."""
        md_path = tmp_path / "test.md"
        content = """## #1: First
<!-- GITEA_ISSUE:1 -->
Body 1

## #2: Second
<!-- GITEA_ISSUE:2 -->
Body 2
"""
        md_path.write_text(content)
        result = remove_existing_issues(md_path, {1, 2})
        assert "## #1:" not in result
        assert "## #2:" not in result


class TestFormatIssue:
    """Tests for format_issue function."""

    def test_formats_issue_with_body(self) -> None:
        """Should format issue with title and body."""
        issue = MockIssue(123, "Test Issue", "This is the body")
        result = format_issue(issue)  # type: ignore[arg-type]
        assert "## #123: Test Issue" in result
        assert "<!-- GITEA_ISSUE:123 -->" in result
        assert "This is the body" in result

    def test_formats_issue_without_body(self) -> None:
        """Should format issue without body."""
        issue = MockIssue(456, "No Body Issue", "")
        result = format_issue(issue)  # type: ignore[arg-type]
        assert "## #456: No Body Issue" in result
        assert "<!-- GITEA_ISSUE:456 -->" in result


class TestWriteIssues:
    """Tests for write_issues function."""

    def test_creates_file_if_not_exists(self, tmp_path: Path) -> None:
        """Should create file if it doesn't exist."""
        md_path = tmp_path / "new.md"
        issue = MockIssue(1, "New Issue", "Body")
        added, updated = write_issues(md_path, [issue], set())  # type: ignore[list-item]
        assert added == 1
        assert updated == 0
        assert md_path.exists()
        content = md_path.read_text()
        assert "## #1: New Issue" in content

    def test_appends_to_existing_file(self, tmp_path: Path) -> None:
        """Should append to existing file."""
        md_path = tmp_path / "existing.md"
        md_path.write_text("# Existing Content\n")
        issue = MockIssue(2, "Appended Issue", "Body")
        added, updated = write_issues(md_path, [issue], set())  # type: ignore[list-item]
        assert added == 1
        assert updated == 0
        content = md_path.read_text()
        assert "# Existing Content" in content
        assert "## #2: Appended Issue" in content

    def test_updates_existing_issues(self, tmp_path: Path) -> None:
        """Should update issues that already exist."""
        md_path = tmp_path / "test.md"
        md_path.write_text("## #1: Old Title\n<!-- GITEA_ISSUE:1 -->\nOld body\n")
        issue = MockIssue(1, "New Title", "New body")
        added, updated = write_issues(md_path, [issue], {1})  # type: ignore[list-item]
        assert added == 0
        assert updated == 1
        content = md_path.read_text()
        assert "## #1: New Title" in content
        assert "New body" in content
        assert "Old Title" not in content

    def test_adds_new_and_updates_existing(self, tmp_path: Path) -> None:
        """Should add new issues and update existing ones."""
        md_path = tmp_path / "test.md"
        md_path.write_text("## #1: Existing\n<!-- GITEA_ISSUE:1 -->\nBody\n")
        issues = [
            MockIssue(1, "Updated", "New body"),
            MockIssue(2, "Brand New", "Fresh"),
        ]
        added, updated = write_issues(md_path, issues, {1})  # type: ignore[arg-type]
        assert added == 1
        assert updated == 1
        content = md_path.read_text()
        assert "## #1: Updated" in content
        assert "## #2: Brand New" in content

    def test_returns_zero_for_empty_list(self, tmp_path: Path) -> None:
        """Should return (0, 0) for empty issue list."""
        md_path = tmp_path / "test.md"
        added, updated = write_issues(md_path, [], set())
        assert added == 0
        assert updated == 0
