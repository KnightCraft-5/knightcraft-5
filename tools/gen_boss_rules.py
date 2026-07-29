#!/usr/bin/env python3
"""Generate per-boss In Control rules and splice them into spawn.json.

Bosses get their OWN rules instead of inheriting the distance bands, because a
boss lives inside a structure and that structure generates wherever worldgen put
it - an Act 8 boss spawning 500 blocks from world spawn would otherwise sit in
the safe zone forever. In Control stops at the first matching rule, so `mob`-keyed
rules placed ABOVE the band rules win and the bands never apply.

Every id is verified by summoning it on the live server before it is written. A
wrong entity id is not an error in In Control - the rule simply never fires, and
the config looks perfectly healthy.

Run:  tools/gen_boss_rules.py [--verify-only]
"""
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path.home() / "mc-test-server"))
from rcon import Rcon  # noqa: E402

INSTANCE = pathlib.Path(__file__).resolve().parent.parent
SPAWN = INSTANCE / "config" / "incontrol" / "spawn.json"

# --- ambient (non-boss) mobs, one distance ring per act ---------------------
# ANCHORED BY THE OWNER: the reference act-1 ring mob is 40 hp and 9 attack damage.
# Every ring from act 2 out is derived from that anchor so the experience stays
# constant as you travel out - a ring's trash kills that act's player in the same
# number of hits, and takes the same time to kill with that act's gear.
#
# ACT 1 ITSELF IS NOT SCALED. Owner's call 2026-07-29: the ring nearest spawn is a
# plain vanilla zone, so a new player is never scaled on before they have gear. The
# anchor above still sets the shape of every OUTER ring; it just no longer describes
# act 1. That puts a deliberate step at the act 1 -> act 2 boundary (3 -> 14 damage),
# which is the price of a genuinely safe starting zone and is intended.
#
# DAMAGE IS FLAT (`damageadd`), NOT A MULTIPLIER. Measured: a suited player at 320
# armour mitigates ~98% of a 20-damage hit, so multiplying a zombie's base 3 can
# never threaten them while the same multiplier on a boss's base 14 is lethal.
# Flat addition lands every mob in a predictable band. Health stays a MULTIPLIER so
# species variety survives - a witch should still be tougher than a zombie.
#
# Baselines are the vanilla zombie: 20 hp, 3 attack damage, 2 armour. Tougher
# species scale above the ring number, which is intended.
ZOMBIE_HP, ZOMBIE_DMG, ZOMBIE_ARMOR = 20.0, 3.0, 2.0
# Walked down in play: 50/12 -> 40/9 -> 30/6. Acts 2-9 derive from this; act 1 is
# pinned to vanilla by FLAT_ACT1, so this only moves the outer rings now. At 30/6 a
# player survives ~5.7 hits per ring instead of ~3.8, and the act 1 -> act 2 step
# softens from 3 -> 14 damage to 3 -> 10. Expected to keep moving as we play.
ANCHOR_HP, ANCHOR_DMG = 30.0, 6.0
# Act 1 emits healthmultiply 1.0 / damageadd 0 / armoradd 0 - a rule that changes
# nothing. It is still emitted rather than omitted so the ring is explicit in
# spawn.json and In Control stops there instead of falling through.
FLAT_ACT1 = True

# Ring radius in blocks from world spawn, per act. In Control stops at the FIRST
# matching rule, so these are emitted outermost-first. Nether uses 1/8 of each
# threshold: getSharedSpawnPos() returns the OVERWORLD spawn in every dimension,
# so nether distance is measured from nether origin and 1:8 keeps the rings aligned.
RING_DIST = {1: 2000, 2: 2950, 3: 4250, 4: 5750, 5: 7750,
             6: 10250, 7: 13250, 8: 16750, 9: 20750}
NETHER_DIV = 8
TRASH_ARMOR = {a: max(0, a - 1) for a in range(1, 10)}

# act -> (health, damage, armour). See tools/boss_tiers.py for the derivation.
ACT_TIERS = {
    1: dict(health=  1000, damage=  6, armor= 2),
    2: dict(health=  1500, damage= 10, armor= 4),
    3: dict(health=  2500, damage= 13, armor= 6),
    4: dict(health=  3250, damage= 18, armor= 8),
    5: dict(health=  3750, damage= 22, armor=10),
    6: dict(health=  7750, damage= 24, armor=13),
    7: dict(health= 13000, damage= 29, armor=16),
    8: dict(health= 18000, damage= 39, armor=20),
    9: dict(health= 50000, damage= 48, armor=24),   # FINAL boss - Ender Dragon, pinned at 50k
}
MINI_HP, MINI_DMG = 0.33, 0.75

