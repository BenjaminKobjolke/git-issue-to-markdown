@echo off
:: Git Issue to Markdown - Close a Gitea issue with a comment
::
:: Usage: closewithcomment.bat <repo_url> <issue_number> <comment_text>
::    or: closewithcomment.bat <repo_url> <issue_number> -file <path>
:: Example: closewithcomment.bat https://xida.me:3030/Intern/turbo-habits-app 123 "Fixed in commit abc"
:: Example: closewithcomment.bat https://xida.me:3030/Intern/turbo-habits-app 123 -file comment.md

uv run python -m git_issue_to_markdown.main %1 --close %2 --comment %2 %3 %4
