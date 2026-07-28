#!/usr/bin/env python3
"""End-to-end balance report: every act's gear vs that act's capstone.

WHY THIS EXISTS
The balance work produced numbers in four separate places - GEAR in balance_model,
ACT_TIERS and WINDOW_BOSSES in gen_boss_rules, and the Ice and Fire dragon block in
config/iceandfire-common.toml. Nothing put them side by side, so it was impossible to
answer "is act 5 actually tuned?" without re-deriving it by hand each time.

THE TRAP THIS AVOIDS
`TTK = hp / dps` is only valid for a boss that accepts damage continuously. Five of the
seven modded capstones gate damage behind an animation window, a parry, or self-healing,
and each measured 3-19x away from the model for a DIFFERENT reason. Scoring them with
model DPS says they are wildly mis-tuned when they are correct. Every window boss below
is therefore scored against its OWN measured rate, recorded next to it.

Run: tools/balance_report.py
"""
import sys, os, re, math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from balance_model import (GEAR, DPS_PER_AD, armour_mult, damage_to_player,
                           GROUP_SIZE, FIGHT_SECONDS)
from gen_boss_rules import ACT_TIERS, WINDOW_BOSSES
from gen_boss_quests import BOSSES

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# DPS measured live against that specific boss, with that act's gear. These are
# observations, not derivations - see UNTESTED.md section F for how each was taken.
MEASURED_DPS = {
    'mowziesmobs:ferrous_wroughtnaut': (1.50, 'window; ONE attacker only, never group-scaled'),
    'cataclysm:amethyst_crab':         (4.94, 'burrow window'),
    'mowziesmobs:frostmaw':            (2.40, 'awake only; sleeps between phases'),
    'cataclysm:ignis':                 (1.01, 'parry gate (blockingProgress)'),
    'cataclysm:the_harbinger':        (34.03, 'bow; melee is NEGATIVE, it out-heals you'),
    'iceandfire:fire_dragon':         (31.02, 'bow; health comes from iceandfire-common.toml'),
}
SOLO_ONLY = {'mowziesmobs:ferrous_wroughtnaut'}


def iaf_dragon_hp(stage=3):
    """Stage-N fire dragon health, read from the live config rather than assumed."""
    cfg = os.path.join(PACK, 'config', 'iceandfire-common.toml')
    m = re.search(r'"Dragon Health" = ([\d.]+)', open(cfg).read())
    if not m:
        return None
    # measured age->health fractions under this scaling (see memory: iaf-dragon-spawn-health)
    return float(m.group(1)) * {1: 0.117, 3: 0.501, 5: 0.962}[stage]


def model_dps(act):
    g = GEAR[act]
    ad = g['weapon'] * g['gem']
    return ad * DPS_PER_AD * armour_mult(ad, ACT_TIERS[act]['armor']), ad


