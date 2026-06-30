#!/usr/bin/env sh
# Download / update the KnightCraft 5 mod jars from the packwiz metadata.
# Run this once during setup, and again whenever the mod list changes.
# macOS / Linux. Needs Java (you already have it if Minecraft runs).
set -e
cd "$(dirname "$0")/.."   # move to the pack root (where pack.toml lives)

BOOT="packwiz-installer-bootstrap.jar"
URL="https://github.com/packwiz/packwiz-installer-bootstrap/releases/latest/download/packwiz-installer-bootstrap.jar"

if ! command -v java >/dev/null 2>&1; then
  echo "ERROR: Java not found on PATH. Install a JRE (e.g. Temurin) or run this from Prism." >&2
  exit 1
fi

if [ ! -f "$BOOT" ]; then
  echo "Downloading packwiz-installer-bootstrap..."
  if command -v curl >/dev/null 2>&1; then curl -fsSL -o "$BOOT" "$URL"; else wget -O "$BOOT" "$URL"; fi
fi

echo "Updating mods..."
java -jar "$BOOT" -s client pack.toml
echo "Done. Mods are up to date."
