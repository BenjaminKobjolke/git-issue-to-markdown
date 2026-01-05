"""Markdown file operations for issue management."""

import re
from pathlib import Path
from typing import TYPE_CHECKING

from .config.constants import Constants

if TYPE_CHECKING:
    from gitea import Issue


def get_existing_issue_ids(md_path: Path) -> set[int]:
    """Parse a markdown file to find existing Gitea issue IDs.

    Looks for markers like: <!-- GITEA_ISSUE:123 -->

    Args:
        md_path: Path to the markdown file.

    Returns:
        Set of issue IDs already present in the file.
    """
    if not md_path.exists():
        return set()

    content = md_path.read_text(encoding="utf-8")
    pattern = Constants.ISSUE_MARKER_PATTERN
    matches = re.findall(pattern, content)

    return {int(issue_id) for issue_id in matches}


def remove_existing_issues(md_path: Path, issue_ids: set[int]) -> str:
    """Remove existing issue sections from a markdown file.

    Removes sections that start with ## #<id>: and contain the GITEA_ISSUE marker.

    Args:
        md_path: Path to the markdown file.
        issue_ids: Set of issue IDs to remove.

    Returns:
        The cleaned content with issue sections removed.
    """
    if not md_path.exists():
        return ""

    content = md_path.read_text(encoding="utf-8")

    for issue_id in issue_ids:
        # Pattern to match: ## #<id>: ... until the next ## or end of file
        # This captures the heading, marker, and body
        pattern = rf"## #{issue_id}:.*?(?=\n## |\Z)"
        content = re.sub(pattern, "", content, flags=re.DOTALL)

    # Clean up multiple consecutive newlines
    content = re.sub(r"\n{3,}", "\n\n", content)

    return content.strip()


def format_issue(
    issue: "Issue",
    comments: list | None = None,
    attachments: list[dict] | None = None,
) -> str:
    """Format a single issue as markdown, including comments and attachments.

    Args:
        issue: Gitea Issue object.
        comments: Optional list of Comment objects for this issue.
        attachments: Optional list of attachment dicts with 'name', 'is_image', 'relative_path'.

    Returns:
        Formatted markdown string for the issue.
    """
    marker = Constants.ISSUE_MARKER_TEMPLATE.format(issue_id=issue.number)
    body = issue.body.strip() if issue.body else ""

    lines = [
        f"## #{issue.number}: {issue.title}",
        marker,
    ]

    if body:
        lines.append(body)

    # Add attachments if any
    if attachments:
        lines.append("")
        lines.append("### Attachments")
        for att in attachments:
            name = att.get("name", "attachment")
            rel_path = att.get("relative_path", "")
            is_image = att.get("is_image", False)

            if is_image:
                # Embed image inline
                lines.append(f"![{name}]({rel_path})")
            else:
                # Link to file
                lines.append(f"- [{name}]({rel_path})")

    # Add comments if any
    if comments:
        lines.append("")
        lines.append("### Comments")
        for comment in comments:
            user = comment.user.username if hasattr(comment, "user") and comment.user else "Unknown"
            comment_body = comment.body.strip() if hasattr(comment, "body") and comment.body else ""
            if comment_body:
                lines.append(f"\n**{user}:**")
                lines.append(comment_body)

    lines.append("")  # Empty line after each issue

    return "\n".join(lines)


def write_issues(
    md_path: Path,
    issues: list["Issue"],
    existing_ids: set[int],
    comments_map: dict[int, list] | None = None,
    attachments_map: dict[int, list[dict]] | None = None,
) -> tuple[int, int]:
    """Write issues to a markdown file, updating existing ones.

    Removes existing issue sections and rewrites them with fresh content.

    Args:
        md_path: Path to the markdown file.
        issues: List of Gitea Issue objects to write.
        existing_ids: Set of issue IDs already in the file.
        comments_map: Optional dict mapping issue number to list of comments.
        attachments_map: Optional dict mapping issue number to list of attachment info.

    Returns:
        Tuple of (issues_added, issues_updated).
    """
    if not issues:
        return 0, 0

    comments_map = comments_map or {}
    attachments_map = attachments_map or {}

    # Determine which issues are new vs updates
    issue_ids_to_write = {issue.number for issue in issues}
    ids_to_update = issue_ids_to_write & existing_ids
    ids_to_add = issue_ids_to_write - existing_ids

    # Remove existing issue sections that we're going to rewrite
    if ids_to_update:
        cleaned_content = remove_existing_issues(md_path, ids_to_update)
    elif md_path.exists():
        cleaned_content = md_path.read_text(encoding="utf-8").strip()
    else:
        cleaned_content = ""

    # Build the new content for all issues (with comments and attachments)
    content_parts = [
        format_issue(
            issue,
            comments_map.get(issue.number),
            attachments_map.get(issue.number),
        )
        for issue in issues
    ]
    new_content = "\n".join(content_parts)

    # Combine existing content with new issues
    if cleaned_content:
        final_content = cleaned_content + "\n\n" + new_content
    else:
        final_content = new_content

    md_path.write_text(final_content, encoding="utf-8")

    return len(ids_to_add), len(ids_to_update)
