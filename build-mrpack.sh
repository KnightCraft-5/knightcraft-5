#!/usr/bin/env bash
# Builds the lightweight importable pack (.mrpack) for KnightCraft 5.
#
# Unlike the drag-and-drop zips, this contains NO jars - about 2 MB instead of
# 600. It lists every mod as a URL plus hashes and lets the launcher fetch them
# from the R2 CDN. Importable by PrismLauncher, the Modrinth App and ATLauncher.
#
# The mod mirror must be current before building:  ./sync-mods.sh --push
#
#   CDN_BASE   defaults to https://knightcraft-cdn.umceko.com
#
# Usage:  ./build-mrpack.sh [output.mrpack]
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$HOME/knightcraft5-$(date +%Y-%m-%d).mrpack}"
CDN="${CDN_BASE:-https://knightcraft-cdn.umceko.com}"
VERSION="$(date +%Y.%m.%d)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

[ -d "$SRC/mods" ] || { echo "no mods/ - run ./sync-mods.sh --pull first" >&2; exit 1; }

echo "building $VERSION against $CDN"

# --- overrides: everything that is not a jar -------------------------------
mkdir -p "$STAGE/overrides"
for d in config defaultconfigs kubejs; do
    cp -r "$SRC/$d" "$STAGE/overrides/"
done
rm -rf "$STAGE/overrides/config/jei/world" "$STAGE/overrides/config/spark/tmp" \
       "$STAGE/overrides/kubejs/.cache" "$STAGE/overrides/kubejs/exported" \
       "$STAGE/overrides/kubejs/logs"
rm -f  "$STAGE/overrides/config/skinrestorer/mojang_profile_cache.json" \
       "$STAGE/overrides/config/voicechat/username-cache.json"
cp "$SRC/KURULUM.txt" "$STAGE/overrides/"

if ! grep -q '"AUTO_HARDCORE": true' "$STAGE/overrides/config/hqm/config.json5"; then
    echo "ABORT: AUTO_HARDCORE is not true" >&2; exit 1
fi

# --- index -----------------------------------------------------------------
python3 - "$SRC" "$STAGE" "$CDN" "$VERSION" <<'PY'
import hashlib, json, os, sys, urllib.parse
src, stage, cdn, version = sys.argv[1:5]

client_only = [l.strip() for l in open(os.path.join(src, 'client-only-mods.txt'))
               if l.strip() and not l.startswith('#')]

files = []
for name in sorted(os.listdir(os.path.join(src, 'mods'))):
    if not name.endswith('.jar'):
        continue
    p = os.path.join(src, 'mods', name)
    s1, s5 = hashlib.sha1(), hashlib.sha512()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            s1.update(b); s5.update(b)
    is_client_only = any(name.startswith(c) for c in client_only)
    files.append({
        "path": f"mods/{name}",
        "hashes": {"sha1": s1.hexdigest(), "sha512": s5.hexdigest()},
        "env": {"client": "required",
                "server": "unsupported" if is_client_only else "required"},
        # quote() leaves '/' alone and percent-encodes spaces, which two of
        # these filenames contain.
        "downloads": [f"{cdn}/mods/{urllib.parse.quote(name)}"],
        "fileSize": os.path.getsize(p),
    })

index = {
    "formatVersion": 1,
    "game": "minecraft",
    "versionId": version,
    "name": "KnightCraft 5",
    "summary": "Turkce RPG modpack - zindanlar, gorevler ve kapili teknoloji.",
    "files": files,
    "dependencies": {"minecraft": "1.20.1", "forge": "47.4.10"},
}
with open(os.path.join(stage, 'modrinth.index.json'), 'w') as fh:
    json.dump(index, fh, indent=2)

srv = sum(1 for f in files if f['env']['server'] == 'required')
print(f"  indexed {len(files)} mods  ({srv} server-side, {len(files)-srv} client-only)")
PY

# --- zip it ----------------------------------------------------------------
rm -f "$OUT"
python3 - "$STAGE" "$OUT" <<'PY'
import os, sys, zipfile
stage, out = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for root, dirs, fs in os.walk(stage):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in fs:
            if f.startswith('.'):
                continue
            p = os.path.join(root, f)
            z.write(p, os.path.relpath(p, stage))
PY

echo
echo "built: $OUT"
echo "size : $(du -h "$OUT" | cut -f1)"
