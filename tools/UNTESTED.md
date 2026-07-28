# Things that cannot be verified headlessly

Everything here has been implemented and loads without error, but **cannot be
proven correct over RCON alone**. Each needs a player in game. Ordered by risk:
the first group can silently break progression, the last group is cosmetic.

## A. Blocks progression if wrong

| # | What | How to test | Expected |
|---|---|---|---|
| A1 | Gem crafting at each bench | Craft one gem per rarity at its table | common/uncommon on Basic 3x3, rare/epic on Advanced 5x5, mythic on Elite 7x7, ancient on Ultimate 9x9 |
| A2 | Wrong bench is refused | Try an ancient recipe on the Elite table | must not craft — EC `tier` is an exact match |
| A3 | Gem variant discrimination | Put 3 **splendor** gems into an **endersurge** upgrade | must NOT craft. `forge:partial_nbt` tested true in isolation but never through a real table |
| A4 | Socket cap 3 -> 5 | Apply a 4th and 5th Sigil of Socketing to a 3-socket item | both succeed (stock cap was 3) |
| A5 | Sigil of Withdrawal | Use it on gear with gems | all gems return to inventory, gear keeps its affixes |
| A6 | The Ultimate Ingot recipe | Craft 8 crystaltine + 1 ultimate catalyst on the Ultimate table | yields 4 ingots. Stock EC has **no** source for this ingot at all |
| A7 | Boss quest completion | Kill any act sub-boss | its quest ticks; the act capstone unlocks only after all sub-bosses |
| A8 | New chapters render | Open the book | "Büyü Sanatı" (13 quests) and "Güçlenme" (12) appear as their own trees |

## B. Balance — the model is arithmetic, not observation

| # | What | How to test | Expected |
|---|---|---|---|
| B1 | Act boss TTK with a real group | 3-4 players of that act's gear kill the act boss | 44s-155s (act 9: ~5min). **Headless simulation ATTEMPTED AND FAILED** — see note below. Needs real players |
| B2 | Solo is miserable but possible | One player attempts an act boss | 3-20 min and dangerous |
| B3 | Boss **ability** damage | Let a Cataclysm / Ice and Fire boss use its scripted attacks | `damageset` only governs melee. Special attacks may ignore it entirely |
| B5 | Nether 8x compression | Cross a portal far from spawn | nether thresholds are 1/8 of overworld |
| B6 | Ender Dragon at 50k | Fight it | ~5.7 min with 3-4 endgame players |
| B7 | DPS-per-attack-damage after the gem nerf | Re-run `dps_test.py` | model assumes 1.95; measured before gems were deflated 8x |
| B8 | ~~Expected gear per act~~ | **RESOLVED — measured, see section E** | was my biggest risk; now real numbers |

## C. PvP / skill ceiling — RESOLVED BY THE DEFLATION

The owner's intent: an act-9 player **should** one-shot an act-3 player; it is
MID players who must survive. The deflated curve already does this, so no damage
cap is shipped (a blanket cap would have blocked the intended early-act one-shot
and would also have blunted boss threat).

| victim act | per hit | hits | verdict |
|---|---|---|---|
| 3 | 21.2 | 0.9 | one-shot — intended |
| 4 | 17.6 | 1.2 | survives 1 hit |
| 5 | 14.6 | 1.6 | survives 1 hit |
| 6 | 11.0 | 2.4 | survives 2-3 |
| 7 | 8.5 | 3.5 | survives 2-3 |
| 8 | 6.1 | 5.6 | real fight |
| 9 | 4.8 | 8.3 | real fight |

**C1** still needs two live players to confirm it *feels* right. Note for future
work: KubeJS's hurt event exposes `damage` READ-ONLY. It is cancellable, so a cap
would have to cancel and re-apply via `setHealth`, losing knockback.

## D. Interface / cosmetic

| # | What |
|---|---|
| D1 | The "4 ways to craft endersurge" JEI display. Recipe manager enumeration shows **126 gem recipes, endersurge x1 per rarity, zero duplicates** — so it is not a duplicate recipe. Need to see the screen to identify the four entries |
| D2 | Gem Cutting Table's JEI category still lists phantom recipes for a table that is uncraftable and non-interactive. KubeJS has JEI hide events; not yet wired |
| D3 | Turkish wording in the two new chapters |
| D4 | The two new chapter groups — "Ana Hikâye" (acts 1-8) and "Serbest Gelişim" (Güçlenme + Büyü Sanatı). `chapter_groups.snbt` was empty, so gated and non-gated trees rendered as one flat list. Need to see the book to confirm both groups appear and collapse |
| D5 | Boss-quest regrid. Sub-bosses stacked in one tall column (act 7 spanned y 4→14.5 while its own tree sat at y −3..2); they now wrap into columns of 4 centred on y=0, span ≤4.5 everywhere. Positions validate structurally but nobody has seen the rendered tree |

