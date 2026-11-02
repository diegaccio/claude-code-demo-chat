// AFK runner: works through `ready-for-agent` Issues one at a time in a Docker
// sandbox and ends each one as a draft pull request, or hands it to a person.
//
// The agents inside the sandbox only write code and commit on their branch:
// they get no GitHub token. Everything that touches GitHub (choosing the
// Issue, pushing, the pull request, comments, labels) runs here on the host
// with your own `gh` login, following docs/agents/issue-tracker.md and
// docs/agents/submission.md. Nothing here marks a pull request ready, merges,
// chooses reviewers or closes an Issue.
//
// Usage:
//   npm run sandcastle             # up to MAX_ISSUES agent-ready Issues
//   npm run sandcastle -- 17       # only Issue #17

import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { claudeCode, createSandbox } from "@ai-hero/sandcastle";
import { docker } from "@ai-hero/sandcastle/sandboxes/docker";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const BASE_BRANCH = "main";
const AGENT_READY_LABEL = "ready-for-agent";
const HUMAN_READY_LABEL = "ready-for-human";

// Issues per run when no Issue number is given. Kept low so an unattended run
// cannot burn through the backlog before anyone has looked at the results.
const MAX_ISSUES = Number(process.env.SANDCASTLE_MAX_ISSUES ?? 3);

// Tier label -> implementer model, from docs/agents/model-routing.md.
// An Issue without a Tier label is `standard`, the routing default.
const TIER_MODELS: Record<string, string> = {
  "tier::light": "claude-haiku-5-5",
  "tier::standard": "claude-sonnet-5-5",
  "tier::deep": "claude-opus-5-5",
};
const DEFAULT_MODEL = TIER_MODELS["tier::standard"];
// The `review` fixed role of docs/agents/model-routing.md.
const REVIEW_MODEL = "claude-opus-5-5";

// An agent that prints nothing for this long is stuck; the test suite and
// pyright can stay quiet for a while, so allow more than Sandcastle's 600s.
const IDLE_TIMEOUT_SECONDS = 900;

// The worktree is checked out on the Windows host, where core.autocrlf gives
// it CRLF files, but the container's git does not see that setting: without
// this, agent commits would store CRLF line endings.
const SANDBOX_GIT_ENV = {
  GIT_CONFIG_COUNT: "1",
  GIT_CONFIG_KEY_0: "core.autocrlf",
  GIT_CONFIG_VALUE_0: "input",
};

// The Validation steps of docs/agents/validation.md, run by this script after
// the agents finish: the pull request is opened only when all of them pass.
// Docker Desktop shows the Windows worktree as mode 777, so ruff's file-mode
// rules (EXE) flag every file there; CI still runs them on a real checkout.
const VALIDATION_STEPS = [
  { name: "prepare", command: "uv sync --locked" },
  { name: "build", command: "uv run pyright" },
  { name: "lint", command: "uv run ruff check --extend-ignore EXE" },
  { name: "test", command: "uv run pytest" },
] as const;

// ---------------------------------------------------------------------------
// Host helpers
// ---------------------------------------------------------------------------

function sh(command: string, args: string[]): string {
  return execFileSync(command, args, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
}

function gh(...args: string[]): string {
  return sh("gh", args);
}

function git(...args: string[]): string {
  return sh("git", args);
}

function bodyFile(text: string): string {
  const path = join(mkdtempSync(join(tmpdir(), "sandcastle-")), "body.md");
  writeFileSync(path, text);
  return path;
}

function slugify(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 40)
    .replace(/-$/, "");
}

// ---------------------------------------------------------------------------
// Issues
// ---------------------------------------------------------------------------

interface Issue {
  number: number;
  title: string;
  body: string;
  labels: { name: string }[];
  comments: { author: { login: string }; body: string }[];
}

function readIssue(number: number): Issue {
  return JSON.parse(gh("issue", "view", String(number), "--json", "number,title,body,labels,comments"));
}

function openBlockers(number: number): number[] {
  return JSON.parse(
    gh(
      "api",
      `repos/{owner}/{repo}/issues/${number}/dependencies/blocked_by`,
      "--jq",
      "[.[] | select(.state == \"open\") | .number]",
    ),
  );
}

// Issue numbers that already have an open pull request from an agent branch.
function issuesWithOpenAgentPullRequest(): Set<number> {
  const heads: { headRefName: string }[] = JSON.parse(
    gh("pr", "list", "--state", "open", "--limit", "1000", "--json", "headRefName"),
  );
  const numbers = heads
    .map((pr) => /^agent\/(\d+)-/.exec(pr.headRefName)?.[1])
    .filter((n): n is string => n !== undefined)
    .map(Number);
  return new Set(numbers);
}

