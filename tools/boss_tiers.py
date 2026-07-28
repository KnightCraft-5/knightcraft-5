#!/usr/bin/env python3
"""Generate per-boss In Control rules, tiered by act.

WHY BOSSES NEED THEIR OWN RULES
The distance bands in config/incontrol/spawn.json scale by distance from world
spawn. That is right for ambient mobs and wrong for bosses: a boss lives inside a
structure, and that structure generates wherever worldgen put it. An Act 8 boss
that happens to spawn 500 blocks from spawn would sit in the safe zone forever.

In Control stops at the FIRST matching rule, so a `mob`-keyed rule placed above
the band rules wins and the bands never apply. That is the mechanism already used
for the ender dragon.

WHY THE NUMBERS LOOK LIKE THIS
Measured on the test server, all against a dummy carrying the player's profile:
  * a suited endgame player is 340 armour / 340 HP / 224 attack damage
  * melee output tracks ~1.9-2.0 DPS per point of attack damage
  * the pack's armour formula is a/(a+armor) with a = 10 + 4*sqrt(damage-20),
    so a boss's armour value matters more against small hits than large ones
  * band 4 lands ~306 raw on a player = ~57 damage = ~6 hits to kill

Cataclysm's per-boss `DamageCap` (20-22) has been raised to 100000 in
config/cataclysm.toml. Until that was done, boss health was a meaningless lever:
a player with 224 attack damage was landing ~5 per swing regardless of gear, so
a 300k-HP boss would have taken 60,000 swings. Do not re-lower those caps without
re-tuning every health value here.
"""

# act -> (boss health, boss attack damage, boss armour)
#
# Health is sized so a group of the act's expected gear tier kills it in 2-5
# minutes. Attack is sized so it kills a player of that tier in ~6 hits, matching
# the ambient band calibration. Armour is kept modest: it multiplies effective
# health, and the formula makes it weakest exactly when players hit hardest.
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

# Mini-bosses sit between acts: roughly a third of the capstone's health and
# three quarters of its damage, so they threaten without being a wall.
MINIBOSS_HEALTH = 0.33
MINIBOSS_DAMAGE = 0.75


def rule(entity, act, miniboss=False):
    """One In Control spawn.json rule for a single boss entity.

    healthset / damageset (not multiply) because these are absolute targets -
    a multiplier would inherit whatever the mod's own config happens to say and
    drift the moment that changes.
    """
    t = ACT_TIERS[act]
    hp = t["health"] * (MINIBOSS_HEALTH if miniboss else 1.0)
    dmg = t["damage"] * (MINIBOSS_DAMAGE if miniboss else 1.0)
    return {
        "mob": entity,
        "when": "onjoin",
        "result": "default",
        "healthset": round(hp),
        "damageset": round(dmg),
        "armorset": t["armor"],
        "knockbackresistanceset": 1.0,
    }


if __name__ == "__main__":
    print(f"{'act':>4} {'health':>9} {'damage':>7} {'armour':>7}   "
          f"{'suited-player hits to kill it':>30}")
    for act, t in ACT_TIERS.items():
        # a suited player deals ~224 attack damage; armour formula applied
        import math
        a = 10 + 4 * math.sqrt(max(224 - 20, 0))
        through = 224 * a / (a + t["armor"])
        print(f"{act:>4} {t['health']:>9,} {t['damage']:>7} {t['armor']:>7}   "
              f"{t['health']/through:>26,.0f} swings")
