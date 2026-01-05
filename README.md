# git-issue-to-markdown

CLI tool to fetch open issues from a Gitea repository and add them to a markdown file.

## Features

- Fetches open issues from Gitea repositories
- Includes issue comments
- Downloads and embeds attachments (images shown inline)
- Updates existing issues with latest content
- Detects duplicates using HTML comment markers

## Installation

1. Clone this repository
2. Run `install.bat` to set up the environment

## Configuration

Edit `config.json` with your Gitea credentials:

```json
{
  "gitea_url": "https://your-gitea-instance.com",
  "token": "your-api-token",
  "verify_ssl": false
}
```

## Usage

```bash
start.bat <repo_url> <target_md_file>
```

### Examples

```bash
# Add issues from a repository to a TODO file
start.bat https://your-gitea-instance.com/USER/PROJECT D:\path\to\TODO.md

# Works with .git suffix too
start.bat https://your-gitea-instance.com/USER/project.git D:\path\to\TODO.md
```

## Output Format

Issues are added in heading format with comments and attachments:

```markdown
## #123: Issue Title
<!-- GITEA_ISSUE:123 -->
Issue description here

### Attachments
![screenshot.png](./attachments/issue_123/screenshot.png)
- [document.pdf](./attachments/issue_123/document.pdf)

### Comments

**username:**
This is a comment on the issue.

**another_user:**
Another comment here.
```

The `<!-- GITEA_ISSUE:123 -->` marker is used to detect and update existing issues.

### Attachments

Attachments are automatically downloaded to an `attachments` folder next to your markdown file:

```
your_file.md
attachments/
  issue_123/
    screenshot.png
    document.pdf
  issue_456/
    diagram.png
```

- Images (png, jpg, gif, etc.) are embedded inline
- Other files are added as download links

## Development

### Run tests

```bash
tools\tests.bat
```

### Update dependencies

```bash
update.bat
```

## Dependencies

- [py-gitea](https://github.com/Langenfeld/py-gitea) - Gitea API wrapper
