#!/usr/bin/env bash
# Builds the drag-and-drop SERVER bundle for KnightCraft 5.
#
# Extracted over a Forge 1.20.1-47.4.10 dedicated server root. Safe to extract
# over a RUNNING-BEFORE (stopped) server to update it: nothing in here touches
# world/, server.properties, ops.json, whitelist.json or eula.txt.
#
# Drag-and-drop can add and overwrite files but can never DELETE them, so a mod
# removed from the pack would linger in the target mods/ folder. That is what
# mods.manifest.txt and temizle.sh exist for - see SUNUCU-KURULUM.txt.
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$HOME/knightcraft5-server-$(date +%Y-%m-%d).zip}"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

# Client-only mods. A dedicated server either crashes on these or gains
# nothing from them. Keep this list in sync with mc-test-server/server-disabled.
CLIENT_ONLY=(
    AI-Improvements BetterThirdPerson Controlling durabilitytooltip
    embeddium EnchantmentDescriptions entityculling melody_forge
    MouseTweaks notenoughcrashes oculus overloadedarmorbar
    PackMenu SimpleDiscordRichPresence smoothchunk ToastControl
)

echo "staging from $SRC"
mkdir -p "$STAGE/mods"

skipped=0
for jar in "$SRC"/mods/*.jar; do
    base="$(basename "$jar")"
    keep=1
    for c in "${CLIENT_ONLY[@]}"; do
        [[ "$base" == "$c"* ]] && { keep=0; break; }
    done
    if [ $keep -eq 1 ]; then cp "$jar" "$STAGE/mods/"; else skipped=$((skipped+1)); fi
done
echo "  mods: kept $(ls "$STAGE/mods" | wc -l), dropped $skipped client-only"

for d in config defaultconfigs kubejs; do
    cp -r "$SRC/$d" "$STAGE/"
done

# per-player / per-install state that must never ship
rm -rf "$STAGE/config/jei" "$STAGE/config/spark/tmp" \
       "$STAGE/kubejs/.cache" "$STAGE/kubejs/exported" "$STAGE/kubejs/logs"
rm -f  "$STAGE/config/skinrestorer/mojang_profile_cache.json" \
       "$STAGE/config/voicechat/username-cache.json"

# --- guard rails -----------------------------------------------------------
# The test server runs with hardcore lives OFF. Shipping that config would
# silently delete the entire death-stakes design, so refuse to build it.
if ! grep -q '"AUTO_HARDCORE": true' "$STAGE/config/hqm/config.json5"; then
    echo "ABORT: AUTO_HARDCORE is not true - refusing to ship a no-lives pack" >&2
    exit 1
fi
if find "$STAGE" \( -name '.sl_password' -o -name 'server.properties' \
                 -o -name 'ops.json' -o -name 'whitelist.json' \) | grep -q .; then
    echo "ABORT: server identity or credential file in staging area" >&2
    exit 1
fi

# --- update tooling --------------------------------------------------------
( cd "$STAGE/mods" && ls *.jar ) > "$STAGE/mods.manifest.txt"

cat > "$STAGE/temizle.sh" <<'CLEAN'
#!/usr/bin/env bash
# Removes mod jars that are NOT part of this pack version.
# Run from the server root AFTER extracting the update, with the server stopped.
#   bash temizle.sh          -> lists what would be deleted
#   bash temizle.sh --apply  -> actually deletes
set -euo pipefail
[ -f mods.manifest.txt ] || { echo "mods.manifest.txt not found - run from server root"; exit 1; }
stale=0
for jar in mods/*.jar; do
    base="$(basename "$jar")"
    if ! grep -Fxq "$base" mods.manifest.txt; then
        stale=$((stale+1))
        if [ "${1:-}" = "--apply" ]; then rm -v "$jar"; else echo "STALE: $base"; fi
    fi
done
[ $stale -eq 0 ] && echo "no stale mods - mods/ matches the manifest"
[ "${1:-}" != "--apply" ] && [ $stale -gt 0 ] && echo && echo "re-run with --apply to delete these"
exit 0
CLEAN
chmod +x "$STAGE/temizle.sh"

cat > "$STAGE/server.properties.example" <<'PROPS'
# Rename to server.properties on a FRESH install only.
# On an update, leave your existing server.properties alone.
difficulty=normal
online-mode=false
max-players=40
view-distance=8
simulation-distance=6
spawn-protection=0
allow-flight=true
enforce-whitelist=false
motd=KnightCraft 5
level-type=minecraft\:normal
PROPS

cp "$SRC/SUNUCU-KURULUM.txt" "$STAGE/"

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
echo "mods : $(ls "$STAGE/mods" | wc -l)"
