# Issue tracker: GitHub

Tasks and Blueprints are GitHub issues of `diegaccio/claude-code-demo-chat`. Run every command inside a clone: the GitHub CLI infers the repository from the `origin` remote, and `{owner}/{repo}` in an API path stands for it.

## Operations

Placeholders: `<id>` an issue number, `<title>`, `<body-file>` a file holding the Markdown body, `<labels>` comma-separated label strings from `task-workflow.md`, `<parent>` the parent Issue's number, `<blocker>` the blocking Issue's number, `<username>`, `<text>`.

Sub-issues and blocking links go through `gh api`, because the installed GitHub CLI (2.92) has no `--parent` or `--add-blocked-by` flag. Both API calls take the issue's internal `id`, not its number: `gh api repos/{owner}/{repo}/issues/<number> --jq .id`.

| Operation | Command | Notes |
| --------- | ------- | ----- |
| create | `gh issue create --title "<title>" --body-file <body-file> --label "<labels>"` | Prints the new issue's URL; its number ends the URL. With a parent: put `## Parent` and `#<parent>` at the top of the body, then attach it with `gh api repos/{owner}/{repo}/issues/<parent>/sub_issues -X POST -F sub_issue_id=<new issue's id>`. |
| read | `gh issue view <id> --comments` | |
| list by label | `gh issue list --label "<labels>" --state open --limit 1000 --json number,title,labels,assignees` | One label per call: several labels are ANDed, so to find Issues carrying any of them, run it once per label and merge the results. `--state all` for closed issues too. Without `--limit`, only 30 come back. |
| comment | `gh issue comment <id> --body "<text>"` | |
| add label | `gh issue edit <id> --add-label "<labels>"` | Labels are plain: before adding a workflow-role or Tier label, remove the issue's previous one with **remove label**. |
| remove label | `gh issue edit <id> --remove-label "<labels>"` | |
| close | `gh issue close <id>` | Post the explanation with **comment** first. |
| link blocking | `gh api repos/{owner}/{repo}/issues/<id>/dependencies/blocked_by -X POST -F issue_id=<blocker's id>` | Native issue dependencies (see Capabilities). |
| list blockers | `gh api repos/{owner}/{repo}/issues/<id>/dependencies/blocked_by --jq '[.[] \| select(.state == "open") \| .number]'` | Unblocked when the list is empty. |
| find children | `gh api repos/{owner}/{repo}/issues/<parent>/sub_issues --jq '[.[].number]'` | |
| current user | `gh api user --jq .login` | |
| verify username | `gh api users/<username> --jq .login` | Valid only when it prints exactly `<username>`. Never accept a similar-looking name. |
| assign | `gh issue edit <id> --add-assignee "<username>"` | |

## Capabilities

Status is `supported`, `missing` (the fallback was confirmed by the user) or `unconfirmed` (not yet settled: counts as missing configuration).

| Capability | Status | Probe | Fallback when missing |
| ---------- | ------ | ----- | --------------------- |
| Native issue dependencies | supported | **list blockers** answered on github.com (2026-11-02). | |
| Sub-issues | supported | **find children** answered on github.com (2026-11-02). | |
| Multiple assignees | supported | | |
| Scoped labels | missing | GitHub has none. | Labels are plain: before adding a state label, remove the issue's previous state label. |

## Pull requests as a request surface

**no.** Set to `yes` if external pull requests are triaged like Issues. GitHub shares one number space between issues and pull requests.
