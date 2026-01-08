@echo off
:: Git Issue to Markdown - Close a Gitea issue with a comment
::
:: Usage: closewithcomment.bat <repo_url> <issue_number> <comment_text>
:: Example: closewithcomment.bat https://xida.me:3030/Intern/turbo-habits-app 123 "Fixed in commit abc"

uv run python -m git_issue_to_markdown.main %1 --close %2 --comment %2 %3
