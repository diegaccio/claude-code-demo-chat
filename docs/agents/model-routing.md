# Model routing

Which model each BDG subagent runs on in this project (ADR-0003). Six slots: three Tiers and three fixed roles. Edit the Model and Fits columns to suit the team; re-running bootstrap keeps the edits.

A skill that spawns a subagent looks its slot up here and passes the Model cell verbatim as the subagent's `model`, on every spawn. When this file is missing, or a slot's model is one the runtime does not accept, the skill stops and asks the user to re-run bootstrap: it never falls back to another model.

**Models** are the aliases the runtime's subagent `model` parameter accepts, such as `haiku`, `sonnet` and `opus`. Full model identifiers and version numbers are not accepted.

## Tiers

A Tier rates how much judgement a Task demands, not how much typing. The BDG package fixes the Tier names, how a Task's Tier is chosen from the Fits text below, and escalation. This table sets each Tier's label, model and Fits text.

The Label is the Issue tracker label that carries a Task's Tier, and it is authoritative: a person re-tiers a Task by swapping it. Tier labels are not workflow labels: the workflow roles and their labels live in `docs/agents/task-workflow.md`. Labels are plain on GitHub: remove the previous Tier label before adding the new one.

Replace the Fits text with examples from this project's own code: the generic text below is a starting point.

| Tier | Label | Model | Fits |
| ---- | ----- | ----- | ---- |
| light | `tier::light` | `haiku` | Mechanical, fully specified edits that copy an existing pattern and that the build, the lint or the existing tests fully check: registering a file, adding an entry that mirrors its neighbours, a rename with a small blast radius. No logic decision is left open. |
| standard | `tier::standard` | `sonnet` | The default. Logic inside one area that already has a pattern and tests to follow: a new endpoint, page or command like the existing ones, a field on a model whose tests exist, a validation rule. |
| deep | `tier::deep` | `opus` | Design left open by the Task, or code where a wrong guess fails silently: a new abstraction or its first test suite, data joined across modules or stores, concurrency, memory or transactions, a refactor that chooses a shape. |

## Fixed roles

| Role | Model | Runs |
| ---- | ----- | ---- |
| exploration | `sonnet` | Reads the codebase before a breakdown or an orchestrated run and writes notes for the implementers. |
| merger | `sonnet` | Merges each finished Task branch into the integration branch and validates the result. |
| review | `opus` | The reviewers that review the changes, whichever skill asks for the review. |
