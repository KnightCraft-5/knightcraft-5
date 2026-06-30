# KnightCraft 5

A Minecraft **Forge 1.20.1** modpack (189 mods), managed with [packwiz](https://packwiz.infra.link/).

This repo is the **source of truth**: mod versions, configs, scripts, and the custom
main menu. Mod jars themselves are *not* stored here — they're referenced by CurseForge
project/file ID in `mods/*.pw.toml` and downloaded on install.

## Layout

| Path | What |
|------|------|
| `pack.toml` / `index.toml` | packwiz pack metadata + file index |
| `mods/*.pw.toml` | one file per mod — CurseForge ID + hash |
| `*.pw.toml` (root) | shaderpacks (Complementary, Sildur's) |
| `config/`, `defaultconfigs/`, `kubejs/` | mod configuration & scripts |
| `packmenu/`, `resourcepacks/` | custom main menu and bundled resource packs |
| `serverconfig/` | server-side config (versioned, not shipped in exports) |

## Build a distributable pack

```bash
packwiz curseforge export -o KnightCraft5.zip
```

Import `KnightCraft5.zip` into the CurseForge app (Create Custom Profile → Import).

## Maintainer workflow

```bash
packwiz curseforge add <slug>     # add a mod
packwiz update --all              # bump everything to latest
git add -A && git commit -m "..." # version the change
```
