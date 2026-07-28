#!/usr/bin/env python3
"""Give every modded weapon an Epic Fight weapon type.

WHY
Epic Fight only ships capabilities for its own weapons and vanilla. Every one of
the 151 modded weapons measured in tools/weapon_sweep.py has NO capability, so
Epic Fight treats them as bare fists: no moveset, no combo, and none of the
`impact` / `armor_negation` combat stats it layers on top of raw attack damage.

Type is inferred from the item name. Attribute values are Epic Fight's own
diamond-tier defaults for that type - deliberately NOT invented per weapon,
because a wrong stat is worse than a generic one.

Files land at data/<namespace>/capabilities/weapons/<item>.json, which is the
path Epic Fight reads for third-party items.
"""
import json, os, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent / 'kubejs/data'

# order matters - first match wins
RULES = [
    (('dagger', 'knife', 'claw', 'fang', 'sting', 'talon'), 'dagger',
     {'impact': 0.5, 'max_strikes': 3}),
    (('spear', 'pike', 'lance', 'ahlspiess', 'glaive', 'halberd', 'trident', 'partisan'), 'spear',
     {'impact': 3.0, 'max_strikes': 2}),
    (('katana', 'tachi', 'uchigatana', 'nodachi'), 'tachi',
     {'impact': 2.5, 'max_strikes': 2}),
    # 'great' MUST be tested before 'sword' - soul_great_sword matched 'sword'
    # first and came out a longsword when it is plainly a greatsword.
    (('great', 'greatsword', 'greataxe', 'axe', 'hammer', 'maul', 'cleaver',
      'scythe', 'club', 'column', 'trunk', 'forge', 'incinerator', 'annihilator'), 'greatsword',
     {'armor_negation': 10.0, 'impact': 4.0, 'max_strikes': 4}),
    (('sword', 'blade', 'saber', 'sabre', 'rapier', 'falchion', 'scimitar'), 'longsword',
     {'impact': 2.5, 'max_strikes': 2}),
]
# not weapons, or Epic Fight cannot use them
SKIP = ('spawn_egg', '_hand', '_inventory', 'staff', 'wand', 'bow', 'crossbow', 'shield',
        'fragment', '_half', '_part', 'blade1', 'blade2', 'handle', 'core', 'hilt')

def infer(path):
    if any(s in path for s in SKIP):
        return None
    for keys, wtype, attrs in RULES:
        if any(k in path for k in keys):
            return wtype, attrs
    return None

def main():
    src = pathlib.Path('/tmp/weapons.txt')
    if not src.exists():
        print('no /tmp/weapons.txt - run the weapon sweep first'); return 1
    written = skipped = 0
    by_type = {}
    for line in src.read_text().splitlines():
        item = line.strip()
        if not item or ':' not in item:
            continue
        ns, path = item.split(':', 1)
        got = infer(path)
        if not got:
            skipped += 1
            continue
        wtype, attrs = got
        d = ROOT / ns / 'capabilities' / 'weapons'
        d.mkdir(parents=True, exist_ok=True)
        f = d / f'{path}.json'
        if f.exists():                       # never clobber a hand-written one
            continue
        f.write_text(json.dumps({'attributes': {'common': attrs},
                                 'type': f'epicfight:{wtype}'}, indent=1))
        by_type[wtype] = by_type.get(wtype, 0) + 1
        written += 1
    print(f'wrote {written} capability files, skipped {skipped} non-weapons')
    for t, n in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f'   {t:12} {n}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
