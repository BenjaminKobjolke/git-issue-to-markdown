"""CLI entry point for git-issue-to-markdown."""

import argparse
import sys
from pathlib import Path

from .config.settings import Settings
from .gitea_client import (
    create_client,
    download_attachment,
    get_issue_attachments,
    get_open_issues,
    is_image_file,
    parse_repo_url,
)
from .markdown_writer import get_existing_issue_ids, write_issues


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        prog="git-issue-to-markdown",
        description="Sync Gitea issues to a markdown file",
    )
    parser.add_argument("repo_url", help="Gitea repository URL")
    parser.add_argument("target_file", help="Target markdown file path")
    parser.add_argument(
        "--complete",
        metavar="FILE",
        help="File containing completed issues (issues marked here will be excluded)",
    )
    args = parser.parse_args()

    repo_url = args.repo_url
    target_file = Path(args.target_file)

    try:
        # Load settings
        settings = Settings.load()
        print(f"Loaded config from config.json")

        # Parse repository URL
        owner, repo_name = parse_repo_url(repo_url)
        print(f"Repository: {owner}/{repo_name}")

        # Connect to Gitea
        print(f"Connecting to {settings.gitea_url}...")
        gitea = create_client(settings)
        print(f"Gitea version: {gitea.get_version()}")

        # Fetch open issues
        print("Fetching open issues...")
        issues = get_open_issues(gitea, owner, repo_name)
        print(f"Found {len(issues)} open issue(s)")

        # Filter out completed issues if --complete file is provided
        if args.complete:
            complete_path = Path(args.complete)
            if complete_path.exists():
                completed_ids = get_existing_issue_ids(complete_path)
                if completed_ids:
                    print(f"Found {len(completed_ids)} completed issue(s) in {complete_path.name}")
                    issues = [i for i in issues if i.number not in completed_ids]
                    print(f"After filtering: {len(issues)} issue(s) to process")

        if not issues:
            print("No open issues to add.")
            return 0

        # Fetch comments for each issue
        print("Fetching comments...")
        comments_map: dict[int, list] = {}
        for issue in issues:
            comments = issue.get_comments()
            if comments:
                comments_map[issue.number] = comments
        total_comments = sum(len(c) for c in comments_map.values())
        print(f"Found {total_comments} comment(s) across {len(comments_map)} issue(s)")

        # Fetch and download attachments for each issue
        print("Fetching attachments...")
        attachments_map: dict[int, list[dict]] = {}
        attachments_dir = target_file.parent / "attachments"
        total_attachments = 0

        for issue in issues:
            raw_attachments = get_issue_attachments(gitea, owner, repo_name, issue.number)
            if not raw_attachments:
                continue

            issue_attachments: list[dict] = []
            issue_dir = attachments_dir / f"issue_{issue.number}"

            for att in raw_attachments:
                name = att.get("name", "attachment")
                download_url = att.get("browser_download_url", "")

                if not download_url:
                    continue

                # Download the file
                save_path = issue_dir / name
                if download_attachment(gitea, download_url, save_path):
                    # Build relative path from markdown file location
                    rel_path = f"./attachments/issue_{issue.number}/{name}"
                    issue_attachments.append({
                        "name": name,
                        "relative_path": rel_path,
                        "is_image": is_image_file(name),
                    })
                    total_attachments += 1

            if issue_attachments:
                attachments_map[issue.number] = issue_attachments

        if total_attachments > 0:
            print(f"Downloaded {total_attachments} attachment(s)")

        # Check for existing issues in the markdown file
        existing_ids = get_existing_issue_ids(target_file)
        if existing_ids:
            print(f"Found {len(existing_ids)} existing issue(s) in {target_file.name}")

        # Write issues (add new ones, update existing ones)
        added_count, updated_count = write_issues(
            target_file, issues, existing_ids, comments_map, attachments_map
        )

        if added_count > 0 or updated_count > 0:
            print(f"Added {added_count} new issue(s), updated {updated_count} existing issue(s)")
        else:
            print("No issues to write")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
