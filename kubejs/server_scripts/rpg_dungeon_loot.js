// Seeds the three Create gate relics into dungeon chests.
//
// WHY
// Create is no longer gated by PMMO engineering levels (the level system was removed and the
// command that granted them no longer resolves). The tree opens by looting dungeons instead:
// rusted gear -> brass schematic -> precision core. Items are registered in
// kubejs/startup_scripts/rpg_dungeon_items.js.
//
// ALL RELICS DROP IN ALL DUNGEONS. The tiers differ only by how likely they are, and the
// likelihood tracks how much of the tree each one opens:
//   rusted gear      unlocks 4 quests   most needed   14%
//   brass schematic  unlocks 3 quests                 10%
//   precision core   unlocks 2 quests   least needed   6%
//
// RATES ARE TUNED SO ONE DUNGEON MOVES YOU FORWARD. You need ONE of each relic, ever, so
// the binding constraint is the RAREST one, not the average. An earlier pass used 6/4/2%,
// which measured correctly but meant ~114 chests for 90% odds on a precision core - several
// dungeons for optional side-tech. At 14/10/6% a ~25-chest dungeon run reliably yields
// tier 1, usually tier 2, and tier 3 within two dungeons, while still leaving ~70% of
// chests with no relic at all.
//
// RHINO: `var` only, bodies in named top-level functions. A `const`/`let` reused across
// callbacks in one file throws "redeclaration of var" on the SECOND invocation - it has
// silently broken five scripts here, most recently rpg_break_guard.js, which failed open
// and policed nothing for its entire life.

// Every dungeon-ish chest table in the pack. Namespaces confirmed present by scanning the
// installed jars: dungeons_arise 130 chest tables, idas 157, nova_structures 80,
// minecraft 24, biomeswevegone 18, threateningly_mobs 16, dungeoncrawl 11,
// betterstrongholds 10, legendary_monsters 8.
var DUNGEON_TABLES = [
	/minecraft:chests\/(simple_dungeon|abandoned_mineshaft|stronghold_.*|nether_bridge|bastion_.*|ancient_city.*|woodland_mansion|jungle_temple|desert_pyramid|end_city_treasure|underwater_ruin_.*|shipwreck_.*|pillager_outpost|ruined_portal)/,
	/dungeons_arise:chests\/.*/,
	/dungeoncrawl:chests\/.*/,
	/betterdungeons:.*/,
	/betterstrongholds:chests\/.*/,
	/bettermineshafts:.*/,
	/legendary_monsters:chests\/.*/,
	/idas:chests\/.*/,
	/nova_structures:chests\/.*/,
	/dungeons_and_taverns:.*/,
	/threateningly_mobs:chests\/.*/,
	/ancient_obelisks:chests\/.*/,
	/dungeon_realm:chests\/.*/,
]

var RELICS = [
	{ item: 'kubejs:rusted_gear', chance: 0.14 },
	{ item: 'kubejs:brass_schematic', chance: 0.1 },
	{ item: 'kubejs:precision_core', chance: 0.06 },
]

function seedRelic(event, relic) {
	var i
	for (i = 0; i < DUNGEON_TABLES.length; i++) {
		event.addLootTableModifier(DUNGEON_TABLES[i])
			.randomChance(relic.chance)
			.addLoot(relic.item)
	}
}

function seedAll(event) {
	var i
	for (i = 0; i < RELICS.length; i++) {
		seedRelic(event, RELICS[i])
	}
	console.info('[rpg] ' + RELICS.length + ' dungeon relics seeded across ' +
		DUNGEON_TABLES.length + ' table patterns')
}

LootJS.modifiers(event => {
	try {
		seedAll(event)
	} catch (e) {
		// A throw here leaves dungeons with no gate items at all and the Create tree
		// permanently locked, so say so loudly rather than failing quietly.
		console.error('[rpg] dungeon loot seeding FAILED - Create tree will be ungettable: ' + e)
	}
})
