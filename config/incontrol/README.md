# Distance-based difficulty — how spawn.json is built

In Control's rule files take **no comments**. An unrecognised key (including
`_comment`) makes `GenericAttributeMapFactory` log an error and return false,
rejecting that rule — the file still loads, the rule just never fires. So the
reasoning lives here. Keep this in step with `spawn.json`.

Replaces Mine and Slash and PMMO, both removed 2026-07-28. Difficulty keys off
**distance from world spawn**: it cannot be outrun, ignores gear and levels, and
is legible to the player — further out is harder. It also removes the incentive
to camp spawn, since rewards there are capped.

## Bands

| dimension | distance | health | damage | armor |
|---|---|---|---|---|
| overworld | 0–800 | — | — | — |
| overworld | 800–3000 | ×1.5 | ×1.2 | +2 |
| overworld | 3000–8000 | ×2.5 | ×1.5 | +5 |
| overworld | 8000+ | ×4.0 | ×1.75 | +8 |
| nether | 0–100 | — | — | — |
| nether | 100–375 | ×1.5 | ×1.2 | +2 |
| nether | 375–1000 | ×2.5 | ×1.5 | +5 |
| nether | 1000+ | ×4.0 | ×1.75 | +8 |
| end | any | ×8.0 | ×2.5 | +14 |
| ender dragon | any | ×5000 → **1,000,000 HP** | ×3.0 | +40, KB-immune |

**Do not use `armortoughness*` in this pack.** ApothicAttributes replaces the
vanilla armor formula with `a / (a + armor)`, where
`a = if(damage < 20, 10, 10 + (damage - 20) / 2)` — see `config/attributeslib.cfg`.
Toughness does not appear in it, so those keys do nothing. Armor still works and
has no cap, but gives *less* reduction against bigger hits: at armor 40 a
50-damage swing is reduced ~62% while a 200-damage swing is reduced only ~29%.
That deliberately rewards heavy hitters over chip damage.

There is also **no max-health ceiling** — vanilla caps `max_health` at 1024 (which
is exactly why Ignis sat at 1024), but ApothicAttributes lifts it; 2,000,000 was
set and read back cleanly.

### Calibrating the dragon

1,000,000 HP is a **first pass, not a measured value.** It assumes ~6,000 combined
DPS from 8–9 endgame players at roughly 50% damage uptime, which with armor gives
a ~10 minute fight. The only hard DPS datum we have is **51.5 DPS at level 45 in
mid gear**; endgame in this pack could plausibly be anywhere from 200 to 2000 DPS
per player, a 10× spread that reasoning cannot close.

To calibrate: park a high-HP dummy, have the group attack for 30 seconds, divide.
Then set `healthmultiply = (target_seconds x group_dps x uptime x armor_factor) / 200`.
It is one number in one file.

**Known regression:** at 1,000,000 HP the End Crystals' healing is negligible, so
destroying them stops mattering and the fight loses its one real mechanic. If that
matters more than raw length, lower the health and raise the pressure instead —
the ×8 End mobs in the arena are the better difficulty lever.

**The Nether thresholds are the overworld ones divided by 8**, because Nether
coordinates are 1:8. 1000 blocks travelled in the Nether is 8000 overworld
blocks, so the bands line up: wherever you stand, the difficulty matches the
overworld position you would emerge at. This is deliberate and is warned about in
the Act 6 entry quest — travel far in the Nether, build a portal, and you exit
into overworld terrain far deadlier than the gear you got there.

`minspawndist` is measured with `ServerLevel.getSharedSpawnPos()`, which is the
**overworld spawn point in all dimensions** (all dimensions share one
`WorldData`). So in the Nether it is effectively distance from Nether origin,
which is exactly what the 1:8 mapping needs.

The End has no distance term — it is endgame by definition, and the dragon is
gated harder still so it cannot be rushed on early gear.

## Rules that are easy to get wrong

**Order matters — most specific and outermost first.** `spawn.json` stops at the
**first matching rule** (`loot.json` is the opposite: every match runs). A mob at
9000 also satisfies `minspawndist: 800`, so the inner band must come last or it
would swallow everything. Same reason the `ender_dragon` rule precedes the
general End rule. There is deliberately no `maxspawndist` — ordering bounds the
bands.

**`when: "onjoin"` is deliberate and was measured.** It maps to Forge's
`EntityJoinLevelEvent`, firing for natural spawns, spawners, worldgen, `/summon`,
and anything KubeJS spawns. The obvious worry is that it also fires when an
existing mob reloads from disk, compounding the multiplier every restart. It does
**not**: In Control's `healthmultiply` computes off the mob's default attribute,
so re-running is idempotent — verified across a restart, a skeleton went 20 → 40
and stayed 40.

The same is **not** true of KubeJS. `EntityEvents.spawned` re-fires for
disk-loaded entities (confirmed: fire count 2 after one restart), so any KubeJS
attribute write needs a `persistentData` guard or it compounds — the same runaway
shape as PMMO's `1.104^level`.

`when: "finalize"` does **not** fire for `/summon`, so it is untested and unused.

`hostile: true` resolves to `instanceof net.minecraft.world.entity.monster.Enemy`.

## Verified in game

Bands measured on the test server with world spawn pinned to 0,-20,0 and a
temporary `healthmultiply: 9.0` catch-all appended to prove "no band matched":

| distance | expected | measured |
|---|---|---|
| 100 | catch-all (safe zone) | 180 ✓ |
| 1000 | ×1.5 → 30 | 30 ✓ |
| 4000 | ×2.5 → 50 | 50 ✓ |
| 9000 | ×4.0 → 80 | 80 ✓ |

`minspawndist` is **plain blocks**, as documented. (A bytecode read suggested it
compared against squared distance; that was wrong — the threshold is squared at
the call site. Measurement settled it.)

When testing, force-load the target chunk *and* distinguish "entity not found"
from "unscaled" — a shell fallback that prints a default on grep failure will
report a missing entity as an unscaled one and send you chasing a phantom bug.

## Tuning

`/incontrol reload` re-reads these files but **requires a player context** — it
cannot run over RCON with nobody online. Restarting also works.

Damage is the dial to watch. Players are on vanilla-scale health now that Mine
and Slash is gone, so every band's damage multiplier sits well below its health
multiplier. A boss with 1024 HP and no damage output died in 81 seconds and
threatened nobody: health lengthens a fight, damage makes it dangerous — and
damage is also what causes one-shots.

Caveat on the dragon: `damagemultiply` scales the `attack_damage` attribute.
Parts of the Ender Dragon's kit (breath, charge) are hardcoded and will not
respond to it. Health, armor and toughness do apply, so the gate holds, but the
dragon's damage will scale less than the number suggests.

## Not done here

Which *species* spawn per band is a separate layer. In Control cannot do it:
`spawner.json` is the only mob-adding file and its condition parser shares zero
keys with the others — no `minspawndist` at all. Options are `result: "deny"`
bands here, or true substitution in KubeJS via `EntityEvents.checkSpawn` (which
is registered `.hasResult()`, so `event.cancel()` works).