# WINDOW-GATED BOSSES.
#
# These are not DPS checks. The Ferrous Wroughtnaut is invulnerable until it
# commits to its top-down swing; only then can it be hit from behind. Damage
# output is therefore capped by the BOSS's attack cycle, not by the player's
# weapon - four players in a group all hit during the same window, so group
# damage scales, but a solo player is limited no matter how geared they are.
#
# Measured live with a player who knew the mechanic and attacked from behind:
# 26 damage in 75 seconds = 0.4 dps. At the model's 4,750 HP that is a 3-HOUR
# solo kill. The whole ACT_TIERS table assumes HP is a time-to-kill lever, and
# for these bosses that assumption simply does not hold.
#
# CALIBRATED FROM A LIVE FIGHT (player attacking from behind, which is the
# intended vulnerability window):
#   active dps = 1.5  (37 damage in 25s of real fighting)
#   at 0.08x -> 380 HP -> 253s solo (~4.2 min), ~72s for a 3.5-player group
#   act-4 targets are 4.8 min solo / 82s group, so 0.08 is right.
# NOTE the first sample read 0.4 dps because it counted positioning time; only
# measure from FIRST DAMAGE or a window-gated boss looks 4x worse than it is.
# Bosses whose attacks BYPASS ARMOUR, so `damageset` lands almost unfiltered.
# MEASURED: Ignis at damageset 23 hit an act-6 player (32 armour, prot 24) for
# avg 6.59 and a max of 13.91 - 70% of a 20 hp player in ONE blow, killing in
# 3.0 hits against a 4-7 target. Its fire is minecraft/attributeslib fire damage,
# which is in the `bypasses_armor` tag, so armour contributes nothing and only
# Protection applies. The damage number has to come down to compensate.
BYPASS_DAMAGE = {
    # 23 raw measured at avg 6.59/hit = 3.0 hits to kill, below the 4-7 target.
    # 0.55 (-> 13) fixed that but gutted it; a fire boss SHOULD be frightening.
    # 0.78 -> 18 lands ~4 hits: still the harsh end of the band, still capable of
    # taking most of a health bar in one blow, but no longer a 3-hit delete.
    'cataclysm:ignis': 0.78,

    # DRAGONS ARE MEASURED, not inferred. Their two attacks differ wildly:
    #   fire breath  = many small ticks, 1.65 each (69 ticks in 40s)
    #   physical bite= 14.76 in ONE hit at damageset 23
    # The bite is what kills - 1.6 hits on a 24 hp act-7 player - and it lands ~3x
    # harder than armour 34 + prot 32 should allow. 0.233 puts the bite at ~4.4,
    # i.e. 5.5 hits, and softens the breath ticks with it. One damageset drives
    # both attacks, so this is the trade.
    #
    # Same mechanism, not yet individually measured. All of these deal fire, cold
    # or freeze damage, which sits in the `bypasses_armor` tag, so their damageset
    # lands almost unfiltered exactly as Ignis's did. Applying Ignis's measured
    # factor is an inference, not a measurement - but leaving them unadjusted is
    # KNOWN wrong, since armour contributes nothing against them.
    'cataclysm:ignited_revenant':       0.78,
    'cataclysm:ignited_berserker':      0.78,
    'cataclysm:netherite_monstrosity':  0.78,
    'threateningly_mobs:the_inferno':   0.78,
    'mowziesmobs:frostmaw':             0.78,
}

