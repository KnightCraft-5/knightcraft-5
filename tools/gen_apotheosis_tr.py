#!/usr/bin/env python3
"""Build the Turkish translation for Apotheosis and validate it against en_us.

WHY A GENERATOR AND NOT A HAND-WRITTEN JSON
A lang file fails silently. A missing key renders as the raw key
("item.apotheosis.gem_dust") and a wrong format specifier count throws a
MissingFormatArgumentException that shows up as a red tooltip or, worse, kicks
the client. Neither is caught by anything at build time, so this script does
the checking:

  * every key in the mod's en_us.json is present in the output
  * %s / %d counts match the English exactly, per key
  * literal %% counts match (Turkish writes %50, English writes 50%, so the
    ORDER differs but the COUNT must not)
  * the newline convention matches - Apotheosis mixes real newlines and literal
    backslash-n in the same file, and swapping them breaks the tooltip

TWO CATEGORIES ARE DERIVED, NOT TRANSLATED
  * enchantment.level.* are roman numerals - copied verbatim
  * item.minecraft.potion/splash_potion/lingering_potion/tipped_arrow.effect.*
    are vanilla potions Apotheosis adds variants of. Mojang already ships the
    naming pattern AND the effect names in tr_tr, so they are built from the
    official strings instead of invented. See the turkish-glossary-source note:
    a term that disagrees with vanilla reads as a bug to the player.

Run:  tools/gen_apotheosis_tr.py [--check]
"""
import glob
import json
import os
import pathlib
import re
import sys
import zipfile

INSTANCE = pathlib.Path(__file__).resolve().parent.parent
MODS = INSTANCE / "mods"
OUT = INSTANCE / "kubejs" / "assets" / "apotheosis" / "lang" / "tr_tr.json"
PARTS = sorted((INSTANCE / "tools" / "lang").glob("apotheosis_tr_*.json"))

# Effects Apotheosis adds potion variants for. The four vanilla ones are pulled
# from Mojang's file; the six Apotheosis-only ones are named here.
APOTH_EFFECTS = {
    "fatigue": "Bitkinlik",
    "flying": "Uçuş",
    "grievous": "Ağır Yara",
    "knowledge": "Bilgi",
    "sundering": "Parçalanma",
    "vitality": "Canlılık",
}
# Vanilla potion name patterns, filled with the effect name.
POTION_FORMS = {
    "potion": "{} İksiri",
    "splash_potion": "Patlayıcı {} İksiri",
    "lingering_potion": "Kalıcı {} İksiri",
    "tipped_arrow": "{} Oku",
}


def apotheosis_jar():
    for j in sorted(glob.glob(str(MODS / "*.jar"))):
        try:
            if "assets/apotheosis/lang/en_us.json" in zipfile.ZipFile(j).namelist():
                return j
        except Exception:
            continue
    raise SystemExit("apotheosis jar not found")


def mojang_tr():
    idx = sorted(glob.glob(os.path.expanduser(
        "~/.local/share/PrismLauncher/assets/indexes/*.json")))[-1]
    h = json.load(open(idx))["objects"]["minecraft/lang/tr_tr.json"]["hash"]
    p = os.path.expanduser(f"~/.local/share/PrismLauncher/assets/objects/{h[:2]}/{h}")
    return json.load(open(p))


def specs(s):
    """(%s/%d count, literal %% count). Order may differ between languages,
    the counts may not - Java formats positionally."""
    return (len(re.findall(r"%(?<!%%)[sd]", s.replace("%%", "\0"))), s.count("%%"))


def newline_style(s):
    return (s.count("\n"), s.count("\\n"))


def main():
    en = json.loads(zipfile.ZipFile(apotheosis_jar())
                    .read("assets/apotheosis/lang/en_us.json").decode("utf-8"))
    vanilla = mojang_tr()

    tr = {}
    for p in PARTS:
        chunk = json.load(open(p, encoding="utf-8"))
        dupes = set(chunk) & set(tr)
        if dupes:
            raise SystemExit(f"{p.name}: duplicate keys {sorted(dupes)[:5]}")
        tr.update(chunk)
    print(f"loaded {len(tr)} hand translations from {len(PARTS)} parts")

    # roman numerals - identical in both languages
    n_lvl = 0
    for k, v in en.items():
        if k.startswith("enchantment.level."):
            tr[k] = v
            n_lvl += 1

    # potions built from Mojang's own strings
    n_pot = 0
    for k in en:
        m = re.match(r"^item\.minecraft\.(\w+)\.effect\.(\w+)$", k)
        if not m:
            continue
        form, eff = m.groups()
        name = APOTH_EFFECTS.get(eff)
        if name is None:
            # vanilla effect - take Mojang's own noun so it matches the rest
            # of the player's tooltips exactly
            name = vanilla.get(f"effect.minecraft.{eff}")
            if name is None:
                raise SystemExit(f"no Turkish name for effect {eff}")
        tr[k] = POTION_FORMS[form].format(name)
        n_pot += 1
    print(f"derived {n_lvl} enchantment levels, {n_pot} potion names")

    # ---- validation -----------------------------------------------------
    missing = [k for k in en if k not in tr]
    extra = [k for k in tr if k not in en]
    bad_spec, bad_nl = [], []
    for k, v in en.items():
        if k not in tr:
            continue
        if specs(v) != specs(tr[k]):
            bad_spec.append(f"{k}: en{specs(v)} != tr{specs(tr[k])}\n"
                            f"      EN {v!r}\n      TR {tr[k]!r}")
        if newline_style(v) != newline_style(tr[k]):
            bad_nl.append(f"{k}: en{newline_style(v)} != tr{newline_style(tr[k])}")

    ok = True
    for label, items in (("MISSING keys", missing), ("EXTRA keys not in en_us", extra),
                         ("format specifier mismatch", bad_spec),
                         ("newline style mismatch", bad_nl)):
        if items:
            ok = False
            print(f"\n{label}: {len(items)}", file=sys.stderr)
            for i in items[:20]:
                print(f"  {i}", file=sys.stderr)
    if not ok:
        return 1

    print(f"\nvalidated {len(tr)} keys against en_us - all OK")
    if "--check" in sys.argv:
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(tr, ensure_ascii=False, indent=2,
                              sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(INSTANCE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
