"""Gitea API client wrapper."""

from pathlib import Path
from urllib.parse import urlparse

from gitea import Gitea, Issue, Repository

from .config.settings import Settings


# Image file extensions for inline embedding
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}


def parse_repo_url(url: str) -> tuple[str, str]:
    """Parse a Gitea repository URL to extract owner and repo name.

    Args:
        url: Repository URL like https://xida.me:3030/Intern/turbo-habits-app
             or https://xida.me:3030/Intern/turbo-habits-app.git

    Returns:
        Tuple of (owner, repo_name)

    Raises:
        ValueError: If URL format is invalid.
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    # Remove .git suffix if present
    if path.endswith(".git"):
        path = path[:-4]

    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError(
            f"Invalid repository URL: {url}\n"
            f"Expected format: https://gitea.example.com/owner/repo"
        )

    owner = parts[0]
    repo_name = parts[1]

    return owner, repo_name


def create_client(settings: Settings) -> Gitea:
    """Create a Gitea client from settings.

    Args:
        settings: Application settings with Gitea URL and token.

    Returns:
        Configured Gitea client instance.
    """
    return Gitea(settings.gitea_url, settings.token, verify=settings.verify_ssl)


def get_open_issues(gitea: Gitea, owner: str, repo_name: str) -> list[Issue]:
    """Fetch all open issues from a repository.

    Args:
        gitea: Gitea client instance.
        owner: Repository owner (user or organization).
        repo_name: Repository name.

    Returns:
        List of open Issue objects.
    """
    repo = Repository.request(gitea, owner, repo_name)
    return repo.get_issues_state(Issue.OPENED)  # type: ignore[no-any-return]


def get_attachment_download_url(att: dict, gitea_url: str) -> str:
    """Extract download URL from attachment dict, trying multiple field names.

    Args:
        att: Attachment dict from API response.
        gitea_url: Base Gitea URL for constructing fallback URLs.

    Returns:
        Download URL or empty string if not found.
    """
    # Try different possible field names
    for field in ["browser_download_url", "download_url", "url"]:
        url = att.get(field, "")
        if url:
            return url

    # Fallback: construct URL from uuid if available
    uuid = att.get("uuid", "")
    if uuid:
        return f"{gitea_url}/attachments/{uuid}"

    return ""


def get_issue_attachments(gitea: Gitea, owner: str, repo_name: str, issue_number: int) -> list[dict]:
    """Fetch attachments for a specific issue.

    Args:
        gitea: Gitea client instance.
        owner: Repository owner.
        repo_name: Repository name.
        issue_number: Issue number.

    Returns:
        List of attachment dicts with 'name', 'browser_download_url', etc.
    """
    endpoint = f"/repos/{owner}/{repo_name}/issues/{issue_number}/assets"
    try:
        result = gitea.requests_get(endpoint)
        if result:
            print(f"  Issue #{issue_number}: Found {len(result)} attachment(s)")
        return result if result else []
    except Exception as e:
        print(f"  Warning: Failed to fetch attachments for issue #{issue_number}: {e}")
        return []


def get_comment_attachments(gitea: Gitea, owner: str, repo_name: str, comment_id: int) -> list[dict]:
    """Fetch attachments for a specific comment.

    Args:
        gitea: Gitea client instance.
        owner: Repository owner.
        repo_name: Repository name.
        comment_id: Comment ID.

    Returns:
        List of attachment dicts with 'name', 'browser_download_url', etc.
    """
    endpoint = f"/repos/{owner}/{repo_name}/issues/comments/{comment_id}/assets"
    try:
        result = gitea.requests_get(endpoint)
        return result if result else []
    except Exception as e:
        print(f"  Warning: Failed to fetch attachments for comment #{comment_id}: {e}")
        return []


def detect_image_type(content: bytes) -> str | None:
    """Detect actual image type from file content magic bytes.

    Args:
        content: File content bytes.

    Returns:
        Correct file extension (e.g., '.jpg', '.png') or None if not an image.
    """
    if content[:3] == b'\xff\xd8\xff':
        return '.jpg'
    elif content[:8] == b'\x89PNG\r\n\x1a\n':
        return '.png'
    elif content[:6] in (b'GIF87a', b'GIF89a'):
        return '.gif'
    elif content[:4] == b'RIFF' and content[8:12] == b'WEBP':
        return '.webp'
    elif content[:2] == b'BM':
        return '.bmp'
    return None


def download_attachment_file(gitea: Gitea, browser_download_url: str, token: str, save_path: Path) -> tuple[bool, Path]:
    """Download an attachment file from browser_download_url with token authentication.

    Args:
        gitea: Gitea client instance.
        browser_download_url: The browser_download_url from attachment metadata.
        token: API token for authentication.
        save_path: Path where the file should be saved.

    Returns:
        Tuple of (success, actual_save_path) - path may differ if extension was corrected.
    """
    try:
        # Append token to URL for authentication
        auth_url = f"{browser_download_url}?token={token}"
        response = gitea.requests.get(auth_url)
        response.raise_for_status()

        content = response.content

        # Detect actual image type and fix extension if needed
        actual_ext = detect_image_type(content)
        if actual_ext:
            current_ext = save_path.suffix.lower()
            if current_ext != actual_ext and current_ext in IMAGE_EXTENSIONS:
                # Extension mismatch - fix it
                save_path = save_path.with_suffix(actual_ext)
                print(f"    Note: Corrected extension from {current_ext} to {actual_ext}")

        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(content)
        print(f"    Downloaded: {save_path.name}")
        return True, save_path
    except Exception as e:
        print(f"    Warning: Failed to download {browser_download_url}: {e}")
        return False, save_path


def is_image_file(filename: str) -> bool:
    """Check if a filename is an image based on extension.

    Args:
        filename: The filename to check.

    Returns:
        True if the file is an image, False otherwise.
    """
    return Path(filename).suffix.lower() in IMAGE_EXTENSIONS
