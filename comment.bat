@echo off
:: Git Issue to Markdown - Add comment to a Gitea issue
::
:: Usage: comment.bat <repo_url> <issue_number> <comment_text>
:: Example: comment.bat https://xida.me:3030/Intern/turbo-habits-app 123 "Fixed in commit abc"

uv run python -m git_issue_to_markdown.main %1 --comment %2 %3
