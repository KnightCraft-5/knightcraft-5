#!/usr/bin/env bash
# Run everything CI runs, locally, before tagging a release.
#
# WHY THIS EXISTS
# A release was tagged against a tree whose quest book did not validate. The
# check had been run by hand several times, but always piped:
#
#     python3 tools/validate_quests.py 2>&1 | tail -2
#
# `$?` after a pipeline is the exit status of the LAST command, so that reports
# tail's status - always 0. The validator prints its problem list to stderr and
# exits 1, and both were swallowed. Every run looked clean while the tree was
# broken, and it only surfaced when GitHub Actions ran the same command bare.
#
# So: never pipe a check whose exit code you care about. This script runs each
# one bare, captures stderr, and reports a real pass/fail per step.
#
# Usage:
#   ./preflight.sh            # structural checks only (no mods/, no network)
#   ./preflight.sh --full     # also verify mods/ against the tracked manifest
set -uo pipefail
cd "$(dirname "$0")" || exit 1

FULL=0
[ "${1:-}" = "--full" ] && FULL=1

fails=0
err="$(mktemp)"
trap 'rm -f "$err"' EXIT

step() {
    local name="$1"; shift
    if "$@" >/dev/null 2>"$err"; then
        printf '  \033[32mPASS\033[0m  %s\n' "$name"
    else
        printf '  \033[31mFAIL\033[0m  %s\n' "$name"
        sed 's/^/          /' "$err" | head -20
        fails=$((fails + 1))
    fi
}

echo "structural"
step "quest book"        python3 tools/validate_quests.py
step "server config keys" python3 tools/validate_configs.py
step "translations"      python3 tools/validate_lang.py
step "hardcore lives on" grep -q '"AUTO_HARDCORE": true' config/hqm/config.json5

# The credential check inverts: finding a match is the failure.
if git ls-files | grep -qE '(^|/)(\.sl_password|r2\.env|\.env|simpleauth_users\.json)$'; then
    printf '  \033[31mFAIL\033[0m  no credentials tracked\n'; fails=$((fails + 1))
else
    printf '  \033[32mPASS\033[0m  no credentials tracked\n'
fi

# Do NOT quietly skip this. The first version skipped when shellcheck was absent,
# so a local run went green while CI - which installs it - failed on SC2164. A
# check that silently does nothing is worse than no check. On NixOS shellcheck is
# one `nix run` away, so reach for it before giving up.
if command -v shellcheck >/dev/null 2>&1; then
    step "shell scripts" shellcheck -S warning build-*.sh sync-mods.sh upload-bundles.sh preflight.sh
elif command -v nix >/dev/null 2>&1; then
    step "shell scripts (via nix)" nix run nixpkgs#shellcheck -- \
        -S warning build-*.sh sync-mods.sh upload-bundles.sh preflight.sh
else
    printf '  \033[31mFAIL\033[0m  shell scripts - shellcheck unavailable and no nix to fetch it.\n'
    printf '          CI *will* run it, so this machine cannot clear a release.\n'
    fails=$((fails + 1))
fi

if [ "$FULL" = 1 ]; then
    echo "artifacts"
    step "mods match manifest" ./sync-mods.sh --verify
fi

echo
if [ "$fails" -eq 0 ]; then
    echo "all green - safe to tag"
    exit 0
fi
echo "$fails check(s) failed - do NOT tag"
exit 1
