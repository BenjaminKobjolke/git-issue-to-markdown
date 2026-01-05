@echo off
:: Git Issue to Markdown - Fetch Gitea issues and add to markdown file
::
:: Usage: start.bat <repo_url> <target_md_file>
:: Example: start.bat https://xida.me:3030/Intern/turbo-habits-app D:\path\to\TODO.md

uv run python -m git_issue_to_markdown.main %*
