# Team map

Who covers what in this project, and how skills pick a person. Written by `bdg:team-map` from confirmed answers only; edit by hand at will, and re-running it keeps the edits. Real names and usernames live only here, never in a skill.

- **Systems:** Issue tracker and Code host are the same GitHub repository, so there is one username column
- **Stale after:** 180 days (a person whose Verified date is older is stale)

## People

One row per person. Every username was checked with the **verify username** operation of that system on the Verified date. `none` means the person has no account there.

| Person | GitHub username | Verified |
| ------ | --------------- | -------- |
| Diego Cattaneo | `diegaccio` | 2026-11-02 |

## Coverage

One row per person, area and role. An **area** is a domain (a glossary context or a business area) or a component (a module, service or folder of the code). A **role** is `domain-expert` (owns the problem, the terms, the business rules and their exceptions) or `software-engineer` (owns the code, its boundaries and its technical constraints). One person may hold both roles, and different roles in different areas. **Responsibility** is `primary` or `support`.

| Person | Area | Kind | Role | Responsibility |
| ------ | ---- | ---- | ---- | -------------- |
| Diego Cattaneo | `claude-code-demo-chat` (whole repository) | domain | domain-expert | primary |
| Diego Cattaneo | `claude-code-demo-chat` (whole repository) | component | software-engineer | primary |

## Assignment rules

A **choice** is one of: `assignee` (does the Task), `counterpart` (answers in a design dialogue), `reviewer` (reviews the pull request). Each choice is made on its own; one never implies another.

To make a choice for a piece of work:

1. Name its **areas** (the domains and components it touches) and its **required competence**: `domain-expert` for a business decision or question, `software-engineer` for code. Unclear areas or competence are a question for the user, not a guess.
2. If a row of the rules table below matches the choice, area and competence, its candidates are the people it names. Otherwise the candidates are the people with a Coverage row for that area and role, `primary` first: fall back to `support` only when no `primary` exists.
3. Drop people the rule excludes (for `reviewer`: the pull request's author).
4. Return exactly one outcome:
   - **match**: one candidate, not stale. Skills may act on it automatically.
   - **none**: no candidate. Flag it to the user.
   - **several**: more than one equivalent candidate. List them and let the user choose; never pick at random.
   - **stale**: a candidate's Verified date is older than **Stale after**, or the area is not in Coverage at all although the code or glossary has it. Flag it and suggest re-running `bdg:team-map`.

When work spans several areas, choose per area; if the areas give different people, that is **several**.

No overrides: every choice follows Coverage. With a single person, a `reviewer` choice always returns **none** and is flagged to the user.

| Choice | Area | Competence | Candidates | Notes |
| ------ | ---- | ---------- | ---------- | ----- |
