#!/usr/bin/env python3
"""Model of player gear vs boss stats, per act, for the raid retune.

WHY THIS EXISTS
The pack's numbers were tuned by measuring one endgame profile and extrapolating.
That produced 240,000 HP bosses and a x16 gem multiplier - numbers so large that
they stopped meaning anything, and hid three separate mitigation layers stacking.

Everything here is measured, not assumed:
  * armour formula      taken = damage * a/(a+armor),  a = 10 + 4*sqrt(damage-20)
  * protection formula  1 - min(0.01*protPoints, 0.5)      (retuned this session)
  * affix reduction     ancient armour affixes measured at ~0.54 multiplier
  * melee output        ~1.95 DPS per point of attack_damage (measured)

TARGETS
  * an act's best gear kills that act's boss with 3-4 players in 90-180s
  * the same fight solo takes >8 minutes -> possible but miserable
  * a boss needs 5-8 hits to kill a player of that act
"""
import math

# --- measured constants -------------------------------------------------
# MEASURED IN A REAL FIGHT, act-2 gear vs the Ravager: 964 damage in 180s =
# 5.36 dps. Player hit was 8.0 (iron sword 6 + sharpness 2); Ravager armour 4
# gives armour_mult 0.714, so raw dps/AD = 5.36 / 0.714 / 8.0 = 0.94.
# The old 1.95 came from a bench measurement that counted something else and
# made every boss ~2x too tanky.
DPS_PER_AD   = 0.94
AFFIX_RED    = 0.54     # ancient armour affix damage reduction (measured 0.54)
PROT_PER_PT  = 0.01
PROT_CAP     = 0.50

def a_value(dmg):
    return 10.0 if dmg < 20 else 10.0 + 4.0 * math.sqrt(max(dmg - 20.0, 0.0))

def armour_mult(dmg, armor):
    a = a_value(dmg)
    return a / (a + armor)

def prot_mult(points):
    return 1.0 - min(PROT_PER_PT * points, PROT_CAP)

def damage_to_player(raw, armor, prot_points, affix=1.0):
    return raw * armour_mult(raw, armor) * prot_mult(prot_points) * affix

# --- expected gear per act ----------------------------------------------
# armour/hp/weapon are the realistic BEST a group has when they reach the act.
# prot = protection points (enchant level x 4 pieces). gem = total damage
# multiplier from sockets available at that act.
GEAR = {
    # armor/weapon are MEASURED (tools/gear_survey.py, weapon_sweep.py), not guessed.
    # Player values = measured-on-dummy minus the zombie's own base (2 armour, 3 attack).
    #   leather 7 | iron 15 | diamond 20 | netherite 20 (SAME as diamond)
    #   dark_metal 24 (born_in_chaos, already gated by act-2/3 mob drops) |
    #   cursium 28 (re-gated to act 5) | ignitium 32 | annihilator 31 (re-gated to
    #   act 7) | dragonsteel 34 | ebonlord 45
    # All 66 complete armour sets in the pack were measured to find these; the
    # ladder below is now every real rung, with no plateau.
    #   stone 5 | iron 6 | diamond 7 | wrought_axe 9 | netherite 8
    #   incinerator 14 | dragonsteel axe 30 | ebonlord blade 20 | soul_great_sword 13
    # Netherite is NOT an armour upgrade over diamond - both 20.
    # Dragonsteel was 30 player damage at act 7, which made group DPS jump
    # 67 -> 225 crossing into act 7 and left acts 8-9 with no upgrade at all.
    # Nerfed to 18 in config/iceandfire-common.toml (Dragonsteel Sword Base
    # Attack Strength 25 -> 13; axes derive from it), giving a smooth
    # 9 -> 14 -> 18 -> 20 ramp across acts 5-8.
    # Protection is MAXED (level 8 = 32 points) from act 5 onward - the owner's
    # rule. Below that it ramps, since players are still assembling a set.
    1: dict(armor=7,  hp=20, weapon=5,  prot=0,  gem=1.00, affix=1.00),
    2: dict(armor=15, hp=20, weapon=6,  prot=8,  gem=1.00, affix=1.00),
    3: dict(armor=20, hp=20, weapon=7,  prot=12, gem=1.08, affix=0.95),
    4: dict(armor=24, hp=22, weapon=9,  prot=16, gem=1.15, affix=0.90),
    5: dict(armor=28, hp=24, weapon=9,  prot=32, gem=1.28, affix=0.85),
    6: dict(armor=32, hp=26, weapon=14, prot=32, gem=1.45, affix=0.78),
    7: dict(armor=34, hp=30, weapon=18, prot=32, gem=1.65, affix=0.70),  # dragonsteel 34 / annihilator 33
    8: dict(armor=45, hp=34, weapon=20, prot=32, gem=1.85, affix=0.62),
    9: dict(armor=45, hp=40, weapon=20, prot=32, gem=2.00, affix=0.54),
}

# Boss armour. Kept modest on purpose: the armour formula is weakest against big
# hits, so piling armour on a boss mostly punishes the low-damage act it belongs
# to. Measured against this gear curve these cost a player 30-50% of their raw
# output; the HP targets below are solved AFTER that reduction, so TTK is honest.
BOSS_ARMOR = {1: 2, 2: 4, 3: 6, 4: 8, 5: 10, 6: 13, 7: 16, 8: 20, 9: 24}