WINDOW_BOSSES = {
    # The Ferrous Wroughtnaut is a SPECIAL CASE and a PACING problem, not just a
    # tuning one. It is invulnerable until it commits to its top-down swing, so the
    # fight is mostly standing around waiting for permission to deal damage.
    # Measured 1.5 dps in endgame gear, ~0.4 in act-4 gear.
    #
    # More health does not make it harder, it makes it LONGER and more boring -
    # the owner's words were "wrought is so boring". So it is deliberately SHORT:
    # the mechanic still has to be learned and executed, but you do it a handful
    # of times instead of thirty. 250 hp is ~3 min solo at 1.5 dps and under a
    # minute for a group, where a group all punishes the same window.
    # ONE PLAYER AT A TIME: the opening is behind it during its swing, so a group
    # cannot stack damage the way they can on every other boss. Its HP is therefore
    # NOT scaled up for a 5-person raid - it stays sized for a single attacker.
    'mowziesmobs:ferrous_wroughtnaut': 0.0777,

    # The Amethyst Crab burrows, but MEASURED 4.94 dps against a normal act-3 rate
    # of 6.8 - the gate costs ~27%, not 80%. Nothing like the Wroughtnaut.
    'cataclysm:amethyst_crab':         0.730,

    # THE HARBINGER HEALS: life_steal 5.0 per hit it lands, auto_heal 2.0 passive.
    # MEASURED in melee: -0.31 dps - it out-heals a melee player entirely, so this
    # is a RANGED-ONLY fight by design. MEASURED with an endgame bow: 34.03 dps.
    # An earlier 7.08 reading was a bad sample (the player was not shooting) and
    # produced a 5,501 hp value that a bow group would have deleted in 32s.
    'cataclysm:the_harbinger':         1.4722,


    # STAGE-3 fire dragon MEASURED at 4.12 dps against an act-7 rate of 20.0 -
    # they fly and are hard to reach, so effective dps is ~20% of nominal. At the
    # untested 13,000 that was 52 MINUTES solo / 10.5 min even with 5 players.

    # Ignis parries via `blockingProgress` and it is SEVERE - as bad as the
    # Wroughtnaut. MEASURED 1.01 dps against an act-6 rate of 14.2, a 93% cut.
    # At the untested 5,500 tier value that was a NINETY MINUTE solo fight.
    # 0.0709 -> 390 hp -> 6.4 min solo, 110s for a 3.5 group (target 111s).
    'cataclysm:ignis':                 0.0709,

    # Frostmaw SLEEPS, and asleep it takes full damage. Two runs, same armour:
    # 20.49 dps with the boss mostly asleep, 2.40 dps once awake - an 8.5x gap for
    # a 7% weapon difference, so it is the sleep state, not the gear. The awake
    # rate is what a real fight is, and 900 hp leaves headroom for the free damage
    # landed before it wakes. (2500 hp would have been a 17-minute solo fight.)
    'mowziesmobs:frostmaw':            0.360,
}
GUARD_BOSSES = WINDOW_BOSSES

