# Validation

The Validation steps of this project: the commands that decide whether a change is green. Written by `bdg:validation-setup`; edit them by hand or re-run it, and re-run it after any edit so the verified commit stays true.

## Steps

Run from the repository root, in this order, stopping at the first that fails. A change is green when every step exits 0. A step marked `none` is skipped.

None of the steps needs a model server: they pass with neither Ollama nor SRH reachable.

| Step | Command | What it does |
| ---- | ------- | ------------ |
| prepare | `uv sync --locked` | Installs the locked dependencies, dev tools included, into `.venv`; fails if `uv.lock` is out of date with `pyproject.toml`. Safe to repeat. |
| build | `uv run pyright` | Type-checks `src` and `tests` in pyright's `standard` mode (Python has no compile step). |
| lint | `uv run ruff check` | Lints with ruff's default rules plus import sorting. |
| test | `uv run pytest` | Runs the tests in `tests/`, async tests included. |

- **Base ref:** not used

## Verification

- **Status:** verified
- **Verified at:** `eb4f317687cf89b0b2808e96eb9ae4666755a42f`
- **Last run:** 2026-11-02, clean checkout: prepare passed, build passed (0 errors), lint passed, test passed (1 test)
