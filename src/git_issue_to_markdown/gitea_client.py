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
        return result if result else []
    except Exception:
        # API might not support attachments or issue has none
        return []


def download_attachment(gitea: Gitea, download_url: str, save_path: Path) -> bool:
    """Download an attachment file.

    Args:
        gitea: Gitea client instance.
        download_url: URL to download the attachment from.
        save_path: Path where the file should be saved.

    Returns:
        True if download succeeded, False otherwise.
    """
    try:
        # Use the gitea session which has auth headers
        response = gitea.requests.get(download_url)
        response.raise_for_status()

        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(response.content)
        return True
    except Exception:
        return False


def is_image_file(filename: str) -> bool:
    """Check if a filename is an image based on extension.

    Args:
        filename: The filename to check.

    Returns:
        True if the file is an image, False otherwise.
    """
    return Path(filename).suffix.lower() in IMAGE_EXTENSIONS