# NOTE: the three Ice and Fire dragons are deliberately ABSENT. In Control's
# healthset/damageset is a flat override, which collapsed Ice and Fire's own
# stage scaling - a hatchling and a stage-5 adult both came out at 13,000 hp.
# They are tuned in config/iceandfire-common.toml instead, where "Dragon Health"
# and "Dragon Attack Damage" are the stage-5 MAXIMA and the mod scales down by age.
#
# (entity id, act, is_miniboss)
BOSSES = [
    # --- Act 2: the road ---------------------------------------------------
    ("minecraft:ravager",                             2, False),
    ("born_in_chaos_v1:lord_pumpkinhead",             2, False),   # 666hp, real bossbar
    ("born_in_chaos_v1:lord_pumpkinhead_withouta_horse", 2, False),# phase 2
    ("born_in_chaos_v1:sir_the_headless",             2, True),
    ("born_in_chaos_v1:supreme_bonescaller",          2, True),
    ("born_in_chaos_v1:supreme_bonescaller_not_despawn", 2, True), # structure copy
    ("born_in_chaos_v1:skeleton_thrasher",            2, True),
    ("born_in_chaos_v1:skeleton_thrasher_not_despawn",2, True),
    ("born_in_chaos_v1:scarlet_persecutor",           2, True),

    # --- Act 3: into the deep ----------------------------------------------
    ("born_in_chaos_v1:nightmare_stalker",            3, True),
    ("born_in_chaos_v1:mother_spider",                3, True),
    ("born_in_chaos_v1:lifestealer_true_form",        3, True),
    ("born_in_chaos_v1:fallen_chaos_knight",          3, True),
    ("cataclysm:amethyst_crab",                       3, False),  # act 3 CAPSTONE (quest book crowns it)
    ("cataclysm:kobolediator",                        3, True),
    ("iceandfire:troll",                              3, True),

    # --- Act 4: the hunt ---------------------------------------------------
    ("mowziesmobs:ferrous_wroughtnaut",               4, False),
    ("cataclysm:the_prowler",                         4, True),
    ("legendary_monsters:overgrown_colossus",         4, True),
    ("legendary_monsters:beheaded_knight",            4, True),
    ("legendary_monsters:resurrected_knight",         4, True),
    ("born_in_chaos_v1:lord_the_headless",            4, True),
    ("wom:saulomonk",                                 4, True),

    # --- Act 5: the arena --------------------------------------------------
    ("mowziesmobs:frostmaw",                          5, False),
    ("cataclysm:coralssus",                           5, True),
    ("cataclysm:coral_golem",                         5, True),
    ("cataclysm:wadjet",                              5, True),
    ("iceandfire:myrmex_queen",                       5, False),
    ("legendary_monsters:frostbitten_golem",          5, True),
    ("legendary_monsters:ancient_guardian",           5, True),
    ("legendary_monsters:skeletosaurus",              5, True),
    ("legendary_monsters:dune_sentinel",              5, True),
    ("threateningly_mobs:the_regalhart",              5, True),
    ("born_in_chaos_v1:krampus",                      5, True),

    # --- Act 6: the nether -------------------------------------------------
    ("cataclysm:ignis",                               6, False),
    ("cataclysm:netherite_monstrosity",               6, False),
    ("cataclysm:ancient_remnant",                     6, False),
    ("mowziesmobs:umvuthi",                           6, False),
    ("cataclysm:ignited_revenant",                    6, True),
    ("cataclysm:ignited_berserker",                   6, True),
    ("cataclysm:aptrgangr",                           6, True),
    ("legendary_monsters:lava_eater",                 6, True),
    ("legendary_monsters:warped_fungussus",           6, True),
    ("legendary_monsters:withered_abomination",       6, True),
    ("threateningly_mobs:the_inferno",                6, True),
    ("born_in_chaos_v1:spiritof_chaos",               6, True),

    # --- Act 7: the dragon -------------------------------------------------
    ("iceandfire:hydra",                              7, False),
    ("cataclysm:the_leviathan",                       7, False),
    ("cataclysm:scylla",                              7, False),
    ("mowziesmobs:sculptor",                          7, False),
    ("alexsmobs:void_worm",                           7, False),
    ("cataclysm:clawdian",                            7, True),
    ("iceandfire:cyclops",                            7, True),
    ("iceandfire:gorgon",                             7, True),
    ("iceandfire:sea_serpent",                        7, True),
    ("iceandfire:dread_lich",                         7, True),
    ("threateningly_mobs:terra_dragon_re",            7, True),
    ("threateningly_mobs:ice_brood_mother",           7, True),
    ("threateningly_mobs:hydra",                      7, True),
    ("alexsmobs:cachalot_whale",                      7, True),
    ("alexsmobs:warped_mosco",                        7, True),

    # --- Act 8: the ancient ------------------------------------------------
    ("cataclysm:the_harbinger",                       8, False),
    ("cataclysm:ender_guardian",                      8, False),
    ("cataclysm:maledictus",                          8, False),
    ("legendary_monsters:the_obliterator",            8, False),
    ("legendary_monsters:posessed_paladin",           8, False),   # note: one 's'
    ("legendary_monsters:cloud_golem",                8, False),   # displays "Cumulonimbus"
    ("threateningly_mobs:hypocritical_saint",         8, False),
    ("cataclysm:ender_golem",                         8, True),
    ("legendary_monsters:endersent",                  8, True),
    ("legendary_monsters:shulker_mimic",              8, True),
    ("legendary_monsters:annihilation_pursuer",       8, True),

    # --- Tier 9: the end ---------------------------------------------------
    ("minecraft:ender_dragon",                        9, False),
]


def ambient_stats():
    """Per-act ambient mob stats, derived from the owner's act-1 anchor.

    Two invariants are held constant across every ring, so the world feels the same
    however far out you are:
      * a ring's trash kills that act's player in the same number of hits as an
        act-1 mob kills an act-1 player
      * a ring's trash takes the same time to kill with that act's own gear
    """
    from balance_model import GEAR, DPS_PER_AD, armour_mult, damage_to_player

    g1 = GEAR[1]
    hits = g1["hp"] / damage_to_player(ANCHOR_DMG, g1["armor"], g1["prot"], g1["affix"])
    ad1 = g1["weapon"] * g1["gem"]
    ttk = ANCHOR_HP / (ad1 * DPS_PER_AD * armour_mult(ad1, TRASH_ARMOR[1]))

    out = {}
    for act in range(1, 10):
        g = GEAR[act]
        armor = TRASH_ARMOR[act]
        # raw damage that kills this act's player in the same `hits`
        lo, hi = 1.0, 800.0
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if g["hp"] / damage_to_player(mid, g["armor"], g["prot"], g["affix"]) > hits:
                lo = mid
            else:
                hi = mid
        dmg = round((lo + hi) / 2.0)
        ad = g["weapon"] * g["gem"]
        hp = round(ad * DPS_PER_AD * armour_mult(ad, armor) * ttk / 5.0) * 5
        out[act] = dict(hp=float(hp), dmg=float(dmg), armor=armor)
    # Act 1 is the safe zone: vanilla stats exactly, so its rule is a no-op. The
    # anchor is still what acts 2-9 above were derived from - it sets their shape,
    # it just is not what act 1 ships as.
    if FLAT_ACT1:
        out[1] = dict(hp=ZOMBIE_HP, dmg=ZOMBIE_DMG, armor=0)
    else:
        out[1]["hp"], out[1]["dmg"] = ANCHOR_HP, ANCHOR_DMG
    return out


