# Task

Review the changes on branch `{{SOURCE_BRANCH}}` for Issue #{{ISSUE_NUMBER}} and fix what must be fixed, unattended. A person reviews the pull request after you, so your job is to make sure they get a correct change that follows this repo's standards.

## Issue #{{ISSUE_NUMBER}}: {{ISSUE_TITLE}}

{{ISSUE_CONTEXT}}

# Context

## Commits on this branch

!`git log --oneline {{BASE_BRANCH}}..HEAD`

## Diff against {{BASE_BRANCH}}

!`git diff {{BASE_BRANCH}}...HEAD`

# Review on two axes

1. **Task.** Does the change do what the Issue asks, all of it and nothing more? Are the edge cases the Issue mentions handled? Is every new or changed behaviour covered by a test through the public interface?
2. **Standards.** Does it follow `CODING_STANDARDS.md` (read it) and name things the way `GLOSSARY.md` does? Check also for unsafe assumptions, swallowed errors, leaked secrets and code that would fail silently.

Sort what you find:

- **Must-fix:** wrong behaviour, a missing or weak test, a broken standard. Fix these yourself on this branch.
- **Suggestions:** anything else worth a person's attention. Do not change the code for these; list them in your report.

# Fixing

- Change only what a must-fix finding needs. Keep the Issue's scope; never change behaviour the Issue did not ask to change.
- Run the Validation steps in order (`uv sync --locked`, `uv run pyright`, `uv run ruff check --extend-ignore EXE`, `uv run pytest`; the sandbox shows every file as executable, so ruff's file-mode rules are skipped here and CI runs them) and commit only when all pass. Message: a short imperative sentence, a blank line, `Related to #{{ISSUE_NUMBER}}`, a blank line, `Co-Authored-By: Claude <noreply@anthropic.com>`.
- If the change is already correct and clean, commit nothing.
- You have no GitHub access. Do not push or switch branches.

# Done

Finish with your report, exactly once, as JSON inside `<report>` tags, then the completion signal:

<report>
{"status": "GREEN", "summary": "What you checked, what you fixed and in which files, in two to five sentences.", "questions": ["Each suggestion or decision a person should check, one per entry."]}
</report>

- `status`: `GREEN` when the branch is correct and all four Validation steps pass; `RED` when a must-fix finding remains or a step fails; `BLOCKED` when the change cannot be made right without a person.

<promise>COMPLETE</promise>
