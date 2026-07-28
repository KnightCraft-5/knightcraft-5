#!/usr/bin/env python3
"""Verify that advancement / entity / structure ids actually exist in the mods.

A wrong id in a quest file is not an error — FTB Quests accepts it happily and
the quest simply never completes. It surfaces weeks later as a player stuck
behind a task that cannot be finished.

Two real examples this exists to catch:

  * Ice and Fire nests its advancements one level deeper than its namespace, so
    the real id is `iceandfire:iceandfire/kill_hydra`. `iceandfire:kill_hydra`
    looks right and is dead. MineColonies does the same thing.
  * `iceandfire:iceandfire/kill_if_dragon` was assumed to require all three
    dragon colours. Its `requirements` is a single group, which is OR — any one
    dragon completes it. Assumptions about AND/OR change quest design, so this
    prints the semantics rather than leaving them to be guessed.

Usage:
    tools/verify_ids.py                 # check ids used by the quest book
    tools/verify_ids.py --plan          # check the ids the remake plan depends on
    tools/verify_ids.py --show ars_nouveau   # list everything a namespace ships
"""
import glob
import json
import os
import re
import sys
import zipfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODS = os.path.join(ROOT, 'mods')

# Ids known to be broken upstream. Using any of these ships a dead quest.
BANNED = {
    'nova_structures:adventure/find_all_illager_structures':
        'references a structure id that does not exist (badland_miner_outpost, missing s)',
    'nova_structures:nether/find_nether_skeleton':
        'references skeleton_camp_basalt, which does not exist',
}
BANNED_PATTERNS = [
    (re.compile(r'^cataclysm:music_disc_'),
     'chance-gated drop, never guaranteed'),
]


def build_index():
    """advancements, entities, structures, and advancement requirement data."""
    adv, ents, structs = set(), set(), set()
    adv_data = {}
    for jar in sorted(glob.glob(os.path.join(MODS, '*.jar'))):
        try:
            z = zipfile.ZipFile(jar)
        except Exception:
            continue
        for n in z.namelist():
            m = re.match(r'^data/([a-z0-9_.-]+)/advancements/(.+)\.json$', n)
            if m:
                # NOTE: the id keeps the full nested path, so a mod that stores
                # advancements under data/<ns>/advancements/<ns>/ produces
                # "<ns>:<ns>/name". That doubling is the trap.
                ident = f'{m.group(1)}:{m.group(2)}'
                adv.add(ident)
                try:
                    adv_data[ident] = json.loads(z.read(n))
                except Exception:
                    pass
                continue
            m = re.match(r'^data/([a-z0-9_.-]+)/worldgen/structure/(.+)\.json$', n)
            if m:
                structs.add(f'{m.group(1)}:{m.group(2)}')
                continue
            m = re.match(r'^data/([a-z0-9_.-]+)/loot_tables/entities/(.+)\.json$', n)
            if m:
                ents.add(f'{m.group(1)}:{m.group(2)}')
                continue
            if n.endswith('lang/en_us.json'):
                try:
                    d = json.loads(z.read(n).decode('utf-8-sig'))
                except Exception:
                    continue
                for k in d:
                    m2 = re.match(r'^entity\.([a-z0-9_]+)\.([a-z0-9_./]+)$', k)
                    if m2:
                        ents.add(f'{m2.group(1)}:{m2.group(2)}')
        z.close()
    return adv, ents, structs, adv_data


def requirement_semantics(data):
    """Return a human phrase for how an advancement's criteria combine."""
    crit = list(data.get('criteria', {}))
    req = data.get('requirements')
    if not req:
        return f'AND of {len(crit)} criteria' if len(crit) > 1 else 'single criterion'
    if len(req) == 1 and len(req[0]) > 1:
        return f'OR of {len(req[0])} criteria  <-- any ONE completes it'
    if len(req) > 1:
        return f'AND of {len(req)} groups'
    return 'single criterion'


