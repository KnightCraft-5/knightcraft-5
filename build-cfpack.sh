#!/usr/bin/env bash
# Builds a CurseForge-app-importable modpack zip.
#
# WHY THIS IS NOT LIGHTWEIGHT
# CurseForge's manifest identifies each mod by projectID + fileID and has no
# field for a download URL, so it cannot point at our CDN the way .mrpack does.
# Building a small CurseForge pack would require the CurseForge project and file
# ID of all 189 jars, which needs a working Core API key.
#
# So this ships the jars inside overrides/ with an empty "files" list. The result
# is the same size as the drag-and-drop zip, but the CurseForge app imports it in
# one click and installs Forge itself, which dragging does not.
#
# Usage:  ./build-cfpack.sh [output.zip]
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$HOME/knightcraft5-curseforge-$(date +%Y-%m-%d).zip}"
VERSION="$(date +%Y.%m.%d)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

[ -d "$SRC/mods" ] || { echo "no mods/ - run ./sync-mods.sh --pull first" >&2; exit 1; }

mkdir -p "$STAGE/overrides"
cp -r "$SRC/mods" "$STAGE/overrides/"
for d in config defaultconfigs kubejs; do
    cp -r "$SRC/$d" "$STAGE/overrides/"
done
cp "$SRC/KURULUM.txt" "$STAGE/overrides/"

rm -rf "$STAGE/overrides/config/jei/world" "$STAGE/overrides/config/spark/tmp" \
       "$STAGE/overrides/kubejs/.cache" "$STAGE/overrides/kubejs/exported" \
       "$STAGE/overrides/kubejs/logs"
rm -f  "$STAGE/overrides/config/skinrestorer/mojang_profile_cache.json" \
       "$STAGE/overrides/config/voicechat/username-cache.json"

grep -q '"AUTO_HARDCORE": true' "$STAGE/overrides/config/hqm/config.json5" \
    || { echo "ABORT: AUTO_HARDCORE is not true" >&2; exit 1; }

cat > "$STAGE/manifest.json" <<JSON
{
  "minecraft": {
    "version": "1.20.1",
    "modLoaders": [
      { "id": "forge-47.4.10", "primary": true }
    ]
  },
  "manifestType": "minecraftModpack",
  "manifestVersion": 1,
  "name": "KnightCraft 5",
  "version": "$VERSION",
  "author": "KnightCraft 5",
  "files": [],
  "overrides": "overrides"
}
JSON

# The CurseForge app shows this in the import dialog; it is optional but its
# absence makes some versions complain.
{
  echo "<ul>"
  for j in "$STAGE/overrides/mods"/*.jar; do
      printf '<li>%s</li>\n' "$(basename "$j" .jar)"
  done
  echo "</ul>"
} > "$STAGE/modlist.html"

python3 -c "import json,sys; json.load(open(sys.argv[1])); print('manifest.json valid')" "$STAGE/manifest.json"

rm -f "$OUT"
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
echo "mods : $(ls "$STAGE/overrides/mods" | wc -l)"