function pickIssues(): number[] {
  const listed: { number: number }[] = JSON.parse(
    gh("issue", "list", "--label", AGENT_READY_LABEL, "--state", "open", "--limit", "1000", "--json", "number"),
  );
  const taken = issuesWithOpenAgentPullRequest();
  const picked: number[] = [];
  for (const { number } of listed.sort((a, b) => a.number - b.number)) {
    if (picked.length >= MAX_ISSUES) break;
    if (taken.has(number)) {
      console.log(`#${number}: skipped, an agent pull request is already open`);
      continue;
    }
    const blockers = openBlockers(number);
    if (blockers.length > 0) {
      console.log(`#${number}: skipped, blocked by ${blockers.map((b) => `#${b}`).join(", ")}`);
      continue;
    }
    picked.push(number);
  }
  return picked;
}

function issueContext(issue: Issue): string {
  const comments = issue.comments.map((c) => `### Comment by ${c.author.login}\n\n${c.body}`).join("\n\n");
  return `${issue.body || "(no description)"}${comments ? `\n\n## Comments\n\n${comments}` : ""}`;
}

function modelFor(issue: Issue): string {
  const tier = issue.labels.map((l) => l.name).find((name) => name in TIER_MODELS);
  return tier ? TIER_MODELS[tier] : DEFAULT_MODEL;
}

// ---------------------------------------------------------------------------
// Agent reports
// ---------------------------------------------------------------------------

interface Report {
  status: "GREEN" | "RED" | "BLOCKED";
  summary: string;
  questions: string[];
}

// The prompts ask for one <report> JSON block; the last one printed wins.
function parseReport(stdout: string): Report | undefined {
  const matches = [...stdout.matchAll(/<report>([\s\S]*?)<\/report>/g)];
  const raw = matches.at(-1)?.[1];
  if (raw === undefined) return undefined;
  try {
    const parsed = JSON.parse(raw);
    if (!["GREEN", "RED", "BLOCKED"].includes(parsed.status)) return undefined;
    return {
      status: parsed.status,
      summary: String(parsed.summary ?? ""),
      questions: Array.isArray(parsed.questions) ? parsed.questions.map(String) : [],
    };
  } catch {
    return undefined;
  }
}

function formatReport(heading: string, report: Report | undefined): string {
  if (!report) return `### ${heading}\n\nThe agent printed no valid report.`;
  const questions = report.questions.length
    ? `\n\n**Open questions**\n\n${report.questions.map((q) => `- ${q}`).join("\n")}`
    : "";
  return `### ${heading}: ${report.status}\n\n${report.summary}${questions}`;
}

// ---------------------------------------------------------------------------
// One Issue
// ---------------------------------------------------------------------------

interface StepResult {
  name: string;
  passed: boolean;
  tail: string;
}

type Outcome = { kind: "pull-request"; url: string } | { kind: "handed-over"; reason: string };

async function work(number: number): Promise<Outcome> {
  const issue = readIssue(number);
  const branch = `agent/${number}-${slugify(issue.title)}`;
  const model = modelFor(issue);
  console.log(`\n=== #${number} ${issue.title} (${model}) on ${branch} ===\n`);

  const promptArgs = {
    ISSUE_NUMBER: String(number),
    ISSUE_TITLE: issue.title,
    ISSUE_CONTEXT: issueContext(issue),
    BASE_BRANCH,
  };
  const logDir = ".sandcastle/logs";

  const sandbox = await createSandbox({
    branch,
    baseBranch: BASE_BRANCH,
    sandbox: docker({ env: SANDBOX_GIT_ENV }),
    hooks: { sandbox: { onSandboxReady: [{ command: "uv sync --locked" }] } },
  });

  let implement: Report | undefined;
  let review: Report | undefined;
  let commits = 0;
  const validation: StepResult[] = [];
  let preservedWorktreePath: string | undefined;

  try {
    const implemented = await sandbox.run({
      name: `implement-${number}`,
      agent: claudeCode(model),
      promptFile: ".sandcastle/implement-prompt.md",
      promptArgs,
      idleTimeoutSeconds: IDLE_TIMEOUT_SECONDS,
      logging: { type: "file", path: `${logDir}/${number}-implement.log`, verbose: true },
    });
    implement = parseReport(implemented.stdout);
    commits += implemented.commits.length;

    if (commits > 0 && implement?.status !== "BLOCKED") {
      const reviewed = await sandbox.run({
        name: `review-${number}`,
        agent: claudeCode(REVIEW_MODEL),
        promptFile: ".sandcastle/review-prompt.md",
        promptArgs,
        idleTimeoutSeconds: IDLE_TIMEOUT_SECONDS,
        logging: { type: "file", path: `${logDir}/${number}-review.log`, verbose: true },
      });
      review = parseReport(reviewed.stdout);
      commits += reviewed.commits.length;

      for (const step of VALIDATION_STEPS) {
        const result = await sandbox.exec(step.command);
        const tail = `${result.stdout}\n${result.stderr}`.trim().split("\n").slice(-30).join("\n");
        validation.push({ name: step.name, passed: result.exitCode === 0, tail });
        if (result.exitCode !== 0) break;
      }
    }
  } finally {
    preservedWorktreePath = (await sandbox.close()).preservedWorktreePath;
  }

  const green =
    commits > 0 &&
    implement?.status !== "BLOCKED" &&
    validation.length === VALIDATION_STEPS.length &&
    validation.every((s) => s.passed) &&
    preservedWorktreePath === undefined;

  const validationText = validation.length
    ? validation
        .map((s) => `- **${s.name}:** ${s.passed ? "passed" : `failed\n\n\`\`\`\n${s.tail}\n\`\`\``}`)
        .join("\n")
    : "- Not run: the implementer made no commits or reported BLOCKED.";
  const leftovers = preservedWorktreePath
    ? `\n\nThe agents left uncommitted changes, kept on the runner's machine at \`${preservedWorktreePath}\`.`
    : "";
  const reports = `${formatReport("Implementer", implement)}\n\n${formatReport("Reviewer", review)}`;

  if (green) {
    git("push", "-u", "origin", branch);
    const body = [
      `Related to #${number}`,
      "",
      "## What the agents did",
      "",
      reports,
      "",
      "## Validation",
      "",
      `The Validation steps of \`docs/agents/validation.md\` passed in the sandbox on \`${BASE_BRANCH}\` plus this branch:`,
      "",
      validationText,
      "",
      `Implemented by \`${model}\`, reviewed by \`${REVIEW_MODEL}\`, unattended through Sandcastle (\`.sandcastle/main.mts\`). A person marks this ready once the \`Validation\` workflow is green and chooses the reviewer.`,
      "",
      "🤖 Generated with [Claude Code](https://claude.com/claude-code)",
    ].join("\n");
    const url = gh(
      "pr", "create", "--draft",
      "--base", BASE_BRANCH,
      "--head", branch,
      "--title", `#${number} ${issue.title}`,
      "--body-file", bodyFile(body),
    );
    gh("issue", "comment", String(number), "--body", `An agent opened a draft pull request for this Task: ${url}`);
    return { kind: "pull-request", url };
  }

  const reason = commits === 0 ? "no commits" : implement?.status === "BLOCKED" ? "blocked" : "not green";
  const comment = [
    `An unattended agent run could not finish this Task (${reason}), so it now needs a person.`,
    "",
    reports,
    "",
    "### Validation",
    "",
    validationText,
    "",
    `The branch \`${branch}\` was not pushed; it stays on the runner's machine.${leftovers}`,
  ].join("\n");
  gh("issue", "comment", String(number), "--body-file", bodyFile(comment));
  gh("issue", "edit", String(number), "--remove-label", AGENT_READY_LABEL);
  gh("issue", "edit", String(number), "--add-label", HUMAN_READY_LABEL);
  return { kind: "handed-over", reason };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function checkBaseIsCurrent(): void {
  git("fetch", "origin", BASE_BRANCH);
  const local = git("rev-parse", BASE_BRANCH);
  const remote = git("rev-parse", `origin/${BASE_BRANCH}`);
  if (local !== remote) {
    throw new Error(
      `Local ${BASE_BRANCH} (${local.slice(0, 7)}) differs from origin/${BASE_BRANCH} (${remote.slice(0, 7)}). ` +
        `Update it first, so the agents start from what is merged.`,
    );
  }
}

gh("auth", "status");
checkBaseIsCurrent();

const requested = process.argv[2];
const issues = requested ? [Number(requested.replace(/^#/, ""))] : pickIssues();
if (issues.length === 0) console.log(`No unblocked ${AGENT_READY_LABEL} Issues. Nothing to do.`);

const outcomes: string[] = [];
for (const number of issues) {
  try {
    const outcome = await work(number);
    outcomes.push(
      outcome.kind === "pull-request"
        ? `#${number}: draft pull request ${outcome.url}`
        : `#${number}: handed to a person (${outcome.reason})`,
    );
  } catch (error) {
    // Left for the person running this: the Issue keeps its label and gets no comment.
    console.error(error);
    outcomes.push(`#${number}: runner error, see above; the Issue was not changed`);
  }
}

console.log(`\n=== Summary ===\n${outcomes.join("\n")}`);