# The ids the remake plan depends on: (kind, id, where it is used)
PLAN_IDS = [
    ('advancement', 'minecraft:story/root', 'act1 entry'),
    ('advancement', 'minecraft:story/smelt_iron', 'act1 spine'),
    ('advancement', 'minecraft:story/obtain_armor', 'act1 spine'),
    ('advancement', 'minecraft:story/mine_diamond', 'act3 entry'),
    ('advancement', 'minecraft:adventure/sleep_in_bed', 'act2 entry (existing)'),
    ('advancement', 'minecraft:nether/obtain_blaze_rod', 'act6 spine'),
    ('advancement', 'minecraft:nether/brew_potion', 'act6 spine - fire res'),
    ('advancement', 'minecraft:nether/obtain_ancient_debris', 'act6 spine'),
    ('advancement', 'minecraft:nether/netherite_armor', 'act8 spine'),
    ('advancement', 'betterdungeons:zombie_dungeon', 'act1 dungeon clear'),
    ('advancement', 'betterdungeons:all_dungeons', 'act3 spine'),
    ('advancement', 'takesapillage:pillager_camp', 'act2 dungeon clear'),
    ('advancement', 'dungeons_arise:find_bandit_towers', 'act2 spine'),
    ('advancement', 'dungeons_arise:find_mining_system', 'act3 dungeon clear'),
    ('advancement', 'mowziesmobs:kill_ferrous_wroughtnaut', 'act4 BOSS'),
    ('advancement', 'nova_structures:adventure/conquer_miner_outpost', 'act4 dungeon clear'),
    ('advancement', 'cataclysm:find_burning_arena', 'act5 entry'),
    ('advancement', 'cataclysm:find_cursed_pyramid', 'act5'),
    ('advancement', 'cataclysm:kill_ignis', 'act6 BOSS'),
    ('advancement', 'cataclysm:find_frosted_prison', 'act7 dungeon clear'),
    ('advancement', 'cataclysm:kill_maledictus', 'act7 dungeon clear'),
    ('advancement', 'cataclysm:kill_ender_golem', 'act7 spine'),
    ('advancement', 'cataclysm:find_ancient_factory', 'act8 dungeon clear'),
    ('advancement', 'cataclysm:kill_ender_guardian', 'act8 mid boss'),
    ('advancement', 'cataclysm:kill_harbinger', 'act8 BOSS'),
    ('advancement', 'cataclysm:kill_all_bosses', 'act8 capstone'),
    ('advancement', 'legendary_monsters:defeat_overgrown_colossus', 'act5 spine'),
    ('advancement', 'legendary_monsters:locate_mossy_temple', 'act5 dungeon clear'),
    ('advancement', 'legendary_monsters:defeat_frostbitten_golem', 'act7 spine'),
    ('advancement', 'legendary_monsters:defeat_annihilation_pursuer', 'act8 spine'),
    ('advancement', 'legendary_monsters:defeat_the_obliterator', 'act8 spine'),
    ('advancement', 'nova_structures:nether/find_keep', 'act6 dungeon clear'),
    ('advancement', 'iceandfire:iceandfire/kill_if_dragon', 'act7 BOSS'),
    ('advancement', 'iceandfire:iceandfire/kill_cyclops', 'act7 spine'),
    ('advancement', 'iceandfire:iceandfire/kill_hydra', 'act7 spine'),
    ('advancement', 'iceandfire:iceandfire/kill_troll', 'act7 spine'),
    ('advancement', 'ars_nouveau:novice_spell_book', 'magic track'),
    ('advancement', 'ars_nouveau:imbuement_chamber', 'magic track'),
    ('advancement', 'ars_nouveau:enchanting_apparatus', 'magic track'),
    ('advancement', 'ars_nouveau:apprentice_spell_book', 'magic track'),
    ('advancement', 'ars_nouveau:archmage_spell_book', 'magic track capstone'),
    ('advancement', 'minecolonies:minecraft/craft_supply', 'colony track'),
    ('advancement', 'minecolonies:minecolonies/place_townhall', 'colony track'),
    ('advancement', 'minecolonies:minecolonies/build_builder', 'colony track'),
    ('advancement', 'lightmanscurrency:currency/coin_mint', 'trade track'),
    ('advancement', 'lightmanscurrency:currency/atm', 'trade track'),
    ('advancement', 'minecraft:adventure/trade', 'trade track entry'),
    ('entity', 'minecraft:ravager', 'act2 BOSS kill'),
    ('entity', 'cataclysm:amethyst_crab', 'act3 BOSS kill'),
    ('entity', 'cataclysm:kobolediator', 'act5 BOSS kill'),
    ('entity', 'cataclysm:coralssus', 'act5 spine kill'),
    ('entity', 'iceandfire:fire_dragon', 'act7 BOSS fallback'),
    ('structure', 'mowziesmobs:wrought_chamber', 'act4 entry'),
    ('structure', 'iceandfire:gorgon_temple', 'act7 entry'),
    ('structure', 'cataclysm:burning_arena', 'act5 entry alt'),
    ('dimension', 'ancient_obelisks:obelisk', 'act4 spine'),
    ('dimension', 'dungeon_realm:dungeon', 'act6 spine'),
]


