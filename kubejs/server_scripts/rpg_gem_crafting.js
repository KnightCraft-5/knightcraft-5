// Apotheosis gems: crafted, act-gated progression instead of random drops.
//
// WHY
// Gems ARE the power curve here. Measured on the test server: a bare weapon does
// ~93 DPS, the same weapon fully gemmed ~726 - a 7-8x multiplier, and it lands
// almost identically for melee and ranged. Leaving the single biggest power
// source in the game behind a 4.5% mob-drop roll made progression pure luck.
//
// Drops are off in config/apotheosis/adventure.cfg (Gem Drop Chance 0, Gem Boss
// Bonus 0, Gem Loot Rules emptied), so these recipes are the ONLY source.
//
// THE LADDER
// Every rarity needs three things at once: three gems of the previous rarity,
// that act's boss drops, and the matching Extended Crafting material. The EC
// ladder (black iron -> redstone -> ender -> enhanced ender -> crystaltine ->
// ultimate) is a long grind by itself, and that is what gates the gem system
// behind mid-game instead of letting an early lucky find skip ahead.
//
// The bench climbs with the rarity - Basic, Advanced, Elite, Ultimate - so gems
// become available in Act 3 as designed rather than all at once behind endgame
// tech. gem_dust stays on the Basic table so the socketing and withdrawal sigils
// (the only way to get gems back OUT of gear) are reachable mid-game.
//
// gem_dust had NO recipe in Apotheosis - it only dropped from salvaging gems,
// which with drops disabled is circular (need gems to get dust to make gems).
// It gets a Black Iron recipe here, and that is the wall the system sits behind.
//
// TWO RHINO TRAPS THIS FILE WORKS AROUND
//  1. A generated ring pattern returned "GGG"/"GGG"/"GGG" under Rhino while the
//     identical logic in Python produced "GMG"/"MEM"/"GMG". The patterns are
//     therefore written out literally - there are only four of them.
//  2. Passing an ItemStack as a recipe key silently DROPS its NBT, leaving
//     {"item":"apotheosis:gem"}, which would let any gem of any variant or
//     rarity satisfy an upgrade. Gem inputs use forge:partial_nbt instead.

// variant -> the catalyst that decides WHICH gem you get. Without a distinct
// ingredient per variant all 21 base recipes collide: JEI shows 21 identical
// entries and the table hands you whichever resolves first.
//
// These MUST be cheap. The catalyst is 1 per base craft and a single ancient gem
// takes 243 base crafts, so a catalyst is really 243 of itself. The first draft
// used netherite_sword, wither_skeleton_skull and enchanted_golden_apple here,
// which priced three gem lines out of the game entirely. Everything below is
// farmable in bulk; the item only has to be DISTINCT, not expensive - the cost
// of the ladder lives in the Extended Crafting ingots and the boss gates.
const GEMS = {
	'core/ballast':        'minecraft:iron_ingot',
	'core/brawlers':       'minecraft:leather',
	'core/breach':         'minecraft:flint',
	'core/combatant':      'minecraft:arrow',
	'core/guardian':       'minecraft:shield',
	'core/lightning':      'minecraft:copper_ingot',
	'core/lunar':          'minecraft:glowstone_dust',
	'core/samurai':        'minecraft:iron_sword',
	'core/slipstream':     'minecraft:feather',
	'core/solar':          'minecraft:sunflower',
	'core/splendor':       'minecraft:gold_ingot',
	'core/tyrannical':     'minecraft:bone',
	'core/warlord':        'minecraft:coal',
	'overworld/earth':     'minecraft:emerald',
	'overworld/royalty':   'minecraft:golden_carrot',
	'the_end/endersurge':  'minecraft:ender_pearl',
	'the_end/mageslayer':  'minecraft:chorus_fruit',
	'the_nether/blood_lord':'minecraft:redstone',
	'the_nether/inferno':  'minecraft:blaze_powder',
	'twilight/forest':     'minecraft:oak_sapling',
	'twilight/queen':      'minecraft:honeycomb',
}

