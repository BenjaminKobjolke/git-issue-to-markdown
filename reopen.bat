@echo off
:: Git Issue to Markdown - Reopen a closed Gitea issue
::
:: Usage: reopen.bat <repo_url> <issue_number>
:: Example: reopen.bat https://xida.me:3030/Intern/turbo-habits-app 123

uv run python -m git_issue_to_markdown.main %1 --reopen %2
