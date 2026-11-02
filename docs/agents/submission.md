# Submission: GitHub pull requests

How a change becomes a pull request in `diegaccio/claude-code-demo-chat`. The operations say how; the procedure says what the team expects. Run every command inside a clone.

## Operations

Placeholders: `<branch>` the source branch, `<target>` the target branch, `<mr>` a pull request number, `<title>`, `<body-file>` a file holding the Markdown description, `<labels>`, `<usernames>` comma-separated, `<id>` a Task's Issue number.

| Operation | Command | Notes |
| --------- | ------- | ----- |
| find | `gh pr list --head <branch> --state open --json number,url,isDraft` | An open pull request from the same source branch is the one to update; never open a second. |
| create | `gh pr create --head <branch> --base <target> --title "<title>" --body-file <body-file>` | Add `--draft` when the procedure says so; add `--label "<labels>"` only when the procedure names labels. |
| update | `gh pr edit <mr> --title "<title>" --body-file <body-file>` | `gh pr ready <mr>` marks a draft ready; `gh pr ready <mr> --undo` turns it back. |
| set reviewers | `gh pr edit <mr> --add-reviewer "<usernames>"` | |
| link Task | A `Related to #<id>` line in the description. | A closing keyword (`Closes #<id>`) only when `task-workflow.md` says merging closes the Task. |

## Procedure

- **Target branch:** `main`
- **Title convention:** the Task's title, prefixed with `#<id>` (for example `#12 Add login endpoint`)
- **Draft use:** open as draft while work continues; mark ready when the Validation steps are green
- **Required checks:** none yet (no CI workflow): run the Validation steps locally before marking the pull request ready; list the CI workflows here once one exists
- **Labels:** none
- **Reviewer choice:** one primary software engineer for the touched component from the team map; never the author. When no one matches, leave reviewers unset and flag the choice to the user

The author never merges their own pull request through an agent: merging follows the team's review.
