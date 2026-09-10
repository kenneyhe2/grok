#!/usr/bin/env bash
# Mirror all kenneyhe-zingbox GitHub repositories into the kenney-he Cursor codebase.
#
# Prerequisites:
#   - Origin CLI installed (https://cursor.com/docs/origin/cli)
#   - origin auth login (or CURSOR_API_KEY / CURSOR_AUTH_TOKEN set)
#   - Cursor GitHub app connected to kenneyhe-zingbox
#   - GitHub admin access on each source repository
#
# Usage:
#   ./scripts/sync-kenney-he-codebase.sh            # mirror all 23 repos
#   ./scripts/sync-kenney-he-codebase.sh --dry-run # print commands only
#   ./scripts/sync-kenney-he-codebase.sh --active # skip archived repos

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="${ROOT_DIR}/codebase/kenney-he/repos.json"
CODEBASE_NAMESPACE="kenney-he"
ORIGIN_BIN="${ORIGIN_BIN:-origin}"

if [[ ! -f "${MANIFEST}" ]]; then
  echo "Manifest not found: ${MANIFEST}" >&2
  exit 1
fi

if ! command -v "${ORIGIN_BIN}" >/dev/null 2>&1; then
  if [[ -x /exec-daemon/tools/origin ]]; then
    ORIGIN_BIN=/exec-daemon/tools/origin
  else
    echo "Origin CLI not found. Install it or set ORIGIN_BIN." >&2
    exit 1
  fi
fi

DRY_RUN=false
ACTIVE_ONLY=false
for arg in "$@"; do
  case "${arg}" in
    --dry-run) DRY_RUN=true ;;
    --active) ACTIVE_ONLY=true ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: ${arg}" >&2
      exit 1
      ;;
  esac
done

if [[ "${DRY_RUN}" == false ]]; then
  if ! "${ORIGIN_BIN}" auth status >/dev/null 2>&1; then
    echo "Not authenticated. Run: ${ORIGIN_BIN} auth login" >&2
    exit 1
  fi
fi

mapfile -t REPOS < <(
  python3 - "${MANIFEST}" "${ACTIVE_ONLY}" <<'PY'
import json
import sys

manifest_path = sys.argv[1]
active_only = sys.argv[2] == "true"

with open(manifest_path, encoding="utf-8") as handle:
    data = json.load(handle)

for repo in data["repositories"]:
    if active_only and repo.get("archived"):
        continue
    print(repo["github"])
PY
)

if [[ "${#REPOS[@]}" -eq 0 ]]; then
  echo "No repositories selected from ${MANIFEST}" >&2
  exit 1
fi

echo "Syncing ${#REPOS[@]} repositories into ${CODEBASE_NAMESPACE}..."

succeeded=0
failed=0
skipped=0

for github_repo in "${REPOS[@]}"; do
  repo_name="${github_repo#*/}"
  origin_repo="${CODEBASE_NAMESPACE}/${repo_name}"

  if [[ "${DRY_RUN}" == true ]]; then
    echo "DRY RUN: ${ORIGIN_BIN} repo create-mirrored ${github_repo} --namespace ${CODEBASE_NAMESPACE}"
    continue
  fi

  if "${ORIGIN_BIN}" repo view "${origin_repo}" >/dev/null 2>&1; then
    echo "SKIP  ${origin_repo} (already exists)"
    skipped=$((skipped + 1))
    continue
  fi

  echo "SYNC  ${github_repo} -> ${origin_repo}"
  if "${ORIGIN_BIN}" repo create-mirrored "${github_repo}" --namespace "${CODEBASE_NAMESPACE}"; then
    succeeded=$((succeeded + 1))
  else
    echo "FAIL  ${github_repo}" >&2
    failed=$((failed + 1))
  fi
done

if [[ "${DRY_RUN}" == true ]]; then
  exit 0
fi

echo ""
echo "Done. created=${succeeded} skipped=${skipped} failed=${failed}"
if [[ "${failed}" -gt 0 ]]; then
  exit 1
fi
