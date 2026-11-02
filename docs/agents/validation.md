# Validation

The Validation steps of this project: the commands that decide whether a change is green. Written by `bdg:validation-setup`; edit them by hand or re-run it, and re-run it after any edit so the verified commit stays true.

## Steps

Run from the repository root, in this order, stopping at the first that fails. A change is green when every step exits 0. A step marked `none` is skipped.

The stack is not chosen yet, so no step has tooling. Re-run `bdg:validation-setup` once it is: until then validation is missing and code Tasks are refused.

| Step | Command | What it does |
| ---- | ------- | ------------ |
| prepare | not configured | |
| build | not configured | |
| lint | not configured | |
| test | not configured | |

- **Base ref:** not used

## Verification

- **Status:** unverified
- **Verified at:** none
- **Last run:** none: no steps defined (2026-11-02)
