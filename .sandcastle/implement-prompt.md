# Task

You are implementing one Task of the Demo app, unattended. Nobody will answer questions during this run: when something is unclear, say so in your report instead of guessing.

## Issue #{{ISSUE_NUMBER}}: {{ISSUE_TITLE}}

{{ISSUE_CONTEXT}}

# Context

You are on branch `{{SOURCE_BRANCH}}`, created from `{{BASE_BRANCH}}`.

## Recent commits on {{BASE_BRANCH}}

!`git log --oneline -10 {{BASE_BRANCH}}`

## Read before you change anything

- `CODING_STANDARDS.md`: the patterns the code follows. Your change must follow them.
- `GLOSSARY.md` and `docs/agents/domain.md`: the domain language. Name things the way the glossary does.
- `docs/agents/validation.md`: the Validation steps.
- The source files and tests the Issue touches.

# Workflow

1. **Explore.** Read the Issue, the files above and the code it touches. If the Issue names a parent Blueprint, its decisions are in the Issue text above.
2. **Plan.** Keep the change as small as the Issue allows. Do nothing the Issue does not ask for.
3. **Build test-first,** in vertical red-green steps: write one failing test through the public interface, make it pass, repeat, then refactor while green. Test behaviour, not internals.
4. **Validate.** Run the Validation steps, in order, from the repository root, and fix every failure:
   - `uv sync --locked`
   - `uv run pyright`
   - `uv run ruff check --extend-ignore EXE` (the sandbox shows every file as executable, so the file-mode rules cannot pass here; CI runs them)
   - `uv run pytest`
5. **Commit.** Commit only when all four steps pass. One commit or a few focused ones. Each message is a short imperative sentence saying what the change does (for example `Show the model name in the status bar`), then a blank line, `Related to #{{ISSUE_NUMBER}}`, a blank line, and `Co-Authored-By: Claude <noreply@anthropic.com>`.

# Rules

- Work on Issue #{{ISSUE_NUMBER}} only.
- You have no GitHub access. Do not push, switch branches, rebase, or try to comment on or close the Issue: the runner does all of that after you finish.
- Do not edit `.sandcastle/`, `.github/` or `docs/agents/` unless the Issue asks for it.
- Do not add a dependency unless the Issue asks for it; if you must, `uv.lock` has to change with it.
- Never commit failing code, commented-out code or TODO comments. Never weaken or delete a test to make it pass.
- If you are blocked (the Issue is ambiguous, contradicts the code, or needs something you cannot do here), stop. Commit nothing broken, and report BLOCKED with the questions a person must answer.

# Done

Finish with your report, exactly once, as JSON inside `<report>` tags, then the completion signal:

<report>
{"status": "GREEN", "summary": "What you changed and why, in two to five sentences, naming the files and tests.", "questions": []}
</report>

- `status`: `GREEN` when you committed and all four Validation steps passed; `RED` when you committed but a step still fails; `BLOCKED` when you could not do the Task.
- `questions`: decisions you had to make that a reviewer should check, or, when BLOCKED, what a person must answer. Empty when there are none.

<promise>COMPLETE</promise>
