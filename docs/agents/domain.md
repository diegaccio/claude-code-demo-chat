# Domain docs

Where this project's domain language and decisions live, and how skills use them. `bdg:domain-design` follows the rules here over its defaults.

## Locations

- **Layout:** single context
- **Glossary:** `GLOSSARY.md` at the repository root
- **ADRs:** `docs/adr/`
- **Research notes:** not configured

Files that do not exist yet are created when the first term or decision settles, never as empty scaffolding.

## Use the glossary's vocabulary

When output names a domain concept (an Issue title, a refactor proposal, a hypothesis, a test name), use the glossary's term. Don't drift to the synonyms it lists under _Avoid_. A concept the glossary lacks is either invented language (reconsider it) or a real gap: note it for `bdg:domain-design`.

## Flag ADR conflicts

When output contradicts an ADR, say so explicitly instead of silently overriding it:

> _Contradicts ADR-0007 (event-sourced orders), but worth reopening because..._
