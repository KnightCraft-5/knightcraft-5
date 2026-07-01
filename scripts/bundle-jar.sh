#!/usr/bin/env sh
# CurseForge/Modrinth'te olmayan ya da indirilemeyen bir modu pakete gömer:
# jar'ı mods/ içine kopyalar, git ve packwiz'in onu tutması için gerekli
# satırları ekler, index'i tazeler. Sonra commit'leyip push'laman yeterli.
#
# Kullanım: scripts/bundle-jar.sh /yol/mod.jar
set -e
cd "$(dirname "$0")/.."

JAR="$1"
if [ -z "$JAR" ] || [ ! -f "$JAR" ]; then
  echo "Kullanım: scripts/bundle-jar.sh /yol/mod.jar" >&2
  exit 1
fi

NAME=$(basename "$JAR")
cp "$JAR" "mods/$NAME"

LINE="!mods/$NAME"
grep -qxF "$LINE" .gitignore     || printf '%s\n' "$LINE" >> .gitignore
grep -qxF "$LINE" .packwizignore || printf '%s\n' "$LINE" >> .packwizignore

if command -v packwiz >/dev/null 2>&1; then
  packwiz refresh
elif [ -x "$HOME/go/bin/packwiz" ]; then
  "$HOME/go/bin/packwiz" refresh
else
  echo "packwiz bulunamadı; elle 'packwiz refresh' çalıştır." >&2
fi

echo "Gömüldü: mods/$NAME — şimdi GitHub Desktop'ta commit'leyip push'la."