## F. THE BOSS-HP MODEL DOES NOT APPLY TO CAPSTONES

All seven modded act capstones can refuse damage in their own `hurt()`. Verified
by reading each one's bytecode - they are NOT all the same kind of gate:

All seven modded act capstones can refuse damage in their own `hurt()`. Verified by
reading each one's bytecode - they are NOT all the same kind of gate, and each one
measured a *different* multiple away from the arithmetic model:

| boss | gate | measured dps | status |
|---|---|---|---|
| Ferrous Wroughtnaut | animation window (top-down swing) | **1.50** | calibrated - one attacker only |
| Amethyst Crab | `CRAB_BURROW` + animation tick | **4.94** | calibrated |
| Frostmaw | animation handler + damage tags | **2.40** awake | calibrated - sleeps between phases |
| Ignis | `blockingProgress` | **1.01** | calibrated - parry gate |
| The Harbinger | animation + `CMDamageTypes.EMP` + life steal | **34.03** bow | calibrated - see below |
| Fire Dragon | damage TYPE immunities only | **31.02** bow | calibrated - not a window |
| Ender Guardian | `GUARDIAN_MASS_DESTRUCTION` + `getIsHelmetless` | — | **UNCALIBRATED** - phase gate, break armour first. Not an act capstone, so it does not gate progression; it inherits its act's tier stats |

`TTK = HP / group_dps` holds only for the Fire Dragon. Everything else needed a timed
kill against its own gate; the Wroughtnaut was wrong by ~100x before calibration, and
the spread between gates is 34x (Ignis 1.01 vs Harbinger 34.03). This is why a single
global DPS constant cannot tune this pack.

**The Harbinger is a ranged-only fight.** `harbinger_life_steal = 5.0` plus
`auto_heal = 2.0` means a melee player measures *negative* dps - it out-heals them
outright. Its 26,500 HP is set from the bow rate and assumes the group brings bows.

`tools/balance_report.py` scores every one of these against its own measured rate and
prints the table. Run it after changing any boss number.

## E. Known-good (already verified live, listed to avoid re-testing)

- 126 gem recipes register; ids unique; no duplicate-id errors
- `forge:partial_nbt` rejects wrong variant and wrong rarity (tested on the raw ingredient)
- Gem Cutting Table recipe removed; right-click cancelled
- 76 boss rules applied, all ids verified by summoning
- Armour formula, protection formula (`1 - min(0.01*p, 0.5)`) — both measured to the decimal
- Ancient armour affixes add a **third** ~46% mitigation layer on top of armour and protection
- Quest book: 158 quests, 10 chapters, 0 dangling dependencies
- **Boss stats live, after re-measuring each capstone against its own gate**
  (`tools/balance_report.py` prints this and scores it):
  ravager 1,500 · crab 1,825 · wroughtnaut 253 · frostmaw 1,350 · Ignis 549 ·
  fire dragon 20,040 · Harbinger 26,500 · **Ender Dragon 50,000 (owner-pinned)**.
  Every scored capstone is inside its target band. The small-looking numbers are
  correct: a window-gated boss only accepts damage for a fraction of the fight, so
  253 HP on the Wroughtnaut is a 2.8-minute solo fight, not a two-hit kill.
- **Bow DPS measured twice, independently: 31.02 (fire dragon) and 34.03 (Harbinger).**
  Two earlier readings — Harbinger 7.08 and fire dragon 4.12 — were both artefacts and
  are discarded. 7.08 was a sample where the player was not actually shooting; 4.12 was
  taken against a dragon summoned at 20 HP (see the IaF spawn trap below).
- **Trap: a summoned Ice and Fire dragon sits at 20 HP regardless of its age.** The
  `AgeTicks`/`DragonAge` NBT sets `max_health` but not `Health`. Always
  `data merge entity ... {Health:<max>f}` after summoning or the boss dies instantly and
  the sampler reports a fraction of a real fight.