def make_bands():
    """Distance-ring rules for ordinary hostiles, outermost first.

    In Control stops at the first matching rule, so ordering matters and each rule
    must fully state its own values - they do not inherit from the ring inside them.
    An unknown key silently rejects the single rule it appears on with no log line,
    so nothing here may carry a comment field.
    """
    stats = ambient_stats()
    bands = []
    end = stats[9]
    bands.append({"dimension": "minecraft:the_end", "hostile": True, "when": "onjoin",
                  "result": "default",
                  "healthmultiply": round(end["hp"] / ZOMBIE_HP, 2),
                  "damageadd": int(end["dmg"] - ZOMBIE_DMG),
                  "armoradd": int(end["armor"])})
    for dim, div in (("minecraft:overworld", 1), ("minecraft:the_nether", NETHER_DIV)):
        for act in sorted(RING_DIST, reverse=True):
            st = stats[act]
            bands.append({"dimension": dim, "hostile": True,
                          "minspawndist": max(1, RING_DIST[act] // div),
                          "when": "onjoin", "result": "default",
                          "healthmultiply": round(st["hp"] / ZOMBIE_HP, 2),
                          "damageadd": int(st["dmg"] - ZOMBIE_DMG),
                          "armoradd": int(st["armor"])})
    return bands


def make_rule(entity, act, mini):
    t = ACT_TIERS[act]
    return {
        "mob": entity,
        "when": "onjoin",
        "result": "default",
        # SET, not multiply: these are absolute targets. A multiplier would
        # inherit whatever the mod's own config says and drift silently the
        # moment that changes - and Cataclysm's config is exactly where the
        # damage caps were hiding.
        "healthset": round(t["health"] * (MINI_HP if mini else 1.0)
                           * GUARD_BOSSES.get(entity, 1.0)),
        "damageset": round(t["damage"] * (MINI_DMG if mini else 1.0)
                           * BYPASS_DAMAGE.get(entity, 1.0)),
        "armorset": t["armor"],
        "knockbackresistanceset": 1.0,
    }


def main():
    r = Rcon(timeout=25).login()
    good, bad = [], []
    for entity, act, mini in BOSSES:
        out = r.cmd(f"execute in minecraft:overworld run summon {entity} 0 -300 0")
        if "Summoned" in out:
            good.append((entity, act, mini))
            r.cmd(f"kill @e[type={entity}]")
        else:
            bad.append((entity, out.strip()[:60]))
        time.sleep(0.05)

    print(f"verified {len(good)} boss ids, {len(bad)} invalid")
    for e, why in bad:
        print(f"  DEAD ID  {e:44} {why}")
    if "--verify-only" in sys.argv:
        return 0 if not bad else 1

    bands = make_bands()
    boss_rules = [make_rule(e, a, m) for e, a, m in sorted(good, key=lambda x: (-x[1], x[0]))]
    SPAWN.write_text(json.dumps(boss_rules + bands, indent=2) + "\n")
    print(f"\nwrote {len(boss_rules)} boss rules above {len(bands)} band rules")
    print("\nambient rings (vanilla zombie baseline):")
    for act, st in sorted(ambient_stats().items()):
        print(f"  act {act}  r>={RING_DIST[act]:>6}  {st['hp']:>5.0f} hp  "
              f"{st['dmg']:>4.0f} dmg  armour {st['armor']}")
    for e, a, m in sorted(good, key=lambda x: (-x[1], x[0])):
        t = ACT_TIERS[a]
        hp = round(t['health'] * (MINI_HP if m else 1.0))
        print(f"  act {a}{'  mini' if m else '      '} {e:44} {hp:>8,} hp")
    return 0


if __name__ == "__main__":
    sys.exit(main())
