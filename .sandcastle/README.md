# AFK runner

Works through `ready-for-agent` Issues unattended with [Sandcastle](https://github.com/mattpocock/sandcastle), one at a time, each in its own Docker container on its own branch `agent/<id>-<slug>`.

For each Issue, `main.mts`:

1. Picks the oldest open `ready-for-agent` Issue with no open blocker and no open agent pull request, or the one you name.
2. Runs an implementer (model from the Issue's Tier label, see `docs/agents/model-routing.md`) with `implement-prompt.md`, then an Opus reviewer with `review-prompt.md`, both in the same container.
3. Runs the Validation steps itself inside the container.
4. When they pass, pushes the branch, opens a **draft** pull request `#<id> <title>` and comments its link on the Issue. Otherwise comments both reports on the Issue and moves it to `ready-for-human`, keeping the branch local.

The agents get no GitHub token: all GitHub work runs on the host with your `gh` login. The runner never marks a pull request ready, merges, chooses reviewers or closes an Issue.

## Setup, once

1. Docker Desktop running; `gh auth status` logged in to github.com.
2. `npm ci`
3. `npm run sandcastle:build-image` (again after every change to `Dockerfile`)
4. Copy `.env.example` to `.env` here and set `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token`.

## Run

Local `main` must match `origin/main`: the agents start from it.

```bash
npm run sandcastle          # up to 3 Issues; SANDCASTLE_MAX_ISSUES changes the cap
npm run sandcastle -- 17    # only Issue #17
```

## Checking a run

- Live and afterwards: `logs/<id>-implement.log` and `logs/<id>-review.log` (verbose: every line the agent printed).
- The draft pull request holds both agents' reports and the Validation result; CI runs the `Validation` workflow on it.
- An Issue that came back to `ready-for-human` has the reports in its comments; its branch stays local for inspection.

After editing `main.mts`, run `npm run sandcastle:typecheck`.