- **Trap: dragon breath bypasses armour and has its own config keys.** It is in the
  `bypasses_armor` damage tag, so only Protection and affixes reduce it, and it does NOT
  scale with `"Dragon Attack Damage"` — raising melee 12→51 changed nothing measurable.
  Predicted mitigation factor 0.422 vs measured 0.405 confirmed the bypass. Breath also
  ticks 2-3x/second, so "hits to kill" is the wrong frame; use `~/mc-test-server/breath_test.py`,
  which reports damage-per-second-of-exposure. **Ice and Fire configs need a server
  restart — `/reload` does not pick them up.**
- **Ambient bands live: 4/4 exact** — safe 3.0, band1 6.5, band2 13.0, band3 23.0 attack damage
- Act 3 capstone consistency: `amethyst_crab` was a *miniboss* in the stat generator while
  the quest book crowned it the act boss (990 HP vs 3,000). Promoted; act 3 had no full boss

### Gear measured, not estimated (tools/gear_survey.py, weapon_sweep.py)
Player values = dummy reading minus the zombie's own base (2 armour, 3 attack).

- Armour: leather 7 | iron 15 | diamond 20 | **netherite 20** | ignitium 32 |
  dragonsteel 34 | ebonlord 45
- Weapons: stone 5 | iron 6 | diamond 7 | wrought axe 9 | netherite 8 |
  incinerator 14 | **dragonsteel axe 30** | ebonlord blade 20 | soul great sword 13

Two findings that change progression design:
1. **Netherite is NOT an armour upgrade over diamond** — both 20. Acts 3-5 sit on
   a flat armour plateau.
2. **Dragonsteel was the act-7 power cliff — FIXED.** At 30 player damage it made
   group DPS jump 67 -> 225 crossing into act 7, and nothing in act 8 beat it.
   Nerfed via `config/iceandfire-common.toml`:
   `Dragonsteel Sword Base Attack Strength` 25.0 -> 13.0 (axes derive from it).
   **Verified in game: sword 24 -> 12, axe 29 -> 17.** Curve is now
   9 -> 14 -> 18 -> 20 across acts 5-8, group DPS 39 -> 67 -> 118 -> 144 -> 147.
   NOTE: a KubeJS `ItemEvents.modification` attempt failed first - modded item
   classes (`ItemModAxe`) have no settable `attackDamage`. Use the mod's config.
3. `iceandfire:troll_weapon_*` were 17 player damage from **act-3** trolls.
   `Trolls Drop Weapon` set to **false** - the items still exist at 17 but are no
   longer obtainable from trolls. Reversible if you would rather keep the drop.

### A4/A5 also cannot be exercised headlessly
Tried calling the smithing recipes directly:
`recipe.matches(container, level)` on `AddSocketsRecipe` / `SocketingRecipe` /
`WithdrawalRecipe` with a hand-built `SimpleContainer(3)`. Every call throws
`ArrayIndexOutOfBoundsException` - Apothic smithing recipes read slots through
the real SmithingMenu, not a plain Container.

What this DID confirm: `kubejs:add_sockets` is registered as a genuine
`AddSocketsRecipe` (so the 3->5 cap override took the correct form), and both
`apotheosis:socketing` and `apotheosis:widthdrawal` are live.
Note the mod's own typo: the id is **widthdrawal**, not withdrawal.

### Why group TTK cannot be simulated headlessly (tools: raid_sim.py)
Tried spawning 4 attacker mobs with `attack_damage` set to the modelled player
hit value, against the real act capstone. **Measured 0 DPS in every trial**, with
both zombie and iron-golem attackers, against Wroughtnaut / Ignis / Harbinger.

Cause: vanilla mob targeting only recognises specific class hierarchies. Zombies
will not attack fellow hostiles, and iron golems' `NearestAttackableTargetGoal`
does not match Mowzie's or Cataclysm boss classes. The same limitation blocked
the boss-ability test (B3) - these bosses only aggro **players**.

So B1, B2 and B3 are permanently player-only. Do not spend more time on rigs.

### Trap: In Control does not reload with /reload
`/reload` leaves the OLD rules live. Use `execute as <player> run ctrl reload`
(the command needs a player context). This is why the first verification pass
read 0/8 — the file was right and the server was wrong.

## Safety note for future damage testing

Do **not** deal test damage to a player and rely on an unverified mitigation to
keep them alive. Buffer max health above the **fully unmitigated** worst case
first (`health_boost`, high amplifier), deal the hit, then remove the buffer.
This pack also has a **downed state** — a player at 0 HP is not dead yet but
dies if "not rescued in time", and does not regenerate while downed.
