---
name: update-session-state
description: Refresh docs/SESSION-STATE.md from current repository state
disable-model-invocation: true
---

# Update Session State

Refresh `docs/SESSION-STATE.md` so a new session can resume without the previous
conversation history. This skill is **user-invoked only** (`/update-session-state`);
it must never run automatically.

## Guardrails

- **Only** edit `docs/SESSION-STATE.md`. Touch no other file.
- Do **not** edit `CLAUDE.md`.
- Do **not** edit `knowledge/DECISIONS-NEEDED.md`.
- Do **not** edit anything under `knowledge/` (the write-guard hook enforces this;
  do not attempt to disable it).
- Do **not** `git add`, `git commit`, or `git push`. Leave the file as an
  uncommitted working-tree change for the owner to review and commit.
- Never invent information. If a fact is not evidenced by the repo or git, write
  `UNKNOWN` or leave the prior text and flag it in your summary.
- Preserve the file's YAML front matter structure and section headings.

## Procedure

### 1. Read the current file

Read `docs/SESSION-STATE.md` in full. Note its section list and the existing
content of every section, especially the ones this skill must **not** rewrite.

### 2. Gather repository state

Run (read-only git commands only):

- `git status --porcelain=v1 --branch` — branch, ahead/behind, staged, unstaged,
  untracked files.
- `git log --oneline -10` — recent history.
- `git rev-parse HEAD` and `git log -1 --format='%H%n%s%n%cI'` — full hash,
  subject, commit date of the tip.
- `git log -1 --name-status HEAD` — files in the last commit.
- `git remote -v` — remote URL (confirm it still points at the private repo).
- `git rev-list --left-right --count origin/main...HEAD` (if `origin/main`
  exists) — divergence from the remote.

Then inspect the project to confirm what actually exists now:

- `docs/` — which specs/docs are present.
- Presence or absence of pipeline code (`config/`, package directories, any
  `*.py`, `pytest` config). "No pipeline code yet" vs "implementation started"
  is a key signal for **Current Phase** and **Next Action**.
- `knowledge/DECISIONS-NEEDED.md` — read (do not edit) to confirm which
  decisions are `DECIDED` / `DEFERRED` / `NEEDS_INPUT`, for the **Deferred** and
  **Open Issues** sections.
- `knowledge/inventories/*.yaml` — current asset counts and how many fields are
  still `NEEDS_INPUT` / `UNKNOWN`, for **Open Issues**.
- `.claude/` — hooks, agents, and skills now configured, if relevant to
  **Current Architecture** or **Completed**.

### 3. Update only these sections

Rewrite the following sections to match what you found. Keep the wording style
of the existing file (concise, evidence-based, `UNKNOWN`/`NEEDS_INPUT` where
appropriate):

- **Current Phase**
- **Completed**
- **Current Architecture**
- **Last Completed Step**
- **Last Commit**
- **Current Repository State**
- **Next Action**
- **Open Issues**
- **Deferred**

Update the `updated:` field in the YAML front matter to today's date.

### 4. Preserve everything else

Do not alter:

- Any section not listed in step 3 (e.g. **Important Decisions**, **Current
  Assets** narrative that is still accurate, **How To Resume**), unless a
  listed change makes a cross-reference factually wrong — in which case fix only
  the wrong reference and note it in your summary.
- The decision history and rationale text carried from `DECISIONS-NEEDED.md`.
- The front-matter keys other than `updated:`.

If **Current Assets** counts are contradicted by the inventories, do not silently
rewrite that section — report the discrepancy in your closing summary and let the
owner decide (inventory edits need explicit authorisation).

### 5. Report back

After writing the file, output:

- A diff-style summary of what changed, section by section.
- Any discrepancy you found but did **not** fix (asset counts, stale decision
  references, drift already logged).
- Confirmation that only `docs/SESSION-STATE.md` was modified and nothing was
  committed. End with the current `git status --short` output.
