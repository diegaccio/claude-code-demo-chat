# Task workflow

The Task types, states and labels of this project. BDG skills name a **role** (such as "agent-ready"); this file maps it to the label string the Issue tracker uses. Edit the Label column to match the team's own vocabulary. Tier labels are not workflow labels: they live in the model routing configuration.

## Types

| Type | Label | Use for |
| ---- | ----- | ------- |
| blueprint | `blueprint` | A Blueprint: the decisions about a piece of work, parent of its Tasks. |
| bug | `bug` | Something broken. |
| feature | `feature` | New or changed behaviour. |
| technical | `technical` | Refactoring, tooling, dependencies: no visible behaviour change. |
| investigation | `investigation` | A question to answer before work can be planned. |

## Workflow roles

An open Task carries exactly one of these labels; a declined Task keeps the declined label when closed. Labels are plain on GitHub: remove the previous role label before adding the next.

| Role | Label | Meaning |
| ---- | ----- | ------- |
| untriaged | `needs-triage` | Nobody has evaluated it yet. |
| awaiting-info | `needs-info` | Waiting on the reporter for more information. |
| agent-ready | `ready-for-agent` | Fully specified: an agent can implement it unattended. |
| human-ready | `ready-for-human` | Needs a person to implement it. |
| declined | `wontfix` | Will not be done. |

## Pathfinder labels

Used by `bdg:pathfinder` to steer work too big for one session: one map Issue and one child Issue per open question or piece of work.

| Role | Label |
| ---- | ----- |
| map | `pathfinder:map` |
| research | `pathfinder:research` |
| prototype | `pathfinder:prototype` |
| dialogue | `pathfinder:dialogue` |
| task | `pathfinder:task` |

## Transitions

| From | To | When |
| ---- | -- | ---- |
| (new Issue from a person) | untriaged | On creation. |
| (new Task from a Blueprint breakdown) | agent-ready or human-ready | On creation: the breakdown already specified it. |
| untriaged | awaiting-info | Triage needs the reporter's answer. |
| awaiting-info | untriaged | The reporter answered. |
| untriaged | agent-ready or human-ready | Triage has fully specified it. |
| untriaged or awaiting-info | declined | It will not be done: comment the reason, then close. |
| agent-ready or human-ready | closed | Its change is merged into the target branch: comment what was done, then close. |

**Closing:** a Task is closed by the skill that finished it, after its change is merged; merging a pull request does not close it by itself. A Blueprint stays open until the team closes it.