# Sharpness level a group realistically has at each act. Vanilla bonus is
# 0.5*level + 0.5, applied at HIT TIME - it is NOT in the attack_damage attribute,
# which is why a survey that only reads attributes misses it entirely.
# Conditional enchants (smite/bane/impaling) are +2.5 PER LEVEL against one mob
# type; at the pack's original max of 10 that was +25, dwarfing the weapon itself.
# Capped to 5 in config/apotheosis/enchantments.cfg. Not modelled here because it
# only applies to some bosses - treat it as headroom, not baseline.
# Enchanting is reachable EARLY in this pack - a table, lapis and levels are act-2/3
# content, not endgame. So sharpness effectively maxes around act 3-4, and the
# early acts are far stronger than a slow ramp would suggest. Modelling it as a
# late ramp under-powered acts 3-5 and made their bosses too soft.
SHARPNESS = {1: 0, 2: 3, 3: 7, 4: 9, 5: 9, 6: 9, 7: 9, 8: 9, 9: 9}

def sharp_bonus(act):
    lvl = SHARPNESS[act]
    return 0.0 if lvl <= 0 else 0.5 * lvl + 0.5

def player_dps(act):
    """Effective DPS AFTER the boss's own armour - the number that sets TTK."""
    g = GEAR[act]
    # gems multiply the ATTRIBUTE; sharpness is added afterwards at hit time.
    ad = g['weapon'] * g['gem'] + sharp_bonus(act)
    return ad * DPS_PER_AD * armour_mult(ad, BOSS_ARMOR[act])

def player_dps_raw(act):
    g = GEAR[act]
    return g['weapon'] * g['gem'] * DPS_PER_AD

def player_hit(act):
    """Raw damage of one swing: gems multiply the attribute, sharpness adds after."""
    g = GEAR[act]
    return g['weapon'] * g['gem'] + sharp_bonus(act)

def pvp(attacker_act, victim_act):
    """Damage one player lands on another, through all three mitigation layers."""
    v = GEAR[victim_act]
    return damage_to_player(player_hit(attacker_act), v['armor'], v['prot'], v['affix'])

# Raid size the pack is tuned for. The owner runs 5-person groups.
GROUP_SIZE = 5.0

def solve_boss(act, target_group_seconds, group=GROUP_SIZE, boss_armor=None):
    """Boss HP that a `group` of act-appropriate players kills in the target time."""
    return player_dps(act) * group * target_group_seconds

def boss_damage_for_hits(act, hits):
    """Raw boss damage so it takes `hits` to kill an act-appropriate player."""
    g = GEAR[act]
    lo, hi = 1.0, 5000.0
    for _ in range(200):
        mid = (lo + hi) / 2
        per = damage_to_player(mid, g['armor'], g['prot'], g['affix'])
        if per * hits < g['hp']:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

# Fight length a 3-4 group should need. Early acts are short and punchy; the
# late acts are real raids. Act 9 is not solved for - the Ender Dragon is pinned
# at 50k by design decision, and everything else is scaled beneath it.
FIGHT_SECONDS = {1: 45, 2: 60, 3: 70, 4: 80, 5: 95, 6: 110, 7: 130, 8: 155}
DRAGON_HP = 50_000
# Owner's target: a boss should take 4-7 hits to drop an act-appropriate player.
# 5.5 is the midpoint we solve for, which leaves headroom on both sides.
HITS_TO_KILL = 5.5

# Bosses whose attacks BYPASS ARMOUR (attributeslib fire/cold/bleed are in the
# `bypasses_armor` damage tag) hit far harder than the armour term predicts.
# MEASURED: Ignis averaged 4.04 per hit against a 56.5-armour player where the
# model said 1.75 - a 2.3x real-world factor. Its damageset has to come down by
# the same factor or an act-6 player dies in under 4 hits.
REAL_DAMAGE_FACTOR = {
    'cataclysm:ignis': 2.3,      # measured
}

def boss_table():
    out = {}
    for act in range(1, 10):
        dps = player_dps(act)
        if act == 9:
            hp = DRAGON_HP
        else:
            hp = round(solve_boss(act, FIGHT_SECONDS[act]) / 250) * 250
        out[act] = dict(hp=hp, dmg=round(boss_damage_for_hits(act, HITS_TO_KILL)),
                        dps=dps, grp=dps * GROUP_SIZE)
    return out

if __name__ == '__main__':
    t = boss_table()
    print(f"{'act':>3}{'dps/plr':>9}{'grp dps':>9}{'boss HP':>9}{'solo':>8}"
          f"{'3.5 grp':>9}{'boss dmg':>10}{'per hit':>9}{'hits':>6}")
    for act in range(1, 10):
        g, b = GEAR[act], t[act]
        per = damage_to_player(b['dmg'], g['armor'], g['prot'], g['affix'])
        solo = b['hp'] / b['dps']
        grp  = b['hp'] / b['grp']
        print(f"{act:>3}{b['dps']:>9.1f}{b['grp']:>9.1f}{b['hp']:>9,}"
              f"{solo/60:>7.1f}m{grp:>8.0f}s{b['dmg']:>10}{per:>9.1f}{g['hp']/per:>6.1f}")