// Which sub-boss supplies a gem's material. A gem's FAMILY picks the sub-boss,
// the TIER picks the act - so a melee gem is fed by that act's melee-flavoured
// sub-boss all the way up the ladder, and no two families share a recipe.
const FAMILY = {
	'core/ballast': 'blade', 'core/tyrannical': 'blade', 'core/samurai': 'blade',
	'core/warlord': 'blade', 'core/breach': 'blade', 'the_nether/blood_lord': 'blade',
	'core/lunar': 'blade', 'core/solar': 'blade', 'the_nether/inferno': 'blade',
	'twilight/queen': 'blade',

	'core/combatant': 'bow', 'core/lightning': 'bow', 'core/slipstream': 'bow',

	'core/guardian': 'ward', 'core/brawlers': 'ward',
	'overworld/royalty': 'ward', 'twilight/forest': 'ward',

	'core/splendor': 'arcane', 'overworld/earth': 'arcane',
	'the_end/endersurge': 'arcane', 'the_end/mageslayer': 'arcane',
}

// G = 3x previous rarity in a TRIANGLE (top-centre, bottom-left, bottom-right),
// M = the tier's Extended Crafting ingot in BULK, F = the family's sub-boss drop
// (exactly 1), B = the act CAPSTONE's drop (exactly 1).
//
// WHY BOSS DROPS ONLY OCCUPY THE 1-COUNT SLOTS
// Three gems per upgrade compounds to 3^5 = 243 base gems for one ancient. So a
// single item in a low-tier recipe is not "one item" - it is 243 of them, and a
// bulk slot at the base tier is 729. An earlier draft put act sub-boss drops in
// the bulk slot and gated every tier on its capstone; the real cost of ONE
// ancient gem came out at 81 Ferrous Wroughtnaut kills and 729 Act-3 sub-boss
// drops, times five sockets per weapon. That is not a grind, it is a wall.
//
// So the bulk slot is the Extended Crafting ingot, which is the one thing in
// this pack designed to be mass-produced, and the boss drops sit in F and B
// where the compounding hits 1/3/9/27 instead of hundreds.
const PATTERNS = {
	3: ['MGM',
	    'FBM',
	    'GMG'],
	5: ['MMGMM',
	    'M   M',
	    'MFB M',
	    'M   M',
	    'GMMMG'],
	7: ['MMMGMMM',
	    'M     M',
	    'M     M',
	    'M FB  M',
	    'M     M',
	    'M     M',
	    'GMMMMMG'],
	9: ['MMMMGMMMM',
	    'M       M',
	    'M       M',
	    'M       M',
	    'M  FB   M',
	    'M       M',
	    'M       M',
	    'M       M',
	    'GMMMMMMMG'],
}

// `grid` selects BOTH the pattern and the bench (see GRID_TIER), so the grid size
// is how much material the rarity demands and which table it needs: 3x3 Basic is
// cheap and early, 9x9 Ultimate is the ancient wall.
//
// Every id below was read out of the mod jars' own loot tables and is GUARANTEED
// (single-entry pool, no conditions) and EXCLUSIVE to that boss. Chance drops are
// deliberately avoided: a 2.5% skull as a recipe input is not a gate, it is a
// slot machine. Notable exclusions found while checking - iceandfire troll_skull
// (2.5%), cyclops_eye (50%), threateningly_mobs inferno_jade (50%), and anything
// dropping born_in_chaos ethereal_spirit or legendary_monsters enderitium_gem,
// both of which come off a dozen unrelated mobs and gate nothing.
// `boss` is the act capstone's drop and is the real gate. It only appears from
// EPIC upward: below that the tier is crafted 27-243 times over, and requiring a
// capstone kill per craft would mean 81 Wroughtnauts for one gem. Common through
// rare gate on sub-boss drops and bulk instead, which is what those tiers are.
// Which Extended Crafting bench each grid size belongs to. EC's `tier` field is
// an EXACT match (tier != getTierFromGridSize -> no match), so this decides the
// bench outright.
//
// The bench CLIMBS WITH THE ACT rather than sitting at the top. An earlier pass
// locked every rarity to the Ultimate 9x9; that put emerald-tier tech (the full
// Basic->Advanced->Elite->Ultimate chain) in front of Act 3, where Cracked gems
// are meant to start, so Acts 3-5 had no gems at all and the low rarities were
// skipped entirely. The real gating is the boss drops and the ingot bulk, not
// the bench.
//
// Derived from `grid` so the pattern and the bench cannot drift apart.
const GRID_TIER = { 3: 1, 5: 2, 7: 3, 9: 4 }   // Basic, Advanced, Elite, Ultimate

