"""CLI entry point for git-issue-to-markdown."""

import argparse
import sys
from pathlib import Path

from .config.settings import Settings
from .gitea_client import (
    add_comment,
    close_issue,
    create_client,
    download_attachment_file,
    get_comment_attachments,
    get_issue_attachments,
    get_open_issues,
    is_image_file,
    parse_repo_url,
    reopen_issue,
)
from .markdown_writer import get_existing_issue_ids, write_issues


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        prog="git-issue-to-markdown",
        description="Sync Gitea issues to a markdown file, or perform actions on issues",
    )
    parser.add_argument("repo_url", help="Gitea repository URL")
    parser.add_argument(
        "target_file",
        nargs="?",
        help="Target markdown file path (required for sync, optional for actions)",
    )
    parser.add_argument(
        "--complete",
        metavar="FILE",
        help="File containing completed issues (issues marked here will be excluded)",
    )
    parser.add_argument(
        "--comment",
        nargs=2,
        metavar=("ISSUE", "TEXT"),
        help="Add a comment to an issue (e.g., --comment 123 'Fixed in commit abc')",
    )
    parser.add_argument(
        "--close",
        type=int,
        metavar="ISSUE",
        help="Close an issue by number",
    )
    parser.add_argument(
        "--reopen",
        type=int,
        metavar="ISSUE",
        help="Reopen a closed issue by number",
    )
    args = parser.parse_args()

    # Check if we're performing actions instead of syncing
    has_actions = args.comment or args.close or args.reopen

    # Require target_file for sync mode (no actions)
    if not has_actions and not args.target_file:
        parser.error("target_file is required when not using --comment, --close, or --reopen")

    repo_url = args.repo_url
    target_file = Path(args.target_file) if args.target_file else None

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

        # Handle actions if provided
        if has_actions:
            success = True

            # Add comment
            if args.comment:
                issue_num = int(args.comment[0])
                comment_text = args.comment[1]
                print(f"Adding comment to issue #{issue_num}...")
                if add_comment(gitea, owner, repo_name, issue_num, comment_text, settings.token):
                    print(f"Comment added to issue #{issue_num}")
                else:
                    print(f"Failed to add comment to issue #{issue_num}")
                    success = False

            # Close issue
            if args.close:
                print(f"Closing issue #{args.close}...")
                if close_issue(gitea, owner, repo_name, args.close, settings.token):
                    print(f"Issue #{args.close} closed")
                else:
                    print(f"Failed to close issue #{args.close}")
                    success = False

            # Reopen issue
            if args.reopen:
                print(f"Reopening issue #{args.reopen}...")
                if reopen_issue(gitea, owner, repo_name, args.reopen, settings.token):
                    print(f"Issue #{args.reopen} reopened")
                else:
                    print(f"Failed to reopen issue #{args.reopen}")
                    success = False

            return 0 if success else 1

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

        # Fetch and download attachments for each issue (from issue body and comments)
        print("Fetching attachments...")
        attachments_map: dict[int, list[dict]] = {}
        attachments_dir = target_file.parent / "attachments"
        total_issue_attachments = 0
        total_comment_attachments = 0

        for issue in issues:
            issue_attachments: list[dict] = []
            issue_dir = attachments_dir / f"issue_{issue.number}"

            # Fetch attachments from the issue itself
            raw_attachments = get_issue_attachments(gitea, owner, repo_name, issue.number)
            for att in raw_attachments:
                name = att.get("name", "attachment")
                browser_download_url = att.get("browser_download_url", "")

                if not browser_download_url:
                    print(f"    Warning: No download URL found for '{name}'")
                    continue

                # Download the file using browser_download_url with token auth
                save_path = issue_dir / name
                success, actual_path = download_attachment_file(gitea, browser_download_url, settings.token, save_path)
                if success:
                    # Build relative path from markdown file location (use actual filename)
                    actual_name = actual_path.name
                    rel_path = f"./attachments/issue_{issue.number}/{actual_name}"
                    issue_attachments.append({
                        "name": actual_name,
                        "relative_path": rel_path,
                        "is_image": is_image_file(actual_name),
                    })
                    total_issue_attachments += 1

            # Fetch attachments from comments
            issue_comments = comments_map.get(issue.number, [])
            for comment in issue_comments:
                comment_id = comment.id if hasattr(comment, 'id') else comment.get('id')
                if not comment_id:
                    continue

                comment_attachments_list = get_comment_attachments(gitea, owner, repo_name, comment_id)
                if comment_attachments_list:
                    print(f"  Comment #{comment_id}: Found {len(comment_attachments_list)} attachment(s)")

                for att in comment_attachments_list:
                    name = att.get("name", "attachment")
                    browser_download_url = att.get("browser_download_url", "")

                    if not browser_download_url:
                        print(f"    Warning: No download URL found for comment attachment '{name}'")
                        continue

                    # Download the file using browser_download_url with token auth
                    save_path = issue_dir / f"comment_{comment_id}" / name
                    success, actual_path = download_attachment_file(gitea, browser_download_url, settings.token, save_path)
                    if success:
                        actual_name = actual_path.name
                        rel_path = f"./attachments/issue_{issue.number}/comment_{comment_id}/{actual_name}"
                        issue_attachments.append({
                            "name": actual_name,
                            "relative_path": rel_path,
                            "is_image": is_image_file(actual_name),
                        })
                        total_comment_attachments += 1

            if issue_attachments:
                attachments_map[issue.number] = issue_attachments

        total_attachments = total_issue_attachments + total_comment_attachments
        if total_attachments > 0:
            print(f"Downloaded {total_attachments} attachment(s) ({total_issue_attachments} from issues, {total_comment_attachments} from comments)")

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
