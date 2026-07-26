#!/usr/bin/env bash
# Builds the drag-and-drop client bundle for KnightCraft 5.
#
# The resulting zip is extracted OVER a clean .minecraft that already has
# Forge 1.20.1-47.4.10 installed. Everything inside is rooted at .minecraft/,
# so "extract here" is the whole install step.
#
# Deliberately NOT bundled: saves/, logs/, journeymap/, options.txt,
# servers.dat, .sl_password and every per-player cache. Those belong to the
# player, not to the pack.
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$HOME/knightcraft5-client-$(date +%Y-%m-%d).zip}"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

echo "staging from $SRC"

# --- payload ---------------------------------------------------------------
for d in mods config defaultconfigs kubejs packmenu; do
    [ -e "$SRC/$d" ] && cp -r "$SRC/$d" "$STAGE/"
done
[ -f "$SRC/icon.png" ] && cp "$SRC/icon.png" "$STAGE/"

# --- strip per-player state that lives inside config/ and kubejs/ ----------
rm -rf "$STAGE/config/jei/world" \
       "$STAGE/config/spark/tmp" \
       "$STAGE/kubejs/.cache" \
       "$STAGE/kubejs/exported" \
       "$STAGE/kubejs/logs"
rm -f  "$STAGE/config/skinrestorer/mojang_profile_cache.json" \
       "$STAGE/config/voicechat/username-cache.json"

# --- safety net: never ship a credential -----------------------------------
if find "$STAGE" -name '.sl_password' -o -name '*.private' | grep -q .; then
    echo "ABORT: credential file found in staging area" >&2
    exit 1
fi

cp "$SRC/KURULUM.txt" "$STAGE/KURULUM.txt"

rm -f "$OUT"
# `zip` is not guaranteed to be present on NixOS; use python's zipfile.
python3 - "$STAGE" "$OUT" <<'PY'
import os, sys, zipfile
stage, out = sys.argv[1], sys.argv[2]
n = 0
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as z:
    for root, dirs, files in os.walk(stage):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if f.startswith('.'):
                continue
            p = os.path.join(root, f)
            z.write(p, os.path.relpath(p, stage))
            n += 1
print(f"zipped {n} files")
PY

echo
echo "built: $OUT"
echo "size : $(du -h "$OUT" | cut -f1)"
echo "mods : $(ls "$STAGE/mods" | wc -l)"