const TIERS = [
	{ rarity: 'common',   grid: 3, ec: 'extendedcrafting:black_iron_ingot',
	  boss: 'extendedcrafting:black_iron_ingot',        // no capstone gate at entry rarity
	  mats: { blade: 'minecraft:iron_ingot',   bow:    'minecraft:string',
	          ward:  'minecraft:copper_ingot', arcane: 'minecraft:lapis_lazuli' } },

	{ rarity: 'uncommon', grid: 3, ec: 'extendedcrafting:redstone_ingot',
	  boss: 'extendedcrafting:redstone_ingot',          // 81 crafts - still too many to gate on a boss
	  mats: { blade: 'minecraft:diamond',   bow:    'minecraft:phantom_membrane',
	          ward:  'minecraft:iron_block', arcane: 'minecraft:amethyst_shard' } },

	// From here the boss drops bite: 27 / 9 / 3 / 1 kills of the act capstone.
	{ rarity: 'rare',     grid: 5, ec: 'extendedcrafting:ender_ingot',
	  boss: 'cataclysm:crystallized_coral_fragments',   // act 5 Coral Golem - farmable minion
	  mats: { blade:  'cataclysm:coral_chunk',                    // Coralssus
	          bow:    'legendary_monsters:crystal_of_sandstorm',   // Dune Sentinel
	          ward:   'legendary_monsters:frozen_rune',            // Frostbitten Golem
	          arcane: 'legendary_monsters:anchor_handle' } },      // Ancient Guardian

	{ rarity: 'epic',     grid: 5, ec: 'extendedcrafting:enhanced_ender_ingot',
	  boss: 'cataclysm:ignitium_ingot',                 // act 6 capstone: IGNIS (drops 3, so 3 kills)
	  mats: { blade:  'cataclysm:monstrous_horn',              // Netherite Monstrosity
	          bow:    'cataclysm:burning_ashes',               // Ignited Revenant
	          ward:   'legendary_monsters:lava_eaters_skin',   // Lava Eater
	          arcane: 'mowziesmobs:sol_visage' } },            // Umvuthi

	{ rarity: 'mythic',   grid: 7, ec: 'extendedcrafting:crystaltine_ingot',
	  boss: 'iceandfire:fire_dragon_heart',             // act 7 capstone: FIRE DRAGON (3 kills)
	  mats: { blade:  'cataclysm:tidal_claws',            // The Leviathan
	          bow:    'cataclysm:essence_of_the_storm',   // Scylla
	          ward:   'alexsmobs:void_worm_mandible',     // Void Worm
	          arcane: 'iceandfire:gorgon_head' } },       // Gorgon

	{ rarity: 'ancient',  grid: 9, ec: 'extendedcrafting:the_ultimate_ingot',
	  boss: 'cataclysm:witherite_block',                // act 8 capstone: THE HARBINGER (1 kill)
	  mats: { blade:  'legendary_monsters:soul_great_sword',   // Possessed Paladin
	          bow:    'legendary_monsters:eye_crystal',        // Annihilation Pursuer
	          ward:   'cataclysm:gauntlet_of_guard',           // Ender Guardian
	          arcane: 'cataclysm:cursium_ingot' } },           // Maledictus
]

