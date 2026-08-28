#!/usr/bin/env bash
# guard-knowledge.sh — Claude Code PreToolUse hook
#
# knowledge/ is human-owned source of truth:
#   - Technical Spec V1 §17: "The pipeline reads knowledge/ and writes only
#     data/<run_id>/, reports/<run_id>/, and appends
#     knowledge/market/opportunity-registry.yaml."
#   - SESSION-STATE.md "How To Resume" #3: do not modify CLAUDE.md,
#     DECISIONS-NEEDED.md, business-dna/*, cluster-taxonomy.md, guardrails.yaml
#     or inventories/* without an explicit per-task instruction from the owner.
#
# This hook blocks Edit / Write / MultiEdit / NotebookEdit on any path under
# knowledge/ EXCEPT knowledge/market/opportunity-registry.yaml, which the
# Technical Spec explicitly authorises tooling to append (append-only, §17).
#
# Contract: tool call arrives as JSON on stdin.
#   exit 0 -> allow the tool call
#   exit 2 -> block the tool call; stderr is shown to Claude
#
# Fail-closed: if the write target cannot be determined, the call is blocked.

set -u

project_dir="${CLAUDE_PROJECT_DIR:-$PWD}"

if ! command -v jq >/dev/null 2>&1; then
  echo "guard-knowledge: 'jq' is not available, so the write target cannot be inspected." >&2
  echo "Blocking to fail safe. Install jq or fix .claude/hooks/guard-knowledge.sh." >&2
  exit 2
fi

input="$(cat)"

# Edit / Write / MultiEdit -> .tool_input.file_path ; NotebookEdit -> .tool_input.notebook_path
path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')"

# No path-shaped field in the payload -> not this hook's concern.
if [ -z "$path" ]; then
  exit 0
fi

# Normalise an absolute path under the project root to a repo-relative path.
rel="$path"
case "$path" in
  "$project_dir"/*) rel="${path#"$project_dir"/}" ;;
esac
rel="${rel#./}"

# Explicitly authorised exception: the append-only operational registry (Spec V1 §17).
case "$rel" in
  knowledge/market/opportunity-registry.yaml|*/knowledge/market/opportunity-registry.yaml)
    exit 0
    ;;
esac

# Everything else under knowledge/ is protected.
case "$rel" in
  knowledge/*|*/knowledge/*)
    {
      echo "BLOCKED — '$rel' is human-owned source of truth."
      echo
      echo "Technical Spec V1 §17: the pipeline reads knowledge/ and must not write it,"
      echo "except appending knowledge/market/opportunity-registry.yaml."
      echo "SESSION-STATE.md 'How To Resume' #3: CLAUDE.md, DECISIONS-NEEDED.md,"
      echo "business-dna/*, cluster-taxonomy.md, guardrails.yaml and inventories/* must not"
      echo "be modified without an explicit per-task instruction from the owner."
      echo
      echo "If the owner authorised this specific edit: make the change manually, or"
      echo "temporarily disable this hook for that task."
    } >&2
    exit 2
    ;;
esac

exit 0
