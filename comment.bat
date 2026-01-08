@echo off
:: Git Issue to Markdown - Add comment to a Gitea issue
::
:: Usage: comment.bat <repo_url> <issue_number> <comment_text>
::    or: comment.bat <repo_url> <issue_number> -file <path>
:: Example: comment.bat https://xida.me:3030/Intern/turbo-habits-app 123 "Fixed in commit abc"
:: Example: comment.bat https://xida.me:3030/Intern/turbo-habits-app 123 -file comment.md

uv run python -m git_issue_to_markdown.main %1 --comment %2 %3 %4