/** Recipe OUTPUT - a real gem stack with its variant and rarity. */
function gemResult(variant, rarity) {
	return {
		item: 'apotheosis:gem',
		count: 1,
		nbt: `{gem:"apotheosis:${variant}",affix_data:{rarity:"apotheosis:${rarity}"}}`,
	}
}

/** Recipe INPUT - must match variant AND rarity, hence partial_nbt. */
function gemInput(variant, rarity) {
	return {
		type: 'forge:partial_nbt',
		item: 'apotheosis:gem',
		nbt: {
			gem: `apotheosis:${variant}`,
			affix_data: { rarity: `apotheosis:${rarity}` },
		},
	}
}

/** One rarity upgrade: 3 gems of TIERS[i-1] -> 1 gem of TIERS[i].
 *
 * THIS IS A FUNCTION FOR A REASON. Written inline as `for (let i...) { const t =
 * TIERS[i]; ... }`, Rhino pinned `t` to TIERS[1] on every iteration while
 * `TIERS[i - 1]` evaluated correctly - so all five upgrades collapsed into one
 * "uncommon in, uncommon out" recipe, and the other four were dropped as
 * duplicate ids. In game that looked like "chipped gems make chipped gems" and
 * the higher tables having no recipes at all. Function scope evaluates properly;
 * do not inline this back into the loop. Same family of Rhino bug as the grid
 * pattern trap noted at the top of this file.
 */
function addUpgrade(event, variant, fam, i) {
	var t = TIERS[i]
	var prev = TIERS[i - 1]
	event.custom({
		type: 'extendedcrafting:shaped_table',
		tier: GRID_TIER[t.grid],
		pattern: PATTERNS[t.grid],
		key: {
			G: gemInput(variant, prev.rarity),
			M: { item: t.ec },        // bulk
			F: { item: t.mats[fam] }, // 1 - which sub-boss feeds this family
			B: { item: t.boss },      // 1 - the act capstone gate
		},
		result: gemResult(variant, t.rarity),
	}).id(`kubejs:gem/${variant}/${t.rarity}`)
}

// THE GEM CUTTING TABLE, PROPERLY CLOSED.
//
// Removing its crafting recipe only stops new ones being built - any table that
// already exists in a world still works, and it upgrades gem rarity using gem
// dust plus rarity materials, which walks commons straight to ancient without
// touching a boss drop or the Ultimate table. That is the whole ladder bypassed.
//
// It cannot be removed with event.remove(): gem cutting is NOT a recipe type.
// Verified against the live server - all 153 registered recipe types were dumped
// and there is no gem_cutting type in any namespace. It is a container/GUI
// mechanic driven by gem data, so there is nothing for a recipe removal to match.
//
// Cancelling the interaction is what actually closes it, and it works on tables
// already placed.
BlockEvents.rightClicked('apotheosis:gem_cutting_table', event => {
	event.cancel()
})

