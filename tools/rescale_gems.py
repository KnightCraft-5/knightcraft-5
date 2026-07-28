#!/usr/bin/env python3
"""Deflate gem values so the whole power curve fits tools/balance_model.py.

The old curve gave ancient offence gems MULTIPLY_BASE 3.0. Five sockets of
MULTIPLY_BASE are ADDITIVE among themselves, so that was base x16 on a weapon -
the single biggest source of number inflation in the pack. Defence was worse:
armour has 20 sockets across a set, so a 1.6 per-socket value is x33.

New targets come straight from the model's GEAR table: total gem multiplier 2.0
at ancient for melee, half that for ranged, and defence sized to move a player
from ~45 to ~57 armour rather than into the hundreds.

SOCKET COUNT IS 3.43, NOT 5. An ancient item rolls up to 5 sockets but the five
rules have chances 1.0/0.85/0.65/0.45/0.25 - all five landing is 6.2%, and the
EXPECTED count is 3.20. The Sigil of Socketing tops an item up to 3 (stock cap,
deliberately left alone), giving an effective 3.43. Values below are sized for
3.43 sockets; an earlier pass assumed 5 and therefore under-delivered by 30%.

SHAPE: every curve keeps the same relative ramp, so rarity still feels like
progress; only the ceiling moves.
"""
import json, glob, os

SHAPE = {'common': 0.10, 'uncommon': 0.20, 'rare': 0.35,
         'epic': 0.55, 'mythic': 0.75, 'ancient': 1.00}

# (attribute, operation) -> ancient ceiling PER SOCKET.
# None means "leave completely alone" (utility, procs, movement, dodge).
CEIL = {
    ('minecraft:generic.attack_damage', 'MULTIPLY_BASE'): 0.29,   # 5 sockets -> x2.0
    # RANGED IS NOT UTILITY. arrow_velocity and draw_speed were originally left
    # out of this table as "utility", but arrow damage SCALES WITH VELOCITY and
    # draw speed is a raw dps multiplier. Left undeflated they compounded with
    # Power into a bow doing 120 dps against melee's ~23 - the design calls for
    # melee to be 2x ranged, so the ratio was inverted by roughly 5x.
    ('attributeslib:arrow_damage',      'MULTIPLY_BASE'): 0.08,
    ('attributeslib:arrow_velocity',    'MULTIPLY_BASE'): 0.08,
    ('attributeslib:draw_speed',        'MULTIPLY_BASE'): 0.40,
    ('minecraft:generic.armor',         'MULTIPLY_BASE'): 0.022,  # 20 sockets -> ~x1.3
    ('minecraft:generic.max_health',    'MULTIPLY_BASE'): 0.029,  # 20 sockets -> ~x1.4
    ('minecraft:generic.armor',         'MULTIPLY_TOTAL'): 0.07,  # compounds - keep tiny
    ('minecraft:generic.max_health',    'MULTIPLY_TOTAL'): 0.07,
    ('attributeslib:fire_damage',       'ADDITION'): 3.0,         # BYPASSES ARMOUR
    ('attributeslib:cold_damage',       'ADDITION'): 3.0,         # BYPASSES ARMOUR
    ('attributeslib:fire_damage',       'MULTIPLY_TOTAL'): 0.09,
    ('attributeslib:cold_damage',       'MULTIPLY_TOTAL'): 0.09,
    ('attributeslib:crit_damage',       'ADDITION'): 0.15,
    ('attributeslib:crit_chance',       'ADDITION'): 0.12,
    ('attributeslib:armor_pierce',      'ADDITION'): 4.4,
    ('attributeslib:life_steal',        'ADDITION'): 0.09,
    ('attributeslib:arrow_velocity',    'MULTIPLY_TOTAL'): 0.06,
    ('apotheosis:damage_reduction',     '-'): 0.12,               # stacks with affix reduction
}
# warlord's helmet attack_damage is a separate, smaller ceiling (helmet is 1 piece)
HELMET_AD = 0.09

def rescale(path):
    d = json.load(open(path))
    changed = []
    for b in d.get('bonuses', []):
        attr = b.get('attribute', b.get('type'))
        op = b.get('operation', '-')
        gc = (b.get('gem_class') or {}).get('key', '-')
        vals = b.get('values')
        if not isinstance(vals, dict) or not all(k in SHAPE for k in vals):
            continue                      # dict-valued procs / non-rarity maps
        key = (attr, op)
        if key not in CEIL:
            continue                      # utility - untouched
        ceil = HELMET_AD if (attr == 'minecraft:generic.attack_damage' and gc == 'helmet') else CEIL[key]
        old = vals.get('ancient')
        for r in list(vals):
            sign = -1 if (isinstance(vals[r], (int, float)) and vals[r] < 0) else 1
            vals[r] = round(sign * ceil * SHAPE[r], 4)
        changed.append((attr, op, gc, old, vals['ancient']))
    if changed:
        json.dump(d, open(path, 'w'), indent=2)
    return changed

if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(__file__), '..'))
    total = 0
    for f in sorted(glob.glob('kubejs/data/apotheosis/gems/**/*.json', recursive=True)):
        for attr, op, gc, old, new in rescale(f):
            print(f"  {os.path.basename(f):18} {attr.split(':')[-1]:20} {op:14} {gc:14} {old} -> {new}")
            total += 1
    print(f"\nrescaled {total} bonus curves")