def main():
    print('ACT CAPSTONES - can that act\'s best gear clear it as a 5-person raid?\n')
    hdr = (f'{"act":>3}  {"capstone":<34} {"hp":>8} {"dps":>6} {"src":>5} '
           f'{"5p TTK":>7} {"tgt":>5} {"":>4} {"solo":>7}')
    print(hdr); print('-' * len(hdr))
    problems = []
    for act in sorted(BOSSES):
        cap = BOSSES[act][0][0]
        tier = ACT_TIERS[act]
        mult = WINDOW_BOSSES.get(cap)
        hp = iaf_dragon_hp(3) if cap == 'iceandfire:fire_dragon' else tier['health'] * (mult or 1)
        if cap in MEASURED_DPS:
            dps, why = MEASURED_DPS[cap]; src = 'meas'
        else:
            dps, _ = model_dps(act); why = ''; src = 'model'
        n = 1.0 if cap in SOLO_ONLY else GROUP_SIZE
        ttk = hp / (dps * n)
        solo = hp / dps
        tgt = FIGHT_SECONDS.get(act)
        if tgt is None:
            flag = ''
        elif cap in SOLO_ONLY:
            flag = 'solo'
        elif 0.7 * tgt <= ttk <= 1.45 * tgt:
            flag = 'ok'
        else:
            flag = '>>' if ttk > tgt else '<<'
            problems.append((act, cap, ttk, tgt))
        print(f'{act:>3}  {cap:<34} {hp:>8,.0f} {dps:>6.2f} {src:>5} '
              f'{ttk:>6.0f}s {str(tgt or "-"):>5} {flag:>4} {solo/60:>6.1f}m')
        if why:
            print(f'{"":>5}  {"":<34} {why}')

    # The Ender Dragon has an In Control rule but no entry in BOSSES - there is no
    # act 9 chapter, it sits past the end of the book - so it drops out of the loop
    # above. It is the one HP the owner pinned by hand (50,000), so it is reported
    # rather than scored.
    ed = ACT_TIERS[9]
    ed_dps = MEASURED_DPS['cataclysm:the_harbinger'][0]   # best endgame bow rate
    print(f'{9:>3}  {"minecraft:ender_dragon":<34} {ed["health"]:>8,} {ed_dps:>6.2f} '
          f'{"meas":>5} {ed["health"]/(ed_dps*GROUP_SIZE):>6.0f}s {"-":>5} {"pin":>4} '
          f'{ed["health"]/ed_dps/60:>6.1f}m')
    print(f'{"":>5}  {"":<34} owner-pinned 50k; no act-9 chapter, so never quest-gated')

    print('\nHITS TO KILL A PLAYER OF THAT ACT (owner\'s band: 4-7)\n')
    hdr2 = f'{"act":>3} {"raw":>5} {"armor":>6} {"prot":>5} {"affix":>6} {"taken":>7} {"hits":>6}'
    print(hdr2); print('-' * len(hdr2))
    for act in range(1, 10):
        g, t = GEAR[act], ACT_TIERS[act]
        taken = damage_to_player(t['damage'], g['armor'], g['prot'], g['affix'])
        hits = g['hp'] / taken
        flag = 'ok' if 4 <= hits <= 7 else ('HARD' if hits < 4 else 'soft')
        print(f'{act:>3} {t["damage"]:>5} {g["armor"]:>6} {g["prot"]:>5} {g["affix"]:>6.2f} '
              f'{taken:>7.2f} {hits:>5.1f} {flag}')

    print('\nDRAGON BREATH - seconds survived standing in the stream (act-7 gear)\n')
    g7 = GEAR[7]
    # armor is absent from this on purpose: breath is in the bypasses_armor tag
    factor = (1 - min(0.01 * g7['prot'], 0.50)) * g7['affix']
    cfg = open(os.path.join(PACK, 'config', 'iceandfire-common.toml')).read()
    live = {k: float(v) for k, v in re.findall(
        r'"Dragon Attack Damage\((\w+) breath\)" = ([\d.]+)', cfg)}
    print(f'{"breath":>16} {"raw":>5} {"@2/s":>7} {"@2.5/s":>7} {"@3/s":>7}')
    print('-' * 46)
    for name, raw in live.items():
        secs = [g7['hp'] / (raw * factor * t) for t in (2, 2.5, 3)]
        print(f'{name:>16} {raw:>5.1f} ' + ' '.join(f'{s:>6.1f}s' for s in secs))
    print('\n  Design target ~3s: long enough to react, short enough to punish standing')
    print('  in it. The tick rate is the open variable - the owner reports 2-3/second,')
    print('  which is the spread shown. Confirm with ~/mc-test-server/breath_test.py,')
    print('  which measures damage-per-second-of-exposure directly.')

    print('\nNOTE: dragon breath BYPASSES armor entirely (bypasses_armor tag) and does not')
    print('      scale with "Dragon Attack Damage" - it has its own config keys. Against a')
    print('      dragon only Protection and affixes apply, so the armor column above is')
    print('      not the relevant defence. It also ticks 2-3x/second, so "hits to kill" is')
    print('      the wrong frame for it - seconds-of-exposure is (tools breath_test.py).')

    if problems:
        print(f'\n{len(problems)} capstone(s) outside target:')
        for act, cap, ttk, tgt in problems:
            print(f'  act {act} {cap}: {ttk:.0f}s vs {tgt}s target')
    else:
        print('\nall scored capstones within target')
    return 0


if __name__ == '__main__':
    sys.exit(main())
