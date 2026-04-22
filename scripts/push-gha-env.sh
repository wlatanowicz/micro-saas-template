#!/usr/bin/env bash
# Push an env file to GitHub Actions secrets and variables using the GitHub CLI (gh).
#
# Convention (same as .env.gha from collect-gha-env.sh):
#   Lines under '# --- Secrets ---' → Actions *secrets*.
#   Lines under '# --- Variables ---' → *variables*.
#   Assignment lines before the first section header are ignored (with a message).
# All non-empty assignments in each section are uploaded (no hardcoded name list).
#
# Requires: gh auth login with repo scope; run from the repo root (or pass -R).
#
# Usage: ./scripts/push-gha-env.sh [-f path] [-y] [-n] [-e ENV_NAME] [-R owner/repo]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env.gha"
DRY_RUN=false
ASSUME_YES=false
GH_ENV=""
GH_REPO=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -f | --file)
      ENV_FILE="${2:?}"
      shift 2
      ;;
    -y | --yes)
      ASSUME_YES=true
      shift
      ;;
    -n | --dry-run)
      DRY_RUN=true
      shift
      ;;
    -e | --env)
      GH_ENV="${2:?}"
      shift 2
      ;;
    -R | --repo)
      GH_REPO="${2:?}"
      shift 2
      ;;
    -h | --help)
      cat <<'EOF'
Usage: ./scripts/push-gha-env.sh [options]

  Upload an env file to GitHub Actions secrets and variables (gh CLI).

  Use section headers exactly like collect-gha-env.sh:
    # --- Secrets ---
    KEY=value
    # --- Variables ---
    KEY=value

  Every non-empty assignment under each section is uploaded.

Options:
  -f, --file PATH   Env file (default: .env.gha at repo root)
  -y, --yes         Skip confirmation
  -n, --dry-run     Show what would be set (no gh writes)
  -e, --env NAME    GitHub Actions environment (scoped secrets + variables)
  -R, --repo REPO   owner/repo (default: current repo)
  -h, --help

Requires: gh, python3 — run from clone with gh auth (repo scope).
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

command -v gh >/dev/null || {
  echo "Install GitHub CLI: https://cli.github.com/  (command: gh)" >&2
  exit 1
}
command -v python3 >/dev/null || {
  echo "Missing python3" >&2
  exit 1
}

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file not found: ${ENV_FILE}" >&2
  echo "Generate one with: ./scripts/collect-gha-env.sh" >&2
  exit 1
fi

PUSH_GHA_DRY_RUN=0
PUSH_GHA_YES=0
$DRY_RUN && PUSH_GHA_DRY_RUN=1
$ASSUME_YES && PUSH_GHA_YES=1
export PUSH_GHA_DRY_RUN PUSH_GHA_YES PUSH_GHA_GH_ENV="$GH_ENV" PUSH_GHA_GH_REPO="$GH_REPO"

python3 - "$ENV_FILE" <<'PY'
import os
import pathlib
import re
import shlex
import subprocess
import sys

path = pathlib.Path(sys.argv[1])
dry = os.environ.get("PUSH_GHA_DRY_RUN", "0") == "1"
assume_yes = os.environ.get("PUSH_GHA_YES", "0") == "1"
gh_env = os.environ.get("PUSH_GHA_GH_ENV", "").strip()
gh_repo = os.environ.get("PUSH_GHA_GH_REPO", "").strip()

key_ok = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
name_ok = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

SECRET_HDR = re.compile(r"^#\s*---\s*Secrets\s*---\s*$", re.IGNORECASE)
VAR_HDR = re.compile(r"^#\s*---\s*Variables\s*---\s*$", re.IGNORECASE)

# Preserve insertion order; last assignment wins per key within that section.
secrets = {}
variables = {}
section = None

for raw in path.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line:
        continue
    if line.startswith("#"):
        if SECRET_HDR.match(line):
            section = "secret"
        elif VAR_HDR.match(line):
            section = "variable"
        continue
    if "=" not in line:
        continue
    k, _, v = line.partition("=")
    k = k.strip()
    if not key_ok.match(k):
        print(f"Skipping invalid key: {k!r}", file=sys.stderr)
        continue
    try:
        parts = shlex.split(v.strip(), posix=True) if v.strip() else []
        val = parts[0] if parts else ""
    except ValueError:
        val = ""
    if not val:
        print(f"Skipping empty value: {k}", file=sys.stderr)
        continue
    if not name_ok.match(k):
        print(f"Skipping invalid name: {k!r}", file=sys.stderr)
        continue

    if section == "secret":
        secrets[k] = val
    elif section == "variable":
        variables[k] = val
    else:
        print(f"Ignoring (before # --- Secrets --- or # --- Variables ---): {k}", file=sys.stderr)

if not secrets and not variables:
    print("Nothing to upload (no non-empty entries under a section).", file=sys.stderr)
    print("Expected headers: # --- Secrets ---  and  # --- Variables ---", file=sys.stderr)
    sys.exit(1)

nsec, nvar = len(secrets), len(variables)
target = gh_repo or "this repository"
if gh_env:
    target = f"{target} (environment: {gh_env})"

if not dry and not assume_yes:
    print(f"Will set {nsec} secret(s) and {nvar} variable(s) on {target}.", file=sys.stderr)
    try:
        ans = input("Continue? [y/N] ").strip().lower()
    except EOFError:
        ans = ""
    if ans not in ("y", "yes"):
        print("Aborted.", file=sys.stderr)
        sys.exit(1)


def gh_base():
    cmd = ["gh"]
    if gh_repo:
        cmd.extend(["-R", gh_repo])
    return cmd


def run_set(kind, name, value):
    cmd = gh_base()
    cmd.extend(["secret" if kind == "secret" else "variable", "set", name])
    if gh_env:
        cmd.extend(["--env", gh_env])
    if dry:
        print(f"[dry-run] {' '.join(cmd)} ({len(value)} bytes)", file=sys.stderr)
        return
    subprocess.run(cmd, input=value.encode("utf-8"), check=True)


for name, val in secrets.items():
    run_set("secret", name, val)
for name, val in variables.items():
    run_set("variable", name, val)

if dry:
    print(f"Dry-run finished ({nsec} secrets, {nvar} variables).", file=sys.stderr)
else:
    print(f"Done ({nsec} secrets, {nvar} variables).", file=sys.stderr)
PY