ServerEvents.recipes(event => {
	// Close every other route to a gem, so the act-gated ladder is the only one.
	//
	// The Gem Cutting Table is the important one: it upgrades gem rarity in CODE,
	// not via a datapack recipe, so leaving it craftable would let a player walk
	// common gems all the way to ancient without ever touching an act's dungeon
	// loot or an Extended Crafting table. Removing its recipe is the only way to
	// shut that path without patching the mod.
	//
	// Salvaging is deliberately left alone - it turns unwanted gems INTO dust,
	// which is recycling rather than a bypass, and dust now has its own recipe.
	event.remove({ output: 'apotheosis:gem' })
	event.remove({ output: 'apotheosis:gem_cutting_table' })

	// THE ULTIMATE INGOT HAS NO SOURCE IN THIS PACK.
	// Verified against the live server's recipe manager: the only two recipes
	// producing extendedcrafting:the_ultimate_ingot are the_ultimate_ingot_recraft
	// (9 nuggets -> ingot) and the_ultimate_block_uncraft (block -> 9 ingots), and
	// nuggets/blocks come only from the ingot. It is a closed loop with no entry
	// point, which also kills the_ultimate_component and the_ultimate_catalyst
	// (both consume the ingot). The ancient gem tier needs it, so it gets an
	// entry point here.
	//
	// ultimate_catalyst is NOT circular - it comes from ultimate_component, which
	// is black iron slate + luminessence + 2 emeralds. Only the "the_" prefixed
	// variants are dead.
	event.custom({
		type: 'extendedcrafting:shaped_table',
		tier: 4,
		pattern: ['CCC', 'CAC', 'CCC'],
		key: {
			C: { item: 'extendedcrafting:crystaltine_ingot' },
			A: { item: 'extendedcrafting:ultimate_catalyst' },
		},
		// Yields 4, mirroring crystaltine's own 4-per-craft economy. At count 1 the
		// ancient tier cost 148 nether stars per gem - 738 withers for a 5-socket
		// weapon. At 4 it is 60 per gem. Still the most expensive thing in the pack,
		// which is the point, but it is now a grind rather than an impossibility.
		result: { item: 'extendedcrafting:the_ultimate_ingot', count: 4 },
	}).id('kubejs:extendedcrafting/the_ultimate_ingot')

	// gem_dust: the mid-game wall the whole system sits behind.
	//
	// DELIBERATELY *NOT* ULTIMATE-ONLY, unlike every gem recipe. Gem dust is the
	// base material for the Sigil of Socketing and the Sigil of Withdrawal, and
	// withdrawal is the only way to get gems back out of gear. Locking dust to the
	// Ultimate table made socket manipulation and gem retrieval endgame-only, so a
	// player who socketed a gem into the wrong item could not recover it for the
	// entire mid-game. The Basic table keeps those two sigils reachable.
	//
	// This does NOT weaken the gem ladder: the 126 gem recipes are still Ultimate-
	// only, so cheap dust buys sigils, not gems.
	event.custom({
		type: 'extendedcrafting:shaped_table',
		tier: 1,
		pattern: ['BBB', 'BLB', 'BBB'],
		key: {
			B: { item: 'extendedcrafting:black_iron_ingot' },
			L: { item: 'extendedcrafting:luminessence' },
		},
		result: { item: 'apotheosis:gem_dust', count: 2 },
	}).id('kubejs:gem_dust')

	let n = 0
	Object.keys(GEMS).forEach(variant => {
		const catalyst = GEMS[variant]
		const fam = FAMILY[variant]
		if (!fam) {
			// A variant with no family would silently fall back to undefined and
			// register a recipe with a missing key, which Extended Crafting reads
			// as air - i.e. a free gem. Refuse it loudly instead.
			console.error(`[rpg] gem variant ${variant} has no FAMILY entry - skipped`)
			return
		}

		// Base gem: sub-boss material + the per-variant catalyst that decides
		// WHICH gem you get. No capstone gate here - common is the entry rarity.
		const b = TIERS[0]
		event.custom({
			type: 'extendedcrafting:shaped_table',
			tier: GRID_TIER[b.grid],
			pattern: ['DMD', 'MCM', 'DED'],
			key: {
				D: { item: 'apotheosis:gem_dust' },
				M: { item: b.mats[fam] },
				E: { item: b.ec },
				C: { item: catalyst },
			},
			// 243 of these are needed per ancient gem, so every ingredient here
			// has to be bulk-farmable - see the note above PATTERNS.
			result: gemResult(variant, b.rarity),
		}).id(`kubejs:gem/${variant}/${b.rarity}`)
		n++

		for (var i = 1; i < TIERS.length; i++) {
			addUpgrade(event, variant, fam, i)
			n++
		}
	})

	console.info(`[rpg] ${n} gem recipes registered for ${Object.keys(GEMS).length} variants`)
})