def main():
    adv, ents, structs, adv_data = build_index()
    print(f'indexed {len(adv)} advancements, {len(ents)} entities, '
          f'{len(structs)} structures from {len(glob.glob(os.path.join(MODS, "*.jar")))} jars\n')

    if '--show' in sys.argv:
        ns = sys.argv[sys.argv.index('--show') + 1]
        for label, coll in (('advancements', adv), ('entities', ents), ('structures', structs)):
            hits = sorted(x for x in coll if x.startswith(ns + ':'))
            print(f'-- {label} ({len(hits)})')
            for h in hits:
                print(f'   {h}')
        return 0

    lookup = {'advancement': adv, 'entity': ents, 'structure': structs}
    bad, notes = [], []

    for kind, ident, use in PLAN_IDS:
        if ident in BANNED:
            bad.append(f'{ident}  BANNED: {BANNED[ident]}')
            continue
        for pat, why in BANNED_PATTERNS:
            if pat.match(ident):
                bad.append(f'{ident}  BANNED: {why}')
                break
        if kind == 'dimension':
            # dimensions live at data/<ns>/dimension/<name>.json - check directly
            ns, path = ident.split(':', 1)
            found = any(
                f'data/{ns}/dimension/{path}.json' in zipfile.ZipFile(j).namelist()
                for j in glob.glob(os.path.join(MODS, '*.jar'))
                if ns in os.path.basename(j).lower().replace('-', '_')
                or True)
            status = 'OK  ' if found else 'MISSING'
            if not found:
                bad.append(f'{ident}  ({kind}, {use})')
            print(f'  {status} {kind:12} {ident:58} {use}')
            continue

        ok = ident in lookup[kind]
        print(f'  {"OK  " if ok else "MISSING"} {kind:12} {ident:58} {use}')
        if not ok:
            bad.append(f'{ident}  ({kind}, {use})')
        elif kind == 'advancement' and ident in adv_data:
            sem = requirement_semantics(adv_data[ident])
            if 'OR' in sem or 'AND of' in sem:
                notes.append(f'{ident}: {sem}')

    if notes:
        print('\nmulti-criterion advancements - check the design assumes the right one:')
        for n in notes:
            print(f'  {n}')

    if bad:
        print(f'\n{len(bad)} PROBLEM(S):', file=sys.stderr)
        for b in bad:
            print(f'  {b}', file=sys.stderr)
        return 1
    print(f'\nall {len(PLAN_IDS)} planned ids verified')
    return 0


if __name__ == '__main__':
    sys.exit(main())
