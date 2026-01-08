@echo off
:: Git Issue to Markdown - Close a Gitea issue
::
:: Usage: close.bat <repo_url> <issue_number>
:: Example: close.bat https://xida.me:3030/Intern/turbo-habits-app 123

uv run python -m git_issue_to_markdown.main %1 --close %2
